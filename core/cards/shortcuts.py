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
    UndoEffect, CopyEffect, PasteEffect,
)
from core.cards.echo import EchoEffect
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


# ─── ✖️ МНОЖИТЕЛИ (мало, под гардом — мост к PAYLOAD + гнездо петель) ─────────
def create_task_manager():
    """«Диспетчер задач» (Task Manager) — ПРЕД-коммит: Эхо 1 → следующая карта ×2.
    E5: собственный механизм (_dispatcher_pending) снесён, ретриггер унифицирован
    на Эхо — один кодовый путь в play_card_by_index, один предохранитель."""
    return Card(
        name="Диспетчер задач",
        cost=1,
        card_type="skill",
        description="Эхо 1: следующая сыгранная карта срабатывает ×2.",
        effects=[EchoEffect(1, 1)],
        rarity=Rarity.UNCOMMON,
    )


def create_undo():
    """«Отменить» (Ctrl+Z) — РЕТРОАКТИВ: вернуть последнюю сыгранную карту в руку."""
    return Card(
        name="Отменить",
        cost=0,
        card_type="skill",
        description="Верните последнюю сыгранную карту из сброса в руку.",
        effects=[UndoEffect()],
        rarity=Rarity.UNCOMMON,
    )


def create_copy():
    """«Копировать» (Ctrl+C) — сохранить последнюю сыгранную карту в Буфер."""
    return Card(
        name="Копировать",
        cost=0,
        card_type="skill",
        description="Сохраните последнюю сыгранную карту в Буфер (перезатир).",
        effects=[CopyEffect()],
        rarity=Rarity.UNCOMMON,
    )


def create_paste():
    """«Вставить» (Ctrl+V) — заново исполнить содержимое Буфера (НЕ очищает)."""
    return Card(
        name="Вставить",
        cost=1,
        card_type="skill",
        description="Заново исполните карту из Буфера (Буфер не очищается).",
        effects=[PasteEffect()],
        rarity=Rarity.UNCOMMON,
    )
