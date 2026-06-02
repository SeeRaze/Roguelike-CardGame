# core/cards/buff/regen.py
# Карты, накладывающие статус регенерации на игрока.
# RegenEffect живёт в base.py -- здесь только фабрики карт.

from core.cards.base import Card, RegenEffect
from core.rarity import Rarity


def create_regenerate():
    """Базовая регенерация. Изгоняется после использования."""
    return Card(
        name="Регенерация",
        cost=1,
        card_type="skill",
        description="Получить Регенерацию (3). Изгнание.",
        effects=[RegenEffect(3, 5)],
        rarity=Rarity.UNCOMMON,
        exile=True,
    )


def create_vitality():
    """Долгая регенерация без изгнания."""
    return Card(
        name="Живучесть",
        cost=2,
        card_type="skill",
        description="Получить Регенерацию (5).",
        effects=[RegenEffect(5, 8)],
        rarity=Rarity.RARE,
    )


def create_triage():
    """Быстрая регенерация + щит. Для Воина."""
    return Card(
        name="Полевая Медицина",
        cost=1,
        card_type="skill",
        description="Получить Регенерацию (2) и 4 щита.",
        effects=[RegenEffect(2, 3)],
        rarity=Rarity.COMMON,
    )