# core/cards/coffee.py
# Стихия РАЗЛИТЫЙ КОФЕ (С58): Уязвимость АДДИТИВНАЯ (+20% вход. урона/стак). Роль —
# УСИЛИТЕЛЬ (множит входящее + катализатор детонаций). Поглотил standalone vulnerable.
from core.cards.base import Card, StatusEffect, AoEStatusEffect
from core.rarity import Rarity


def create_coffee_spill():
    """«Кофе на клавиатуру» — пол: пассивный амп + катализатор детонаций (Электролиз)."""
    return Card(
        name="Кофе на клавиатуру",
        cost=1,
        card_type="skill",
        description="Накладывает Разлитый кофе 2(3) (получаемый урон +20%/стак).",
        effects=[
            StatusEffect("coffee", 2, 3),
        ],
    )


def create_coffee_flood():
    """«Разлив в опенспейсе» — площадной катализатор: Кофе по ВСЕМ врагам."""
    return Card(
        name="Разлив в опенспейсе",
        cost=1,
        card_type="skill",
        description="Накладывает Разлитый кофе 2(3) ВСЕМ врагам.",
        effects=[
            AoEStatusEffect("coffee", 2, 3),
        ],
        rarity=Rarity.UNCOMMON,
    )
