# tests/test_reaction_order.py
# Единый порядок-приоритет боевых реакций (ревизия ядра, пункт 2).
# R0: чистая таблица приоритетов + детерминированная сортировка реестров.
from core.ReactionOrder import ReactionPriority, order_keyed


# ═══════════════════════════════════════════════════════════
# R0 — таблица приоритетов
# ═══════════════════════════════════════════════════════════

def test_приоритеты_строго_возрастают_в_порядке_цепочки():
    # Комбо раньше детонаций, детонации раньше эха, эхо раньше тиков статусов,
    # тики раньше хуков реликвий/врагов — порядок розыгрыша карты → фазы врага.
    assert ReactionPriority.COMBO < ReactionPriority.SHOCK
    assert ReactionPriority.SHOCK < ReactionPriority.FORGE_TAG
    assert ReactionPriority.FORGE_TAG < ReactionPriority.DETONATION
    assert ReactionPriority.DETONATION < ReactionPriority.ECHO
    assert ReactionPriority.ECHO < ReactionPriority.STATUS_TICK
    assert ReactionPriority.STATUS_TICK < ReactionPriority.RELIC_HOOK
    assert ReactionPriority.RELIC_HOOK < ReactionPriority.ENEMY_HOOK


def test_приоритеты_уникальны():
    values = [p.value for p in ReactionPriority]
    assert len(values) == len(set(values))


def test_приоритет_это_int():
    # IntEnum → можно сравнивать и сортировать как числа без .value.
    assert ReactionPriority.COMBO == 10
    assert int(ReactionPriority.DETONATION) == 40


# ═══════════════════════════════════════════════════════════
# R0 — детерминированная сортировка реестров
# ═══════════════════════════════════════════════════════════

def test_order_keyed_сортирует_по_имени_при_общем_приоритете():
    # Однородное семейство (один приоритет) → стабильный алфавит по ключу,
    # независимо от порядка вставки в dict.
    records = {"z": {"v": 1}, "a": {"v": 2}, "m": {"v": 3}}
    keys = [k for k, _ in order_keyed(records, ReactionPriority.DETONATION)]
    assert keys == ["a", "m", "z"]


def test_order_keyed_стабилен_независимо_от_порядка_вставки():
    r1 = {"electro_blast": {}, "lava": {}, "acid": {}}
    r2 = {"acid": {}, "electro_blast": {}, "lava": {}}
    assert order_keyed(r1, ReactionPriority.DETONATION) and True
    assert [k for k, _ in order_keyed(r1, ReactionPriority.DETONATION)] == \
           [k for k, _ in order_keyed(r2, ReactionPriority.DETONATION)]


def test_order_keyed_принимает_функцию_приоритета():
    # Разнородные приоритеты на запись: сортируем по prio, затем по ключу.
    records = {
        "b": {"prio": 50},
        "a": {"prio": 10},
        "c": {"prio": 10},
    }
    keys = [k for k, _ in order_keyed(records, lambda rec: rec["prio"])]
    assert keys == ["a", "c", "b"]   # 10:a,c (алфавит) → 50:b
