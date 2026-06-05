# core/enemies/bosses/__init__.py
# Пакет боссов-фильтров: по одному классу на каждый босс-этаж (20/40/60/80/100).
# BOSS_BY_FLOOR — диспатч: этаж → класс босса.
# Импорты добавляются инкрементально по мере создания файлов боссов.
from core.enemies.bosses.base import BossBase

# Диспатч боссов по этажам. Используется EnemySpawner.build_enemy().
# Этажи не в словаре → BossTitan (старый fallback).
# Заполняется по мере добавления боссов (guardian/archivist/elemental/keeper/architect).
BOSS_BY_FLOOR = {}

__all__ = [
    "BossBase",
    "BOSS_BY_FLOOR",
]
