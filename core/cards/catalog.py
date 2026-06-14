# core/cards/catalog.py
# Единый каталог карт — ЕДИНСТВЕННЫЙ источник правды о том, какие карты
# существуют и кому они доступны. Без pygame, чистые данные + хелперы.
#
# Деление:
#   GENERIC_FACTORIES  — нейтральные карты, доступны всем классам (общий пул).
#   CLASS_FACTORIES    — классовые карты, выдаются в забеге ТОЛЬКО своему классу.
#
# Добавить классовую карту = одна строка в CLASS_FACTORIES.
from core.progression import is_card_unlocked, card_id_for
from core.cards import (
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_catalyst,
    create_steel_barricade, create_bastion,
    create_flex, create_battle_cry, create_thorn_armor,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_critical_bug, create_release_candidate, create_test_plan,
    create_checklist_drafting, create_bug_report,
    create_smoke_test, create_release_freeze,
    create_boil, create_arcane_focus, create_elemental_surge,
    create_overclock, create_resonant_discharge,
    create_friday_release, create_debug_session,
    create_breakthrough, create_pair_programming,
    create_echo_resonance, create_echo_cascade,
    create_escalation, create_force_push, create_refactoring, create_crunch,
    create_burning_sprint, create_ci_bypass,
    create_final_deploy, create_prod_crutch,
    create_cleaving_strike, create_piercing_thrust, create_wide_swing,
)
# Новые стихии (С58, айти-передел) — PAYLOAD-семья, импорт из модулей напрямую.
from core.cards.legacy import create_legacy_patch, create_tech_debt
from core.cards.coffee import (
    create_coffee_spill, create_coffee_flood, create_caffeine_overdose,
)
from core.cards.shortcircuit import (
    create_voltage_spike, create_overload, create_mass_short,
)
from core.cards.tox import create_micromanage, create_overtime
from core.cards.leak import create_memory_leak, create_infinite_loop
from core.cards.decomp import create_disassembler, create_reverse_engineer
from core.cards.shortcuts import (
    create_window_swap, create_refresh, create_coffee_break,
    create_hard_delete, create_stack_trace,
    create_task_manager, create_undo, create_copy, create_paste,
)
# Слой БАГОВ (ярус 1, С59): карта-Баг НЕ драфтится (вне GENERIC_FACTORIES/наград) —
# только навешивается через ACCRUE. Импортируется сюда РАДИ регистрации в RAW_FACTORIES
# (сейв/загрузка current_deck: Баг персистит между боями, нужен стабильный card_id).
from core.cards.bug import create_bug
# Пол цикла разработки (С60, задача 4 — снос флата): 4 карты пола В GENERIC-пуле,
# заменили флат Удар/Защита/Тяжёлый Клинок/Железную Стену 1:1. Флат-фабрики живы
# (basic.py: стартер Химика + тесты-vehicle), но из пула выдачи ВЫШЛИ.
from core.cards.devcycle import (
    create_commit, create_push_to_prod, create_code_review, create_sandbox,
)

# ─── Нейтральные карты (generic) — общий пул для всех классов ────────────────
GENERIC_FACTORIES = [
    # ── ПОЛ = ЦИКЛ РАЗРАБОТКИ (С60): Коммит/Пуш в прод/Код-ревью = COMMON-пол
    # стартдеков; Песочница = UNCOMMON Locked (награда). Петля долга с 1-го боя.
    create_commit, create_push_to_prod, create_code_review, create_sandbox,
    create_catalyst,
    # ── НОВЫЕ СТИХИИ (С58) — PAYLOAD: наложи Кофе/Legacy/Замыкание, детонируй ──
    create_legacy_patch, create_tech_debt,
    create_coffee_spill, create_coffee_flood,
    # Кофеин-овердос (контент-волна Стажёр, Этап 1) — generic СТАРТОВАЯ: cost0
    # кровь → добор 2. SelfHarm инертно-безопасен вне овердрафта (клампит на 0).
    create_caffeine_overdose,
    create_voltage_spike, create_overload, create_mass_short,
    create_micromanage, create_overtime,
    create_memory_leak, create_infinite_loop,
    create_disassembler, create_reverse_engineer,
    # ── ENGINE (С58): шорткаты-движок (манипуляция своими ресурсами). LOCKED. ──
    create_window_swap, create_refresh, create_coffee_break,
    create_hard_delete, create_stack_trace,
    create_task_manager, create_undo, create_copy, create_paste,
    # ── Буфф/хил/утилити/эхо/клив (отдельный слой, рескин позже) ──
    create_flex, create_battle_cry, create_thorn_armor,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_echo_resonance, create_echo_cascade,
    create_cleaving_strike, create_piercing_thrust, create_wide_swing,
    # Барьер (несгораемый щит) — универсальная защита (С57). LOCKED (за прогресс).
    create_steel_barricade, create_bastion,
    # «Залить в прод» — Мага ПАР-сетап (мигрирует в C4 вместе с Магом). LOCKED.
    create_boil,
]

