from core.players.base import Player
from core.players.abilities import RogueAbility
from core.cards import (
    create_strike, create_defend,
    create_neutralize, create_lacerate,
    create_open_wound,
)


def get_rogue_deck():
    return [
        create_strike(), create_strike(), create_strike(),
        create_strike(),
        create_defend(), create_defend(),
        create_neutralize(),
        create_lacerate(),
        create_open_wound(),
    ]


class Rogue(Player):
    def __init__(self):
        super().__init__(
            name="Разбойник",
            max_hp=55,
            max_energy=4,
            gold=120,
            starter_deck_factory=get_rogue_deck,
        )
        self.active_ability = RogueAbility()