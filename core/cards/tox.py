# core/cards/tox.py
# Стихия ТОКСИЧНЫЙ МЕНЕДЖМЕНТ (С58): мультипл. Слабость (×0.9 урона врага/стак, пол
# 20%). Роль — САБОТАЖ (контроль/деградация систем врага). Поглотил standalone weak.
from core.cards.base import Card, StatusEffect
from core.rarity import Rarity


def create_micromanage():
    """«Микроменеджмент» — пол-applier саботажа: режет урон врага."""
    return Card(
        name="Микроменеджмент",
        cost=1,
        card_type="skill",
        description="Накладывает Токсичный менеджмент 2(3) (урон врага ×0.9/стак).",
        effects=[
            StatusEffect("tox", 2, 3),
        ],
    )


def create_overtime():
    """«Овертайм» — тяжёлый applier: топливо под семью реакций-саботажа."""
    return Card(
        name="Овертайм",
        cost=1,
        card_type="skill",
        description="Накладывает Токсичный менеджмент 3(4).",
        effects=[
            StatusEffect("tox", 3, 4),
        ],
        rarity=Rarity.UNCOMMON,
    )
