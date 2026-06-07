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
        """Подавляем сеть/UI: просто фиксируем факт смерти."""
        if self.player.hp > 0:
            return False
        self.player.hp = 0
        return True

    def run_bot_loop(self, max_turns: int = 200):
        """Прогнать бой до конца. Возвращает True, если игрок выжил."""
        policy = get_policy(type(self.player).__name__)

        while self.player.hp > 0 and any(e.hp > 0 for e in self.enemies):
            if self.turn_count > max_turns:
                break   # страховка от зацикливания (напр. нечем добить врага)

            policy.on_turn_begin(self)   # проактивные способности (призыв/ярость)

            # Ход игрока: разыгрываем доступные карты, пока есть чем
            overdraft = getattr(self.player, 'energy_overdraft', False)
            while self.player.hp > 0:
                hand = self.deck_manager.hand
                if overdraft:
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
                    return True

            policy.on_turn_end(self)      # реактивные способности (по набранным стакам)

            self.end_turn_phase()

        return self.player.hp > 0
