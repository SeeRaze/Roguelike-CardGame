# ui/shop/data.py
# Магазин: палитра, пул карт, цены, генерация витрины. Без pygame.
import random
from core.cards import (
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_bash, create_neutralize, create_intimidate,
    create_ignite, create_fire_breath,
    create_splash, create_rain_cloud,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
)
from core.cards.heal import create_bandage, create_second_wind, create_elixir
from core.cards.buff.regen import create_regenerate, create_vitality, create_triage
from core.cards.buff.vampirism import create_drain, create_blood_feast, create_life_tap
from core.cards.debuff.bleed import create_lacerate, create_hemorrhage, create_open_wound

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

# Пул карт витрины
_CARD_POOL = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_bash, create_neutralize, create_intimidate,
    create_ignite, create_fire_breath,
    create_splash, create_rain_cloud,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_drain, create_blood_feast, create_life_tap,
    create_lacerate, create_hemorrhage, create_open_wound,
]


def get_card_price(floor: int) -> int:
    return 35 + floor * 3


def pick_two_cards():
    """Две случайные разные карты для витрины (готовые экземпляры)."""
    picks = random.sample(_CARD_POOL, 2)
    return picks[0](), picks[1]()
