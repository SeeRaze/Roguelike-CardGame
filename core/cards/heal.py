# core/cards/heal.py
# Карты прямого исцеления игрока.
# HealEffect живёт в base.py -- здесь только фабрики карт.

from core.cards.base import Card, HealEffect
from core.rarity import Rarity


def create_bandage():
    """Быстрое лечение. Доступно всем классам."""
    return Card(
        name="Подорожник",
        cost=1,
        card_type="skill",
        description="Восстановить 8 (12) HP.",
        effects=[HealEffect(8, 12)],
        rarity=Rarity.COMMON,
    )


def create_second_wind():
    """Мощное лечение. Изгоняется после использования."""
    return Card(
        name="Отгул",
        cost=1,
        card_type="skill",
        description="Восстановить 15 (20) HP. Изгнание.",
        effects=[HealEffect(15, 20)],
        rarity=Rarity.UNCOMMON,
        exile=True,
    )


def create_elixir():
    """Дорогое, но мощное лечение."""
    return Card(
        name="Отпуск",
        cost=2,
        card_type="skill",
        description="Восстановить 25 (35) HP.",
        effects=[HealEffect(25, 35)],
        rarity=Rarity.RARE,
    )