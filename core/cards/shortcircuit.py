# core/cards/shortcircuit.py
# Стихия КОРОТКОЕ ЗАМЫКАНИЕ (С58): копит заряд до порога → детонация (позвоночник).
# Роль — ДЕТОНАТОР (кнопка взрыва, со-элемент выбирает вкус). Поглотил shock.
from core.cards.base import Card, DamageEffect, StatusEffect, DetonateEffect
from core.rarity import Rarity


def create_voltage_spike():
    """«Скачок напряжения» — пол-applier заряда (копит до порога 5)."""
    return Card(
        name="Скачок напряжения",
        cost=1,
        card_type="skill",
        description="Накладывает Короткое замыкание 2(3) (при 5 — детонация).",
        effects=[
            StatusEffect("shortcircuit", 2, 3),
        ],
    )


def create_overload():
    """«Перегрузка» — дешёвый детонатор-кнопка: урон + досрочная детонация заряда."""
    return Card(
        name="Перегрузка",
        cost=1,
        card_type="attack",
        description="Урон 3(4). Детонация Короткого замыкания (вкус по со-элементу).",
        effects=[
            DamageEffect(3, 4),
            DetonateEffect(),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_mass_short():
    """«Замыкание на массу» — само-достаточный взрыв: большой заряд + сразу детонация."""
    return Card(
        name="Замыкание на массу",
        cost=2,
        card_type="attack",
        description="Накладывает Короткое замыкание 3(4) и сразу детонирует.",
        effects=[
            StatusEffect("shortcircuit", 3, 4),
            DetonateEffect(),
        ],
        rarity=Rarity.RARE,
    )
