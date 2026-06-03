from core.players.base import Player
from core.cards import (
    create_strike, create_heavy_blade,
    create_flex, create_battle_cry,
)

def get_berserker_deck():
    return [
        create_strike(), create_strike(), create_strike(),
        create_strike(), create_strike(),   # много базовых атак
        create_heavy_blade(),               # тяжёлый удар
        create_heavy_blade(),
        create_flex(),                      # ярость
        create_battle_cry(),                # ярость на всю руку
    ]

class Berserker(Player):
    def __init__(self):
        super().__init__(
            name="Берсерк",
            max_hp=60,
            max_energy=3,
            gold=80,
            starter_deck_factory=get_berserker_deck,
        )