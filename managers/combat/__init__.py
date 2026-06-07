"""Поведенческие миксины боевого менеджера (разбор god-object CombatManager, С49).

`managers/CombatManager.py` остаётся ТОЧКОЙ ИМПОРТА и оркестратором (инфра: __init__,
лог, предохранитель глубины). Каждый миксин — одна ответственность боя; собираются
в `CombatManager` через наследование. Миксины оперируют ТОЛЬКО через `self` и НЕ
импортируют CombatManager (нет циклов). Внешний API (`CombatManager(...)`,
`.play_card_by_index()` и т.д.) и путь импорта — байт-в-байт прежние.
"""
from managers.combat.positioning import PositioningMixin

__all__ = ["PositioningMixin"]
