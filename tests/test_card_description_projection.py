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


# ─── Финальный урон в бою: замена ЦЕЛИТ в урон-пару N(M) ───────────────────────

from ui.cards.description import _resolve_description  # noqa: E402
from ui.cards.data import DMG_MARKER  # noqa: E402


class _Stub:
    pass


def _combat(desc, upgraded, base, predicted):
    return _resolve_description(desc, upgraded, player=_Stub(), enemy=_Stub(),
                                base_override=base, predicted=predicted)


def test_combat_simple_attack_replaces_damage():
    r = _combat("Наносит 6 (9) чистейшего урона.", False, 6, 10)
    assert r == f"Наносит {DMG_MARKER}10 чистейшего урона."


def test_combat_multihit_preserves_hit_count():
    # «3 удара» — счётчик, НЕ урон; урон в паре 2(3) → подменяется он, не «3».
    r = _combat("Наносит 3 удара по 2(3) урона.", False, 2, 4)
    assert r == f"Наносит 3 удара по {DMG_MARKER}4 урона."


def test_combat_multihit_upgraded_collision():
    # Улучшено: урон=3 совпал со счётчиком=3 — позиционный якорь на пару спасает.
    r = _combat("Наносит 3 удара по 2(3) урона.", True, 3, 5)
    assert r == f"Наносит 3 удара по {DMG_MARKER}5 урона."


def test_combat_cascade_preserves_x2():
    # «×2» не пара → не трогаем; урон-пара 8(12) подменяется.
    r = _combat("Урон 8(12). Если есть Эхо — урон ×2.", False, 8, 12)
    assert r == f"Урон {DMG_MARKER}12. Если есть Эхо — урон ×2."


def test_combat_multi_effect_resolves_other_pairs():
    r = _combat("Урон 4(6). Накладывает 3(5) Яда.", False, 4, 7)
    assert r == f"Урон {DMG_MARKER}7. Накладывает 3 Яда."


def test_combat_no_modifier_no_highlight():
    r = _combat("Наносит 6 (9) урона.", False, 6, 6)
    assert DMG_MARKER not in r and r == "Наносит 6 урона."


def test_card_base_damage_detects_echo_payoff():
    from ui.cards.renderer import CardRenderer
    from core.cards.echo import EchoPayoffEffect
    c = Card("Каскад", 2, "attack", "Урон 8(12).", [EchoPayoffEffect(8, 12)])
    assert CardRenderer._card_base_damage(c) == 8
    c.upgrade()
    assert CardRenderer._card_base_damage(c) == 12


def test_card_base_damage_skips_shield_damage():
    from ui.cards.renderer import CardRenderer
    from core.cards.warrior import ShieldDamageEffect
    c = Card("Возмездие", 1, "attack", "Урон = щиту (130%).",
             [ShieldDamageEffect(1.0, 1.3)])
    assert CardRenderer._card_base_damage(c) is None


# ─── Свёртка процентных пар base(upgrade): «(значение после улучшения)» не торчит ──

def test_resolve_pairs_collapses_percent_pairs():
    from ui.cards.description import _resolve_pairs
    s = "урон 6(9) ×(1 + 30%(40%) за стак)"
    assert _resolve_pairs(s, False) == "урон 6 ×(1 + 30% за стак)"
    assert _resolve_pairs(s, True) == "урон 9 ×(1 + 40% за стак)"
    # процент-цена в начале (Жажда крови)
    assert _resolve_pairs("Платите 7%(5%) макс. HP", False) == "Платите 7% макс. HP"
    # формульная скобка ×(1 + ...) без пары — не трогаем
    assert _resolve_pairs("урон 6 + 1 за долг", False) == "урон 6 + 1 за долг"


# ─── Проекция scaling-карт: база учитывает ТЕКУЩИЙ ресурс игрока (== удар) ─────────

def test_card_base_damage_scaling_uses_player_resource():
    from ui.cards.renderer import CardRenderer
    from core.cards.catalog import get_class_cards
    from core.players import Warrior
    card = next(f() for f in get_class_cards("Warrior")
                if f().name == "Карающий строй")
    eff = card.effects[0]
    p = Warrior()
    # без Дисциплины → база (множитель ×1)
    assert CardRenderer._card_base_damage(card, p) == eff.base_val
    # с Дисциплиной → base × (1 + mult_per × стак)
    p.set_status("discipline", 5)
    assert CardRenderer._card_base_damage(card, p) == int(eff.base_val * (1 + eff.mult_per * 5))
    # без игрока (библиотека/магазин) → база, без падения
    assert CardRenderer._card_base_damage(card, None) == eff.base_val
