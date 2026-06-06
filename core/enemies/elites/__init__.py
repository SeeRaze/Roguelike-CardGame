# core/enemies/elites/__init__.py
# Пакет элитных врагов-контр билдам: по одному классу на архетип.
# ELITE_REGISTRY — список классов; EnemySpawner.build_enemy выбирает случайный
# при is_elite=True. Импорты/записи добавляются инкрементально по мере создания
# файлов архетипов.
from core.enemies.elites.base import EliteBase
from core.enemies.elites.spell_eater import SpellEater
from core.enemies.elites.plague import PlaguePustule
from core.enemies.elites.butcher import ButcherTorturer

# Реестр элитных архетипов. Наполняется по мере добавления файлов.
# EnemySpawner.build_enemy: random.choice(ELITE_REGISTRY) при is_elite.
ELITE_REGISTRY = [
    SpellEater,
    PlaguePustule,
    ButcherTorturer,
]

__all__ = [
    "EliteBase",
    "SpellEater",
    "PlaguePustule",
    "ButcherTorturer",
    "ELITE_REGISTRY",
]
