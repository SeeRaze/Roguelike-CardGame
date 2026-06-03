from core.players.base import Player
from core.cards import (
    create_strike, create_defend,
    create_neutralize, create_intimidate,
    create_lacerate, create_hemorrhage, create_open_wound,
)

def get_rogue_deck():
    return [
        create_strike(), create_strike(), create_strike(),
        create_strike(),                    # много быстрых ударов
        create_defend(), create_defend(),
        create_neutralize(),                # слабость
        create_lacerate(),                  # кровотечение
        create_open_wound(),                # тяжёлое кровотечение
    ]

class Rogue(Player):
    def __init__(self):
        super().__init__(
            name="Разбойник",
            max_hp=65,
            max_energy=4,       # ключевое изменение -- больше карт за ход
            gold=120,
            starter_deck_factory=get_rogue_deck,
        )