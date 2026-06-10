# core/players/abilities/ -- активные способности всех классов игрока.
# Один файл на способность. Реэкспорт сохраняет прежнюю точку входа:
#   from core.players.abilities import WarriorAbility, RogueAbility, ...
from core.players.abilities.warrior import WarriorAbility
from core.players.abilities.rogue import RogueAbility
from core.players.abilities.mage import MageAbility
from core.players.abilities.berserker import BerserkerAbility
from core.players.abilities.summoner import SummonerAbility
from core.players.abilities.chemist import ChemistAbility

__all__ = [
    "WarriorAbility",
    "RogueAbility",
    "MageAbility",
    "BerserkerAbility",
    "SummonerAbility",
    "ChemistAbility",
]
