# ui/library/data.py
# Библиотека карт: вкладки и геометрия сетки.
# ПАРС ВСЕХ КАРТ ИЗ КАТАЛОГА (источник правды core/cards/catalog.py) — список НЕ
# ведётся вручную, а собирается динамически: новая карта в catalog.py автоматически
# появляется в библиотеке. Вкладки: «Все» (весь пул) + «Общие» (generic) + по классу
# (только классовые карты — срез идентичности для ревизии).
from core.cards.catalog import GENERIC_FACTORIES, RAW_FACTORIES, get_class_cards

# Весь пул (generic + все классовые), в порядке регистрации в каталоге.
ALL_CARDS = list(RAW_FACTORIES.values())

# Только нейтральные карты (общий пул всех классов).
GENERIC_CARDS = list(GENERIC_FACTORIES)

# Вкладки. Классовые вкладки = ТОЛЬКО классовые карты (generic вынесены в «Общие»),
# чтобы наглядно читался срез идентичности класса. Классы без своих карт пропускаются.
_CLASS_TABS = [
    ("Тестировщик", "Warrior"),
    ("Вайб-кодер",  "Mage"),
    ("Стажёр",      "Berserker"),
]

TABS = [
    ("Все",   ALL_CARDS),
    ("Общие", GENERIC_CARDS),
]
for _label, _cls in _CLASS_TABS:
    _cards = get_class_cards(_cls)
    if _cards:
        TABS.append((_label, _cards))

# Геометрия сетки
CARD_W, CARD_H = 180, 250
COLS    = 8
GAP_X   = 20
GAP_Y   = 30
START_X = 60
START_Y = 200
