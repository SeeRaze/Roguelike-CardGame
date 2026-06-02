from core.players.base import Player
from core.cards import create_strike, create_defend, create_ignite, create_splash

def get_mage_deck():
    return [
        create_strike(), create_strike(),
        create_defend(), create_defend(), create_defend(),
        create_ignite(),  # Огонь
        create_splash()   # Вода для комбо
    ]

class Mage(Player):
    def __init__(self):
        super().__init__(
            name="Маг",
            max_hp=55,          # Стеклянная пушка
            max_energy=3,
            gold=90,
            starter_deck_factory=get_mage_deck
        )
