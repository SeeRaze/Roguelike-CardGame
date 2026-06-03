# ui/library/data.py
# Библиотека карт: списки карт по классам, вкладки, геометрия сетки.
# Растёт с контентом: новая карта класса -> строка в соответствующий список.
from core.cards import (
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_ignite, create_fire_breath, create_splash, create_rain_cloud,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
    create_bash, create_neutralize, create_intimidate,
    create_flex, create_battle_cry, create_thorn_armor,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_drain, create_blood_feast, create_life_tap,
    create_lacerate, create_hemorrhage, create_open_wound,
)

WARRIOR_CARDS = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_flex, create_battle_cry, create_thorn_armor, create_bash,
]

ROGUE_CARDS = [
    create_strike, create_defend,
    create_neutralize, create_intimidate,
    create_lacerate, create_hemorrhage, create_open_wound,
    create_drain, create_blood_feast,
]

MAGE_CARDS = [
    create_strike, create_defend,
    create_ignite, create_fire_breath,
    create_splash, create_rain_cloud,
    create_bash, create_acid_shield,
]

DRUID_CARDS = [
    create_strike, create_defend,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_poison_stab, create_toxic_cloud,
]

BERSERKER_CARDS = [
    create_strike, create_defend,
    create_heavy_blade, create_iron_wall,
    create_flex, create_battle_cry,
    create_life_tap,                    # вампиризм -- балансировать на грани
    create_lacerate,                    # кровь -- давление
]

ALL_CARDS = list({f.__name__: f for f in
    WARRIOR_CARDS + ROGUE_CARDS + MAGE_CARDS +
    DRUID_CARDS + BERSERKER_CARDS}.values())

TABS = [
    ("Все",       ALL_CARDS),
    ("Воин",      WARRIOR_CARDS),
    ("Разбойник", ROGUE_CARDS),
    ("Маг",       MAGE_CARDS),
    ("Друид",     DRUID_CARDS),
    ("Берсерк",   BERSERKER_CARDS),
]

# Геометрия сетки
CARD_W, CARD_H = 180, 250
COLS    = 8
GAP_X   = 20
GAP_Y   = 30
START_X = 60
START_Y = 200
