# core/cards/buff/vampirism.py
# Карты с механикой вампиризма: урон + хил 50% от нанесённого.

from core.cards.base import Card, VampireDamageEffect
from core.rarity import Rarity


def create_drain():
    """Воин/Разбойник: базовый вампирский удар."""
    return Card(
        name="Высасывание",
        cost=1,
        card_type="attack",
        description="Урон 6 (9). Восстановить 50% нанесённого урона.",
        effects=[VampireDamageEffect(6, 9)],
        rarity=Rarity.UNCOMMON,
    )


def create_blood_feast():
    """Тяжёлый вампирский удар. Изгнание."""
    return Card(
        name="Кровавый Пир",
        cost=2,
        card_type="attack",
        description="Урон 18 (24). Восстановить 50% нанесённого урона. Изгнание.",
        effects=[VampireDamageEffect(18, 24)],
        rarity=Rarity.RARE,
        exile=True,
    )


def create_life_tap():
    """Маг: слабый удар, но гарантированный хил даже при 1 уроне."""
    return Card(
        name="Жизнеотвод",
        cost=1,
        card_type="attack",
        description="Урон 4 (6). Восстановить 50% нанесённого урона.",
        effects=[VampireDamageEffect(4, 6)],
        rarity=Rarity.COMMON,
    )