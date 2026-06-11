# ui/relic_library/data.py
# Библиотека артефактов: весь пул в один экран, сгруппированный по ДЕЙСТВИЮ
# (доминантному хуку срабатывания). Категория выводится из того, какие хуки
# артефакт переопределяет — без ручной разметки, новый артефакт раскладывается сам.
from core.relics import ALL_RELICS
from core.relics.base import Relic
from core.rarity import Rarity

_RARITY_ORDER = {
    Rarity.COMMON: 0, Rarity.UNCOMMON: 1, Rarity.RARE: 2,
    Rarity.EPIC: 3, Rarity.LEGENDARY: 4,
}


def _overrides(cls, hook) -> bool:
    """Переопределяет ли класс артефакта базовый хук Relic (= реально на нём работает)."""
    return getattr(cls, hook, None) is not getattr(Relic, hook, None)


def categorize(relic) -> str:
    """Категория артефакта по доминантному действию (приоритет сверху вниз).
    Эвристика по переопределённым хукам — для удобной ревизии пула, не для логики."""
    cls = type(relic)
    if relic.is_active:
        return "Активируемые"
    if _overrides(cls, "on_boss_defeated") or _overrides(cls, "on_combat_end"):
        return "Рост по забегу (компаунд)"
    if _overrides(cls, "on_damage_calculated"):
        return "Модификатор урона"
    if _overrides(cls, "on_kill"):
        return "При убийстве"
    if _overrides(cls, "on_shield_gained"):
        return "Щит и защита"
    if any(_overrides(cls, h) for h in
           ("on_tick_legacy", "on_coffee_applied", "on_bleed_tick", "on_heal")):
        return "Стихии, статусы, лечение"
    if _overrides(cls, "on_card_played"):
        return "При розыгрыше карт"
    if _overrides(cls, "on_chest_opened"):
        return "Сундуки и экономика"
    if any(_overrides(cls, h) for h in
           ("on_combat_start", "on_turn_start", "on_turn_end")):
        return "Начало боя и тайминг"
    return "Прочее"


# Порядок групп на экране (сверху вниз).
CATEGORY_ORDER = [
    "Модификатор урона",
    "При убийстве",
    "Щит и защита",
    "Стихии, статусы, лечение",
    "При розыгрыше карт",
    "Начало боя и тайминг",
    "Рост по забегу (компаунд)",
    "Сундуки и экономика",
    "Активируемые",
    "Прочее",
]


def grouped_relics():
    """[(категория, [relic, ...]), ...] в порядке CATEGORY_ORDER; внутри по редкости
    затем по имени. Артефакты инстанцируются один раз на построение списка."""
    buckets = {}
    for cls in ALL_RELICS:
        relic = cls()
        buckets.setdefault(categorize(relic), []).append(relic)
    out = []
    for cat in CATEGORY_ORDER:
        items = buckets.get(cat)
        if items:
            items.sort(key=lambda r: (_RARITY_ORDER.get(r.rarity, 9), r.name))
            out.append((cat, items))
    # Подстраховка: категории вне CATEGORY_ORDER (если появится новый хук) — в конец.
    for cat, items in buckets.items():
        if cat not in CATEGORY_ORDER:
            items.sort(key=lambda r: (_RARITY_ORDER.get(r.rarity, 9), r.name))
            out.append((cat, items))
    return out


def total_count() -> int:
    return len(ALL_RELICS)
