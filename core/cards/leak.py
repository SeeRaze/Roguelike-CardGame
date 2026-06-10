# core/cards/leak.py
# Стихия УТЕЧКА ПАМЯТИ (С58): урон на АКТ ДОБОРА = стаки × размер руки. Роль — ДВИЖОК
# (темп/ресурс, всё на триггере добора). Ось «рука = Контекстное Окно» (семя Демиурга).
from core.cards.base import Card, StatusEffect, DrawEffect
from core.rarity import Rarity


def create_memory_leak():
    """«Утечка памяти» — пол-applier движка: посев Утечки (бьёт на доборе)."""
    return Card(
        name="Утечка памяти",
        cost=1,
        card_type="skill",
        description="Накладывает Утечку памяти 1(2) (урон на доборе = стаки × рука).",
        effects=[
            StatusEffect("leak", 1, 2),
        ],
    )


def create_infinite_loop():
    """«Бесконечный цикл» — само-синергия: Утечка + добор (рука↑ → Утечка больнее)."""
    return Card(
        name="Бесконечный цикл",
        cost=1,
        card_type="skill",
        description="Накладывает Утечку памяти 2(3) и добирает 1(2) карту.",
        effects=[
            StatusEffect("leak", 2, 3),
            DrawEffect(1, 2),
        ],
        rarity=Rarity.UNCOMMON,
    )