# ─── Классовые карты — выдаются только своему классу ─────────────────────────
CLASS_FACTORIES = {
    # Воин = чисто ось Дисциплины (С57, чистка под единый формат): старая ось «щит=атака»
    # убрана из классового пула. Барьер (Failover/Кластер) → generic; Регрессионка → из выдачи
    # (фабрика жива для совместимости/тестов, но не выдаётся — дублировала Критический баг).
    "Warrior":   [create_critical_bug, create_release_candidate, create_test_plan,
                  create_checklist_drafting, create_bug_report,
                  create_smoke_test, create_release_freeze],
    # Маг = ось Мастерства/Нестабильности (С57, чистка под единый формат): «Залить в прод»
    # (чистый ПАР, 0 Мастерства) → generic. Остальные 4 трогают Мастерство (Стихийный
    # всплеск = мост стихии→ось через MasteryEffect).
    "Mage":      [create_overclock, create_resonant_discharge,
                  create_arcane_focus, create_elemental_surge,
                  create_friday_release, create_debug_session,
                  create_breakthrough, create_pair_programming],
    "Berserker": [create_escalation, create_force_push, create_refactoring,
                  create_crunch, create_burning_sprint, create_ci_bypass,
                  create_final_deploy, create_prod_crutch],
}


def _tagged(factory, class_name):
    """Обёртка фабрики: помечает созданную карту принадлежностью классу.
    Фабрики остаются чистыми — тег проставляется централизованно здесь."""
    def make():
        card = factory()
        card.card_class = class_name
        return card
    # Сохраняем имя оригинальной фабрики (нужно для дедупликации в библиотеке).
    make.__name__ = factory.__name__
    return make


# Каталог классовых фабрик с проставленным тегом card_class.
_TAGGED_CLASS_FACTORIES = {
    cls: [_tagged(f, cls) for f in factories]
    for cls, factories in CLASS_FACTORIES.items()
}


def get_pool_for_class(class_name, meta=None) -> list:
    """Пул выдачи карт для класса: generic + классовые этого класса.
    Используется магазином / сундуком / событиями в забеге.

    meta=None → ВЕСЬ пул без фильтра (обратная совместимость: сим/baseline и любые
    ещё-не-проведённые вызовы видят всё, как раньше → эталон не двинут). При переданной
    meta фильтруем по анлокам ([[capstone-reorder-content-first]], узкий стартовый пул):
    стартовые карты всегда, locked — только если их card_id записан в meta['unlocks']."""
    pool = GENERIC_FACTORIES + _TAGGED_CLASS_FACTORIES.get(class_name, [])
    if meta is None:
        return pool
    return [f for f in pool if is_card_unlocked(meta, card_id_for(f))]


def get_class_cards(class_name) -> list:
    """Только классовые карты класса (для вкладки библиотеки)."""
    return _TAGGED_CLASS_FACTORIES.get(class_name, [])


# ─── РЕЕСТР ВОССОЗДАНИЯ КАРТ (сейв забега, С57) ───────────────────────────────
# Карта = объект с эффектами + мутируется ковкой (base_val/uid/теги) → в сейв пишем
# card_id + forge-уровень, а при загрузке ПЕРЕСОЗДАЁМ фабрикой и накатываем ковку.
# RAW_FACTORIES: card_id → фабрика (классовые — TAGGED, чтобы проставился card_class).
RAW_FACTORIES = {}
for _f in GENERIC_FACTORIES:
    RAW_FACTORIES[card_id_for(_f)] = _f
for _cls_facs in _TAGGED_CLASS_FACTORIES.values():
    for _f in _cls_facs:
        RAW_FACTORIES[card_id_for(_f)] = _f
# Баг — НЕ в пулах выдачи, но в реестре воссоздания: навешанный долг лежит в
# gm.current_deck и обязан пережить сейв/загрузку (card_id='bug').
RAW_FACTORIES[card_id_for(create_bug)] = create_bug
# Флат (С60, задача 4) — ВЫШЕЛ из GENERIC, но в реестре воссоздания: strike/defend
# живут в стартере Химика (сейв-round-trip), heavy_blade/iron_wall — чтобы старые
# сейвы с Тяж.Клинком/Жел.Стеной в колоде не теряли карты при загрузке.
for _f in (create_strike, create_defend, create_heavy_blade, create_iron_wall):
    RAW_FACTORIES[card_id_for(_f)] = _f

# name → [(card_id, card_class)]: определяет id уже созданной карты для сохранения БЕЗ
# origin-поля на инстансе (не трогаем точки создания). В ЖИВОЙ колоде card_class почти
# всегда None (стартдек/generic тег не ставят), поэтому матчим по ИМЕНИ. Имена уникальны;
# при возможном дубле имени card_id_of развязывает по классу карты/игрока (hint_class).
# Гарантия — тест test_card_registry.
_NAME_TO_ENTRIES = {}
for _cid, _f in RAW_FACTORIES.items():
    _c = _f()
    _NAME_TO_ENTRIES.setdefault(_c.name, []).append((_cid, getattr(_c, "card_class", None)))


def make_card_by_id(card_id):
    """Пересоздать карту по card_id (для загрузки сейва). None, если id неизвестен
    (карта вне реестра — напр. транзиентный Глитч/особая). Forge-уровень накатывает
    вызывающий через core.forge."""
    factory = RAW_FACTORIES.get(card_id)
    return factory() if factory else None


def card_id_of(card, hint_class=None):
    """Определить card_id уже созданной карты (для сохранения колоды). None, если карта
    вне реестра. Матч по имени; при дубле имени разрешаем по классу карты ИЛИ подсказке
    класса игрока (hint_class — для стартдек-карт, где card_class не проставлен)."""
    # Ковка уровня 1 (card.upgrade) добавляет «+» к имени — зачищаем для матча по базовому.
    base_name = card.name.rstrip("+")
    entries = _NAME_TO_ENTRIES.get(base_name)
    if not entries:
        return None
    if len(entries) == 1:
        return entries[0][0]
    want = getattr(card, "card_class", None) or hint_class
    for cid, cclass in entries:
        if cclass == want:
            return cid
    return entries[0][0]
