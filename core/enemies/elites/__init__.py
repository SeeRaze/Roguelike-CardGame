# core/enemies/elites/__init__.py
# Пакет элитных врагов-контр билдам: по одному классу на архетип.
# ELITE_REGISTRY — список классов; EnemySpawner.build_enemy выбирает случайный
# при is_elite=True. Импорты/записи добавляются инкрементально по мере создания
# файлов архетипов.
from core.enemies.elites.base import EliteBase
from core.enemies.elites.spell_eater import SpellEater

# Реестр элитных архетипов. Наполняется по мере добавления файлов.
# EnemySpawner.build_enemy: random.choice(ELITE_REGISTRY) при is_elite.
ELITE_REGISTRY = [
    SpellEater,
]

__all__ = [
    "EliteBase",
    "SpellEater",
    "ELITE_REGISTRY",
]
