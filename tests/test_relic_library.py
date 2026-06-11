# tests/test_relic_library.py
# Библиотека артефактов: весь пул раскладывается по категориям действия без потерь.
from core.relics import ALL_RELICS
from ui.relic_library.data import grouped_relics, categorize, CATEGORY_ORDER, total_count


def test_grouped_covers_whole_pool():
    """Каждый артефакт попадает ровно в одну группу; сумма == весь пул."""
    groups = grouped_relics()
    flat = [r for _, relics in groups for r in relics]
    assert len(flat) == total_count() == len(ALL_RELICS)
    names = [r.name for r in flat]
    assert len(names) == len(set(names))   # без дублей/потерь


def test_categories_are_known():
    """Все выданные категории — из объявленного порядка (нет «висячих» групп)."""
    for cat, _ in grouped_relics():
        assert cat in CATEGORY_ORDER


def test_categorize_uses_dominant_hook():
    """Категория выводится из переопределённого хука (примеры-якоря)."""
    by_name = {cls().name: cls() for cls in ALL_RELICS}
    # Линтер — модификатор урона (on_damage_calculated).
    assert categorize(by_name["Линтер"]) == "Модификатор урона"
    # Сердце Титана — рост/восстановление по забегу (on_combat_end).
    assert categorize(by_name["Сердце Титана"]) == "Рост по забегу (компаунд)"
    # Железная Воля — активируемая.
    assert categorize(by_name["Железная Воля"]) == "Активируемые"


def test_groups_sorted_by_rarity_inside():
    """Внутри группы артефакты идут по возрастанию редкости."""
    from core.rarity import Rarity
    order = {Rarity.COMMON: 0, Rarity.UNCOMMON: 1, Rarity.RARE: 2,
             Rarity.EPIC: 3, Rarity.LEGENDARY: 4}
    for _, relics in grouped_relics():
        ranks = [order[r.rarity] for r in relics]
        assert ranks == sorted(ranks)
