from core.players.base import Player
from core.cards import create_strike, create_defend, create_heavy_blade


def get_warrior_deck():
    """Стартовая колода Воина по нашему ГОСТу"""
    return [
        create_strike(), create_strike(), create_strike(), create_strike(),
        create_defend(), create_defend(), create_defend(), create_defend(),
        create_heavy_blade(),  # Одна тяжелая карта для веса
    ]


class Warrior(Player):
    def __init__(self):
        super().__init__(
            name="Воин",
            max_hp=80,
            max_energy=3,
            gold=100,
            starter_deck_factory=get_warrior_deck,
        )

    # ------------------------------------------------------------------
    # Пассивка «Железный задел»
    # 30% накопленного щита переносится на следующий ход.
    # Вызывается из CombatManager.start_turn_phase ВМЕСТО player.shield = 0
    # ------------------------------------------------------------------
    def on_turn_start_passive(self, combat_manager) -> None:
        carry = int(self.shield * 0.3)
        self.shield = carry
        if carry > 0 and combat_manager:
            combat_manager.add_log_message(
                f" [ВОИН] Железный задел: {carry} щита перенесено на новый ход."
            )