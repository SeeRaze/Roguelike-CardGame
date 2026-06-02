from core.players.base import Player
from core.cards import create_strike, create_defend, create_neutralize, create_poison_stab

def get_rogue_deck():
    return [
        create_strike(), create_strike(), create_strike(),
        create_defend(), create_defend(), create_defend(),
        create_neutralize(),  # Слабость
        create_poison_stab()  # Яд
    ]

class Rogue(Player):
    def __init__(self):
        super().__init__(
            name="Разбойник",
            max_hp=65,          # Меньше ХП, упор на уклонение/щиты
            max_energy=3,
            gold=120,           # Чуть больше золота в карманах
            starter_deck_factory=get_rogue_deck
        )
