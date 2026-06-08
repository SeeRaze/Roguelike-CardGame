# tests/test_card_description_projection.py
# Проекция значений ковки на строку описания карты (ui.cards.description.
# project_forge_values). Ковка (+δ) бампит base_val/upgrade_val эффектов, но НЕ
# строку описания — без проекции форжёная карта в костре/магазине показывает
# устаревшее число. Проверяем: чистые карты обновляются, нестандартные — no-op.

from core.cards.base import (
    Card, DamageEffect, ShieldEffect, PoisonEffect, StatusEffect, RegenEffect,
)
from core.forge import apply_linear_level
from ui.cards.description import project_forge_values


def _forge(card, levels):
    """Сымитировать живую ковку: lvl1 = upgrade(), дальше +δ (apply_linear_level),
    как в core.forge.forge_card_one_level."""
    for lvl in range(1, levels + 1):
        if lvl == 1:
            card.upgrade()
        else:
            apply_linear_level(card, 1)


# ─── Чистые карты: пары N(M) пересчитываются из эффектов ───────────────────────

def test_single_damage_card_projects_delta():
    c = Card("Удар", 1, "attack", "Наносит 6 (9) чистейшего урона.",
             [DamageEffect(6, 9)])
    _forge(c, 3)  # δ = 2 (lvl2 + lvl3)
    assert project_forge_values(c) == "Наносит 8 (11) чистейшего урона."


def test_unforged_card_unchanged():
    c = Card("Удар", 1, "attack", "Наносит 6 (9) чистейшего урона.",
             [DamageEffect(6, 9)])
    assert project_forge_values(c) == c.description


def test_multi_effect_card_projects_all_pairs():
    c = Card("Кислотный Барьер", 1, "defense",
             "Дает 6(9) щита. Накладывает 2(3) Яда.",
             [ShieldEffect(6, 9), PoisonEffect(2, 3)])
    _forge(c, 2)  # δ = 1 (на base И upgrade)
    assert project_forge_values(c) == "Дает 7(10) щита. Накладывает 3(4) Яда."


def test_spacing_preserved():
    # «6 (9)» с пробелом и «2(3)» без — оба сохраняют свой стиль.
    c = Card("X", 1, "attack", "A 6 (9). B 2(3).",
             [DamageEffect(6, 9), PoisonEffect(2, 3)])
    _forge(c, 2)
    assert project_forge_values(c) == "A 7 (10). B 3(4)."


def test_status_turns_not_bumped_but_displayed():
    # Поджог: урон бампится ковкой, длительность статуса — НЕТ (turns).
    c = Card("Поджог", 1, "attack", "Урон 2(4). Поджигает врага на 3(4) х.",
             [DamageEffect(2, 4), StatusEffect("ignited", 3, 4)])
    _forge(c, 2)  # δ = 1 (только на DamageEffect)
    assert project_forge_values(c) == "Урон 3(5). Поджигает врага на 3(4) х."


# ─── Страховка: несовпадение пар и эффектов → строка не трогается ──────────────

def test_pair_count_mismatch_is_noop():
    # 1 пара в строке, 3 эффекта (мульти-хит) → no-op, без порчи.
    c = Card("Серия молний", 2, "attack", "Наносит 3 удара по 2(3) урона.",
             [DamageEffect(2, 3), DamageEffect(2, 3), DamageEffect(2, 3)])
    _forge(c, 2)
    assert project_forge_values(c) == "Наносит 3 удара по 2(3) урона."


def test_lone_paren_number_is_noop():
    # «Регенерацию (2)» — нет цифры перед скобкой, пара не матчится → no-op.
    c = Card("Регенерация", 1, "skill", "Получить Регенерацию (2). Изгнание.",
             [RegenEffect(2, 4)])
    _forge(c, 3)
    assert project_forge_values(c) == "Получить Регенерацию (2). Изгнание."


def test_no_numbers_is_noop():
    c = Card("Перестроение", 0, "skill", "Тасует колоду.", [])
    assert project_forge_values(c) == "Тасует колоду."
