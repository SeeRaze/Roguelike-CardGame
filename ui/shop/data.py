# ui/shop/data.py
# Магазин: палитра, цены, генерация витрины. Без pygame.
# Пул карт берётся из единого каталога (core/cards/catalog.py) с учётом класса.
import random
from core.cards.catalog import get_pool_for_class

# ─── Палитра (тёмно-зелёная/золотая, стиль EventView) ────────────────────────
_BG_COLOR        = (10,  15,  10)
_PANEL_COLOR     = (18,  28,  18)
_BTN_COLOR       = (30,  55,  30)
_BTN_HOVER_COLOR = (55,  100, 55)
_BTN_BORDER      = (140, 200, 100)
_TITLE_COLOR     = (255, 220, 60)
_TEXT_COLOR      = (200, 210, 190)
_GOLD_COLOR      = (255, 215, 0)
_RED_COLOR       = (220, 80,  60)
_GRAY_COLOR      = (120, 120, 120)
_SOLD_COLOR      = (40,  50,  40)


def get_card_price(floor: int) -> int:
    return 35 + floor * 3


def pick_two_cards(class_name=None):
    """Две случайные разные карты для витрины (готовые экземпляры).
    Пул = generic + классовые карты класса игрока (class_name)."""
    pool  = get_pool_for_class(class_name)
    picks = random.sample(pool, 2)
    return picks[0](), picks[1]()
