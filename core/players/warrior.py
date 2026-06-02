from core.players.base import Player
from core.cards import create_strike, create_defend, create_heavy_blade

def get_warrior_deck():
    """Стартовая колода Воина по нашему ГОСТу"""
    return [
        create_strike(), create_strike(), create_strike(), create_strike(),
        create_defend(), create_defend(), create_defend(), create_defend(),
        create_heavy_blade() # Одна тяжелая карта для веса
    ]

class Warrior(Player):
    def __init__(self):
        super().__init__(
            name="Воин",
            max_hp=80,          # Много здоровья
            max_energy=3,       # Стандартная энергия
            gold=100,           # Стартовый капитал
            starter_deck_factory=get_warrior_deck
        )
