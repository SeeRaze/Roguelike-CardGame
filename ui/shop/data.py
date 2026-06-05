# ui/shop/data.py
# Магазин: палитра, цены, генерация витрины. Без pygame.
# Пул карт берётся из единого каталога (core/cards/catalog.py) с учётом класса.
# Реликвии для витрины — через RewardManager.pick_shop_relic (единый источник).
import random
from core.cards.catalog import get_pool_for_class
from core.rarity import Rarity
from managers.RewardManager import pick_shop_relic

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

# ─── Экономика витрины ───────────────────────────────────────────────────────
SHOP_CARD_SLOTS = 5                       # сколько карт на витрине
_KEY_PRICE      = 30                      # цена ключа от сундука
_RELIC_PRICE = {                          # база цены реликвии по редкости
    Rarity.COMMON:   70,
    Rarity.UNCOMMON: 100,
    Rarity.RARE:     140,
    Rarity.EPIC:     200,
    Rarity.LEGENDARY: 280,
}


def get_card_price(floor: int) -> int:
    return 35 + floor * 3


def get_key_price() -> int:
    return _KEY_PRICE


def get_relic_price(relic, floor: int) -> int:
    """Цена реликвии = база по редкости + лёгкий рост с этажом."""
    return _RELIC_PRICE.get(relic.rarity, 100) + floor * 2


def pick_cards(n: int, class_name=None):
    """n случайных РАЗНЫХ карт для витрины (готовые экземпляры).
    Пул = generic + классовые карты класса игрока (class_name)."""
    pool = get_pool_for_class(class_name)
    n    = min(n, len(pool))
    return [factory() for factory in random.sample(pool, n)]


def pick_relic(gm):
    """Реликвия для витрины (или None, если все собраны)."""
    return pick_shop_relic(gm)
