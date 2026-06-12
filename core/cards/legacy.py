# core/cards/legacy.py
# Стихия LEGACY-КОД (С58): чистый DoT, УВАЖАЕТ щит (пробитие = заработок Кислотного
# дождя). Роль — УРОН (полезная нагрузка). Декей-триангуляр (модель Яда). Поглотил poison.
from core.cards.base import Card, DamageEffect, StatusEffect
from core.cards.bug import AccrueBugEffect
from core.rarity import Rarity


def create_legacy_patch():
    """«Костыль» — пол-офенс: мгновенный урон + посев Legacy. УЧИТ механике DoT.
    ACCRUE-райдер (С60): костыль буквально хак → оставляет техдолг (+1 Баг в колоду
    забега). Долг авторский за legacy-DoT (агентность, не штраф)."""
    return Card(
        name="Костыль",
        cost=1,
        card_type="attack",
        description="Урон 3(5). Накладывает Legacy-код 3(4). Навешивает 1 Баг.",
        effects=[
            DamageEffect(3, 5),
            StatusEffect("legacy", 3, 4),
            AccrueBugEffect(1),
        ],
    )


def create_tech_debt():
    """«Технический долг» — тяжёлый applier: чистый DoT-сетап под детонацию/реакции."""
    return Card(
        name="Технический долг",
        cost=1,
        card_type="skill",
        description="Накладывает Legacy-код 6(9).",
        effects=[
            StatusEffect("legacy", 6, 9),
        ],
        rarity=Rarity.UNCOMMON,
    )
