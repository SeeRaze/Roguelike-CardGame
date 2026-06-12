# core/cards/buff/regen.py
# Карты, накладывающие статус Хелсчек (healthcheck) на игрока.
# RegenEffect живёт в base.py -- здесь только фабрики карт.

from core.cards.base import Card, RegenEffect, ShieldEffect
from core.rarity import Rarity


def create_regenerate():
    """Базовый хелсчек. Изгоняется после использования."""
    return Card(
        name="Ребут",
        cost=1,
        card_type="skill",
        description="Получить Хелсчек (2). Изгнание.",
        effects=[RegenEffect(2, 4)],
        rarity=Rarity.UNCOMMON,
        exile=True,
    )


def create_vitality():
    """Долгий хелсчек без изгнания."""
    return Card(
        name="Отказоустойчивость",
        cost=2,
        card_type="skill",
        description="Получить Хелсчек (3).",
        effects=[RegenEffect(3, 5)],
        rarity=Rarity.RARE,
    )


def create_triage():
    """Быстрый хелсчек + щит. Для Воина."""
    return Card(
        name="Техподдержка",
        cost=1,
        card_type="skill",
        description="Получить Хелсчек (2) и 4 щита.",
        effects=[RegenEffect(2, 3), ShieldEffect(4, 6)],
        rarity=Rarity.COMMON,
    )