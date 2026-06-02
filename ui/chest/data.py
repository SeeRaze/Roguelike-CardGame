import random

from core.cards.basic import (
    create_strike, create_defend,
    create_heavy_blade, create_iron_wall,
)
from core.cards.fire    import create_ignite, create_fire_breath
from core.cards.poison  import create_poison_stab, create_toxic_cloud, create_acid_shield
from core.cards.buff.strength  import create_flex, create_battle_cry
from core.cards.buff.thorns    import create_thorn_armor
from core.cards.debuff.vulnerable import create_bash
from core.cards.debuff.weak       import create_neutralize, create_intimidate
from core.cards.heal             import create_bandage, create_second_wind, create_elixir
from core.cards.buff.regen       import create_regenerate, create_vitality, create_triage
from core.cards.buff.vampirism   import create_drain, create_blood_feast, create_life_tap
from core.cards.debuff.bleed     import create_lacerate, create_hemorrhage, create_open_wound

CHEST_CARD_POOL = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_ignite, create_fire_breath,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
    create_flex, create_battle_cry,
    create_thorn_armor,
    create_bash,
    create_neutralize, create_intimidate,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_drain, create_blood_feast, create_life_tap,
    create_lacerate, create_hemorrhage, create_open_wound,
]

CURSED_BUFF_POOL = [
    (
        "+3 Ярости",
        "Постоянный бонус +3 к урону всех атак.",
        15,
        lambda gm: setattr(gm.player, "strength",
                           getattr(gm.player, "strength", 0) + 3),
    ),
    (
        "+5 Шипов",
        "Постоянный бонус: отражать +5 урона атакующему.",
        12,
        lambda gm: setattr(gm.player, "thorns",
                           getattr(gm.player, "thorns", 0) + 5),
    ),
    (
        "+1 Энергия",
        "Максимальная энергия +1 навсегда.",
        20,
        lambda gm: setattr(gm.player, "max_energy", gm.player.max_energy + 1),
    ),
    (
        "+15 Щита",
        "Немедленно получить 15 щита.",
        10,
        lambda gm: gm.player.gain_shield(15),
    ),
    (
        "+25 Золота",
        "Найти 25 монет в тёмных глубинах сундука.",
        8,
        lambda gm: setattr(gm, "player_gold", gm.player_gold + 25),
    ),
    (
        "+1 Карта/ход",
        "Добирать на 1 карту больше в начале каждого боя.",
        18,
        lambda gm: setattr(gm.player, "bonus_draw",
                           getattr(gm.player, "bonus_draw", 0) + 1),
    ),
]

CHEST_TYPES   = ["common", "locked", "cursed"]
CHEST_WEIGHTS = [33, 33, 34]


def pick_chest_type():
    return random.choices(CHEST_TYPES, weights=CHEST_WEIGHTS, k=1)[0]


def generate_chest_cards(count=2):
    factories = random.sample(CHEST_CARD_POOL, min(count, len(CHEST_CARD_POOL)))
    return [f() for f in factories]


def generate_cursed_buffs(count=3):
    return random.sample(CURSED_BUFF_POOL, min(count, len(CURSED_BUFF_POOL)))