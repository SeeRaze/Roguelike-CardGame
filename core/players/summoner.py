from core.players.base import Player
from core.players.abilities import SummonerAbility
from core.cards import (
    create_strike, create_defend,
    create_bandage, create_summon_wolf,
)


def get_summoner_deck():
    return [
        create_strike(), create_strike(), create_strike(),
        create_defend(), create_defend(),
        create_bandage(),
        create_summon_wolf(), create_summon_wolf(),
    ]


class Summoner(Player):
    def __init__(self):
        super().__init__(
            name="Призыватель",
            max_hp=60,
            max_energy=3,
            gold=100,
            starter_deck_factory=get_summoner_deck,
        )
        self.active_ability = SummonerAbility()
