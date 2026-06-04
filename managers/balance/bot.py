# managers/balance/bot.py
# Бот для симуляции боя: играет жадно (случайные доступные карты),
# не шлёт сетевой рекорд и не трогает pygame при смерти.
import random
from managers.CombatManager import CombatManager


class BotCombatManager(CombatManager):
    """CombatManager без ручного ввода и без сетевых/UI-побочек.

    Цель — ИЗМЕРЕНИЕ, а не оптимальная игра: бот разыгрывает случайные
    доступные по энергии карты, пока может, затем завершает ход."""

    def check_player_defeat(self) -> bool:
        """Подавляем сеть/UI: просто фиксируем факт смерти."""
        if self.player.hp > 0:
            return False
        self.player.hp = 0
        return True

    def run_bot_loop(self, max_turns: int = 200):
        """Прогнать бой до конца. Возвращает True, если игрок выжил."""
        while self.player.hp > 0 and any(e.hp > 0 for e in self.enemies):
            if self.turn_count > max_turns:
                break   # страховка от зацикливания (напр. нечем добить врага)

            # Ход игрока: разыгрываем доступные карты, пока есть чем
            while self.player.hp > 0:
                hand = self.deck_manager.hand
                playable = [c for c in hand
                            if self.player.energy >= getattr(c, 'temp_cost', c.cost)]
                if not playable:
                    break
                card = random.choice(playable)
                idx  = hand.index(card)
                self.play_card_by_index(idx)
                if all(e.hp <= 0 for e in self.enemies):
                    return True

            self.end_turn_phase()

        return self.player.hp > 0
