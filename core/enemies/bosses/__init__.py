# core/enemies/bosses/__init__.py
# Пакет боссов-фильтров: по одному классу на каждый босс-этаж (20/40/60/80/100).
# BOSS_BY_FLOOR — диспатч: этаж → класс босса.
# Импорты добавляются инкрементально по мере создания файлов боссов.
from core.enemies.bosses.base import BossBase
from core.enemies.bosses.guardian import ThresholdGuardian
from core.enemies.bosses.archivist import OblivionArchivist
from core.enemies.bosses.elemental import VoidElemental
from core.enemies.bosses.keeper import TimeKeeper

# Диспатч боссов по этажам. Используется EnemySpawner.build_enemy().
# Этажи не в словаре → BossTitan (старый fallback).
BOSS_BY_FLOOR = {
    20: ThresholdGuardian,
    40: OblivionArchivist,
    60: VoidElemental,
    80: TimeKeeper,
}

__all__ = [
    "BossBase",
    "ThresholdGuardian",
    "OblivionArchivist",
    "VoidElemental",
    "TimeKeeper",
    "BOSS_BY_FLOOR",
]
