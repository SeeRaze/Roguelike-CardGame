# core/cards/coffee.py
# Стихия РАЗЛИТЫЙ КОФЕ (С58): Уязвимость АДДИТИВНАЯ (+20% вход. урона/стак). Роль —
# УСИЛИТЕЛЬ (множит входящее + катализатор детонаций). Поглотил standalone vulnerable.
from core.cards.base import Card, StatusEffect, AoEStatusEffect, DrawEffect
from core.cards.berserker import SelfHarmEffect
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


def create_caffeine_overdose():
    """«Кофеин-овердос» — cost 0: плати кровью → добор 2 карт. GENERIC СТАРТОВАЯ.
    Грань «кровь → темп» для всех классов: SelfHarmEffect реюзабелен (lose_hp клампит
    на пол; у Стажёра hp_overdraft → уводит в долг, у прочих инертно-безопасен на 0).
    Generic-вариант мягче классового «Горящего Спринта» по синергии долга, но даёт
    +1 карту (добор 2). Числа = ЗАГЛУШКИ. COMMON."""
    return Card(
        name="Кофеин-овердос",
        cost=0,
        card_type="skill",
        description="Платите 5%(4%) макс. HP, доберите 2 карты.",
        effects=[SelfHarmEffect(0.05, 0.04), DrawEffect(2, 2)],
        rarity=Rarity.COMMON,
    )
