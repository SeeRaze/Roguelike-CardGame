# core/cards/shortcuts.py
# Семья ENGINE (С58): шорткаты-движок — манипуляция СВОИМИ ресурсами (рука/колода/
# энергия), чтобы PAYLOAD прилетел жирнее. Имена = АКТ-1-ПРОСТЫЕ (что делают); акт 2 →
# хоткеи (Ctrl+C…), акт 3 → код (card_naming_escalation, ENGINE-only).
#
#   🔋 ТОПЛИВО (щедро): Переключить окно / Обновить / Перерыв.
#   🔍 ФИЛЬТР (щедро): Удалить безвозвратно / Просмотр стека.
#   ✖️ МНОЖИТЕЛИ (мало, под гардом): Диспетчер задач / Отменить / Копировать / Вставить (C2b).
from core.cards.base import (
    Card, DrawEffect, EnergyEffect, DiscardRedrawEffect,
    ExileFromHandEffect, ScryEffect,
)
from core.rarity import Rarity


# ─── 🔋 ТОПЛИВО ──────────────────────────────────────────────────────────────
def create_window_swap():
    """«Переключить окно» (Alt+Tab) — КАЧЕСТВО: сбросить руку, добрать столько же."""
    return Card(
        name="Переключить окно",
        cost=0,
        card_type="skill",
        description="Сбросьте руку и доберите столько же карт.",
        effects=[DiscardRedrawEffect()],
        rarity=Rarity.UNCOMMON,
    )


def create_refresh():
    """«Обновить» (F5) — КОЛИЧЕСТВО: чистый добор (утилити-пол)."""
    return Card(
        name="Обновить",
        cost=1,
        card_type="skill",
        description="Доберите 2(3) карты.",
        effects=[DrawEffect(2, 3)],
    )


def create_coffee_break():
    """«Перерыв» (Кофе-брейк) — ЭНЕРГИЯ: рамп/бурст-ход."""
    return Card(
        name="Перерыв",
        cost=0,
        card_type="skill",
        description="Получите +2(3) энергии в этот ход.",
        effects=[EnergyEffect(2, 3)],
        rarity=Rarity.UNCOMMON,
    )


# ─── 🔍 ФИЛЬТР ───────────────────────────────────────────────────────────────
def create_hard_delete():
    """«Удалить безвозвратно» (Shift+Delete) — ХИРУРГИЯ: изгнать карту из руки."""
    return Card(
        name="Удалить безвозвратно",
        cost=0,
        card_type="skill",
        description="Изгоните карту из руки (безвозвратно).",
        effects=[ExileFromHandEffect()],
        exile=True,
    )


def create_stack_trace():
    """«Просмотр стека» (Stack Trace) — ИНФО: прочистка верха колоды."""
    return Card(
        name="Просмотр стека",
        cost=0,
        card_type="skill",
        description="Посмотрите верх 3(5) колоды; лишнее — в сброс.",
        effects=[ScryEffect(3, 5)],
    )
