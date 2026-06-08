# ui/shop/data.py
# Магазин: палитра, цены, генерация витрины. Без pygame.
# Пул карт берётся из единого каталога (core/cards/catalog.py) с учётом класса.
# Реликвии для витрины — через RewardManager.pick_shop_relic (единый источник).
import random
from core.cards.catalog import get_pool_for_class
from core.rarity import Rarity
from core import forge as forge_mod
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
ROB_SUCCESS_CHANCE = 0.30                 # шанс украсть реликвию («Ограбление»)
_KEY_PRICE      = 30                      # цена ключа от сундука
# Шанс, что КОНКРЕТНЫЙ слот витрины выдаст уже выкованную карту (С57, шаг 3
# эконом-дуги: анти-смерть магазина в лейте). Независимо на каждый из 5 слотов →
# редкий джекпот 5/5 = дофамин (replayability-doctrine). Уровень ковки берётся из
# forge.reward_level_for_floor(floor) (растёт по босс-гейтам: 0 до эт.20, далее 5/10/15).
SHOP_FORGE_CHANCE = 0.20
# Надбавка к цене за каждый уровень ковки (платишь золотом за сэкономленный FP).
SHOP_FORGE_PRICE_PER_LEVEL = 12
_RELIC_PRICE = {                          # база цены реликвии по редкости
    Rarity.COMMON:   70,
    Rarity.UNCOMMON: 100,
    Rarity.RARE:     140,
    Rarity.EPIC:     200,
    Rarity.LEGENDARY: 280,
}


def get_card_price(floor: int) -> int:
    return 35 + floor * 3


def get_forged_card_price(card, player, floor: int) -> int:
    """Цена карты с учётом ковки: база по этажу + надбавка за уровень (платишь
    золотом за сэкономленный FP-прогресс). Некованая карта = базовая цена."""
    level = forge_mod.forge_level(player, card)
    return get_card_price(floor) + level * SHOP_FORGE_PRICE_PER_LEVEL


def get_key_price() -> int:
    return _KEY_PRICE


def get_relic_price(relic, floor: int) -> int:
    """Цена реликвии = база по редкости + лёгкий рост с этажом."""
    return _RELIC_PRICE.get(relic.rarity, 100) + floor * 2


def pick_cards(n: int, class_name=None, player=None, floor: int = 1):
    """n случайных РАЗНЫХ карт для витрины (готовые экземпляры).
    Пул = generic + классовые карты класса игрока (class_name).

    С57 (шаг 3): если передан player, каждый слот НЕЗАВИСИМО с шансом
    SHOP_FORGE_CHANCE выковывается до reward_level_for_floor(floor) (паспорт
    пишется на player; некупленные снимаются Shop при выходе). Уровень 0 (до
    первого босса) → ковка no-op, карты обычные."""
    pool = get_pool_for_class(class_name)
    n    = min(n, len(pool))
    cards = [factory() for factory in random.sample(pool, n)]
    if player is not None:
        level = forge_mod.reward_level_for_floor(floor)
        if level > 0:
            for card in cards:
                if random.random() < SHOP_FORGE_CHANCE:
                    forge_mod.forge_card_to_level(player, card, level,
                                                  class_name or "")
    return cards


def pick_relic(gm):
    """Реликвия для витрины (или None, если все собраны)."""
    return pick_shop_relic(gm)
