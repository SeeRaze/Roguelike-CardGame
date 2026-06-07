# managers/balance/bot.py
# Бот для симуляции боя: играет КОМПЕТЕНТНО к ядру своего класса (см. policy.py),
# не шлёт сетевой рекорд и не трогает pygame при смерти.
from managers.CombatManager import CombatManager
from managers.balance.policy import get_policy


class BotCombatManager(CombatManager):
    """CombatManager без ручного ввода и без сетевых/UI-побочек.

    Цель — ИЗМЕРЕНИЕ, а не оптимальная игра: бот играет по классовой политике
    (приоритет карт + тайминг способности), пока может, затем завершает ход."""

    def check_player_defeat(self) -> bool:
        """Подавляем сеть/UI: просто фиксируем факт смерти. Floor-aware (§4): при HP-
        овердрафте игрок выживает в минусе до пола _hp_floor() (дефолт 0 → как раньше).
        НЕ обнуляем hp в 0 (для овердрафта 0 ВЫШЕ пола → цикл run_bot_loop счёл бы живым
        и завис) — оставляем hp на полу/ниже, чтобы `hp > _hp_floor()` корректно дал смерть."""
        if self.player.hp > self.player._hp_floor():
            return False
        return True

    def run_bot_loop(self, max_turns: int = 200):
        """Прогнать бой до конца. Возвращает True, если игрок выжил."""
        policy = get_policy(type(self.player).__name__)

        while self.player.hp > self.player._hp_floor() and any(e.hp > 0 for e in self.enemies):
            if self.turn_count > max_turns:
                break   # страховка от зацикливания (напр. нечем добить врага)

            policy.on_turn_begin(self)   # проактивные способности (призыв/ярость)

            # Позиционка (§4, opt-in): после призыва переставляем партию по рангам,
            # чтобы свежие саммоны получили ранг до фазы врага. NO-OP без флага
            # positioning_enabled → baseline зелёный.
            self._apply_positioning()

            # Ход игрока: разыгрываем доступные карты, пока есть чем
            overdraft = getattr(self.player, 'energy_overdraft', False)
            madness = getattr(self.player, 'madness_active', False)
            while self.player.hp > self.player._hp_floor():
                hand = self.deck_manager.hand
                if madness:
                    # БЕЗУМИЕ (Берсерк): карты за 0 энергии → все доступны (цена = HP,
                    # пол HP ограничит). Дамп руки ради темпо/нырка в множитель.
                    playable = list(hand)
                elif overdraft:
                    # Долговой движок (§7): бот допускает уход энергии в минус, но не
                    # глубже жёсткого пола (как гейт play_card_by_index).
                    from core.debt import DEBT_MAX_OVERDRAFT
                    playable = [
                        c for c in hand
                        if getattr(c, 'temp_cost', c.cost) - self.player.energy
                        <= DEBT_MAX_OVERDRAFT
                    ]
                else:
                    playable = [c for c in hand
                                if self.player.energy >= getattr(c, 'temp_cost', c.cost)]
                if not playable:
                    break
                card = policy.pick_card(playable, self)
                idx  = hand.index(card)
                self.play_card_by_index(idx)
                if all(e.hp <= 0 for e in self.enemies):
                    self.player.on_combat_won(self)   # пик победы (Берсерк: |HP|→FP)
                    return True
                if madness and card in self.deck_manager.hand:
                    break        # в безумии карта не ушла из руки (нет цели) → анти-зацикл

            policy.on_turn_end(self)      # реактивные способности (по набранным стакам)

            self.end_turn_phase()

        # Внешний цикл вышел: все враги мертвы (победа) или игрок пал. Пик победы (Берсерк)
        # фиксируем, только если враги мертвы И игрок жив (победа в фазе врага/союзника).
        if (all(e.hp <= 0 for e in self.enemies)
                and self.player.hp > self.player._hp_floor()):
            self.player.on_combat_won(self)
        return self.player.hp > self.player._hp_floor()
