# core/cards/debuff/bleed.py
# Карты, накладывающие статус кровотечения на врага.

from core.cards.base import Card, DamageEffect
from core.rarity import Rarity


class BleedEffect:
    """Накладывает кровотечение на врага."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        enemy.add_status("bleed", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> {enemy.name} получает Кровотечение ({amount})."
            )


def create_lacerate():
    """Разбойник: быстрый порез, вешает кровотечение."""
    return Card(
        name="Порез",
        cost=1,
        card_type="attack",
        description="Урон 4 (6). Кровотечение 3 (4).",
        effects=[DamageEffect(4, 6), BleedEffect(3, 4)],
        rarity=Rarity.COMMON,
    )


def create_hemorrhage():
    """Разбойник: тяжёлый удар с сильным кровотечением."""
    return Card(
        name="Кровопускание",
        cost=2,
        card_type="attack",
        description="Урон 8 (12). Кровотечение 6 (9).",
        effects=[DamageEffect(8, 12), BleedEffect(6, 9)],
        rarity=Rarity.UNCOMMON,
    )


def create_open_wound():
    """Только кровотечение, без урона. Изгнание."""
    return Card(
        name="Открытая Рана",
        cost=1,
        card_type="skill",
        description="Кровотечение 8 (12). Изгнание.",
        effects=[BleedEffect(8, 12)],
        rarity=Rarity.RARE,
        exile=True,
    )