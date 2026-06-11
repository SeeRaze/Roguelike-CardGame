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
    create_drain, create_blood_feast, create_life_tap,
    create_lacerate, create_hemorrhage, create_open_wound,
    create_punishing_formation, create_shield_wall, create_warrior_stance,
    create_boil, create_arcane_focus, create_elemental_surge,
    create_overclock, create_resonant_discharge,
    create_echo_resonance, create_echo_strike, create_echo_cascade,
    create_blood_rage, create_reckless_blow, create_blood_thirst, create_crunch,
    create_cleaving_strike, create_piercing_thrust, create_wide_swing,
)
# Новые стихии (С58, айти-передел) — PAYLOAD-семья, импорт из модулей напрямую.
from core.cards.legacy import create_legacy_patch, create_tech_debt
from core.cards.coffee import create_coffee_spill, create_coffee_flood
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

# ─── Нейтральные карты (generic) — общий пул для всех классов ────────────────
GENERIC_FACTORIES = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_catalyst,
    # ── НОВЫЕ СТИХИИ (С58) — PAYLOAD: наложи Кофе/Legacy/Замыкание, детонируй ──
    create_legacy_patch, create_tech_debt,
    create_coffee_spill, create_coffee_flood,
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
    create_drain, create_blood_feast, create_life_tap,
    create_lacerate, create_hemorrhage, create_open_wound,
    create_echo_resonance, create_echo_strike, create_echo_cascade,
    create_cleaving_strike, create_piercing_thrust, create_wide_swing,
    # Барьер (несгораемый щит) — универсальная защита (С57). LOCKED (за прогресс).
    create_steel_barricade, create_bastion,
    # «Закипание» — Мага ПАР-сетап (мигрирует в C4 вместе с Магом). LOCKED.
    create_boil,
]

# ─── Классовые карты — выдаются только своему классу ─────────────────────────
CLASS_FACTORIES = {
    # Воин = чисто ось Дисциплины (С57, чистка под единый формат): старая ось «щит=атака»
    # убрана из классового пула. Барьер (Заслон/Бастион) → generic; Возмездие → из выдачи
    # (фабрика жива для совместимости/тестов, но не выдаётся — дублировала Карающий строй).
    "Warrior":   [create_punishing_formation, create_shield_wall, create_warrior_stance],
    # Маг = ось Мастерства/Нестабильности (С57, чистка под единый формат): «Закипание»
    # (чистый ПАР, 0 Мастерства) → generic. Остальные 4 трогают Мастерство (Стихийный
    # всплеск = мост стихии→ось через MasteryEffect).
    "Mage":      [create_overclock, create_resonant_discharge,
                  create_arcane_focus, create_elemental_surge],
    "Berserker": [create_blood_rage, create_reckless_blow, create_blood_thirst,
                  create_crunch],
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
