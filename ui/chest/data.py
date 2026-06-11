import random

from core.cards.catalog import get_pool_for_class

CURSED_BUFF_POOL = [
    (
        "+3 Ярости",
        "Постоянный бонус +3 к урону всех атак.",
        15,
        lambda gm: setattr(gm.player, "strength",
                           getattr(gm.player, "strength", 0) + 3),
    ),
    (
        "+5 Файрвола",
        "Постоянный бонус: отражать +5 урона атакующему.",
        12,
        lambda gm: setattr(gm.player, "firewall",
                           getattr(gm.player, "firewall", 0) + 5),
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


def generate_chest_cards(count=2, class_name=None, meta=None):
    """Карты для сундука. Пул = generic + классовые карты класса игрока.
    meta (узкий стартовый пул, С57) фильтрует locked-карты; None → весь пул."""
    pool      = get_pool_for_class(class_name, meta)
    factories = random.sample(pool, min(count, len(pool)))
    return [f() for f in factories]


def generate_cursed_buffs(count=3):
    return random.sample(CURSED_BUFF_POOL, min(count, len(CURSED_BUFF_POOL)))