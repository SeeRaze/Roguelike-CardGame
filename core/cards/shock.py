# core/cards/shock.py
# Карты стихии «Молния» (статус Шок). Архетип — МИКРО-АТАКИ: Шок не тикает сам,
# он расходуется ударами (+3 урона за удар, −1 заряд, см. EffectCalculator).
# Поэтому связка «навесить много зарядов → пробить серией мелких ударов» бьёт
# нелинейно: каждый отдельный DamageEffect дренит свой заряд.
#
# Трио:
#   «Разряд»       — дешёвый энейблер, чистое наложение Шока.
#   «Серия молний» — мульти-хит пейофф (3 удара → дренит до 3 зарядов за карту).
#   «Громовой удар» — гибрид: бьёт сейчас и подзаряжает Шок на следующие удары.
from core.cards.base import Card, DamageEffect, StatusEffect, DetonateEffect
from core.rarity import Rarity


def create_shock_bolt():
    """«Разряд» — навешивает Шок 3(4) на цель. Чистый энейблер за 1 энергию:
    сам урона не наносит, готовит цель под серию ударов."""
    return Card(
        name="Разряд",
        cost=1,
        card_type="skill",
        description="Накладывает Шок 3(4). Каждый удар по цели наносит +3 урона.",
        effects=[
            StatusEffect("shock", 3, 4),
        ],
    )


def create_chain_lightning():
    """«Серия молний» — 3 удара по 2(3). Пейофф архетипа: каждый удар отдельно
    дренит заряд Шока, поэтому при 3 зарядах карта бьёт (2+3)×3 = 15."""
    return Card(
        name="Серия молний",
        cost=1,
        card_type="attack",
        description="Наносит 3 удара по 2(3) урона. Каждый удар тратит заряд Шока.",
        effects=[
            DamageEffect(2, 3),
            DamageEffect(2, 3),
            DamageEffect(2, 3),
        ],
    )


def create_thunder_strike():
    """«Громовой удар» — урон 6(8) + Шок 2(3). Гибрид: бьёт сейчас и подзаряжает
    цель под последующие мелкие удары."""
    return Card(
        name="Громовой удар",
        cost=2,
        card_type="attack",
        description="Урон 6(8). Накладывает Шок 2(3).",
        effects=[
            DamageEffect(6, 8),
            StatusEffect("shock", 2, 3),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_overload():
    """«Перегрузка» — урон 3(4) + ДЕТОНАЦИЯ. Если цель Мокрая и под Шоком —
    срабатывает Электро-взрыв (Шок×6 урона по всем врагам, см. DetonationRegistry).
    Меж-стихийный детонатор: связка Вода → Шок → Перегрузка."""
    return Card(
        name="Перегрузка",
        cost=1,
        card_type="attack",
        description="Урон 3(4). Детонация: Мокрый + Шок -> Электро-взрыв по всем врагам.",
        effects=[
            DamageEffect(3, 4),
            DetonateEffect(),
        ],
        rarity=Rarity.UNCOMMON,
    )
