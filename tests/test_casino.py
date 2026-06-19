# tests/test_casino.py
# Этап 2 С70: казино мета-прогрессии (core/casino.py) + разведение пулов в progression.py.

import random

import pytest

from core import casino, progression


# ─── Инвариант разведённых пулов ──────────────────────────────────────────────

def test_pool_disjoint_invariant():
    """ACHIEVEMENT_GRANT_* и CASINO_POOL_* не пересекаются."""
    assert not (progression.ACHIEVEMENT_GRANT_CARDS & progression.casino_pool_cards())
    assert not (progression.ACHIEVEMENT_GRANT_RELICS & progression.casino_pool_relics())


def test_achievement_grants_are_subset_of_locked():
    """Грантить можно только то, что вообще заперто (нельзя «открыть» стартовое)."""
    assert progression.ACHIEVEMENT_GRANT_CARDS <= progression.LOCKED_CARDS
    assert progression.ACHIEVEMENT_GRANT_RELICS <= progression.LOCKED_RELICS


def test_casino_pool_currently_full_locked():
    """На Этапе 2 (ачивки пустые) пул казино = весь LOCKED."""
    assert progression.casino_pool_cards()  == progression.LOCKED_CARDS
    assert progression.casino_pool_relics() == progression.LOCKED_RELICS


# ─── try_spin: счастливый путь ────────────────────────────────────────────────

def _fresh_meta(xp=0):
    """Пустая мета с заданным запасом Опыта."""
    return {"xp": xp, "grade_xp": 0, "casino_seen": [], "casino_bans": [],
            "unlocks": [], "achievements": [], "keepsake": None}


def test_spin_succeeds_with_enough_xp():
    meta = _fresh_meta(xp=200)
    res = casino.try_spin(meta, rng=random.Random(42))
    assert res["ok"] is True
    assert res["kind"] in ("card", "relic")
    assert res["id"] is not None
    # Списано 100 Опыта.
    assert meta["xp"] == 100
    # Накопительный счётчик НЕ затронут (Грейд фиксируется).
    assert meta["grade_xp"] == 0
    # Предмет в casino_seen и unlocks.
    assert res["id"] in meta["casino_seen"]
    assert res["id"] in meta["unlocks"]


def test_spin_grants_unlock_visible_to_progression():
    """После крутки is_card_unlocked / is_relic_unlocked возвращают True
    для выпавшего предмета (один namespace меты)."""
    meta = _fresh_meta(xp=500)
    res = casino.try_spin(meta, rng=random.Random(123))
    assert res["ok"]
    if res["kind"] == "card":
        assert progression.is_card_unlocked(meta, res["id"])
    else:
        assert progression.is_relic_unlocked(meta, res["id"])


def test_spin_no_duplicates_across_many_pulls():
    """50 круток подряд — все выпавшие предметы РАЗНЫЕ (casino_seen фильтрует)."""
    meta = _fresh_meta(xp=50 * 100)   # хватит на 50 круток
    rng = random.Random(7)
    seen_ids: list = []
    for _ in range(50):
        res = casino.try_spin(meta, rng=rng)
        assert res["ok"], f"крутка #{len(seen_ids)+1} провалилась: {res}"
        seen_ids.append(res["id"])
    assert len(seen_ids) == len(set(seen_ids)), "крутка вернула дубль"


# ─── try_spin: отказы (идемпотентность мета) ──────────────────────────────────

def test_spin_no_meta_returns_failure():
    res = casino.try_spin(None)
    assert res["ok"] is False
    assert res["reason"] == "no_meta"


def test_spin_not_enough_xp_does_not_mutate():
    meta = _fresh_meta(xp=99)        # на 1 меньше CASINO_SPIN_COST
    snapshot = {k: list(v) if isinstance(v, list) else v for k, v in meta.items()}
    res = casino.try_spin(meta)
    assert res["ok"] is False
    assert res["reason"] == "not_enough_xp"
    assert meta == snapshot          # мета не тронута


def test_spin_pool_empty_does_not_charge():
    """Если все предметы уже выкручены/забанены — крутка не списывает Опыт."""
    meta = _fresh_meta(xp=500)
    # Симулируем «всё выкручено» — кладём весь пул в casino_seen.
    meta["casino_seen"] = list(progression.casino_pool_cards() | progression.casino_pool_relics())
    res = casino.try_spin(meta)
    assert res["ok"] is False
    assert res["reason"] == "pool_empty"
    assert meta["xp"] == 500         # Опыт цел


def test_spin_skips_banned_items():
    """Забаненный предмет никогда не выпадет (но казино не списывает xp если
    все остальные тоже исчерпаны)."""
    meta = _fresh_meta(xp=200)
    # Забаним один случайный предмет из пула.
    pool = sorted(progression.casino_pool_cards())
    banned = pool[0]
    meta["casino_bans"] = [banned]
    # Прокрутим 10 раз — забаненный не должен ни разу выпасть.
    rng = random.Random(11)
    for _ in range(10):
        meta["xp"] = 200             # обновляем баланс
        meta["casino_seen"] = []     # сбрасываем seen — иначе пул сжимается
        res = casino.try_spin(meta, rng=rng)
        if res["ok"]:
            assert res["id"] != banned


# ─── Перманент-баны (L2+) ─────────────────────────────────────────────────────

@pytest.mark.parametrize("grade_xp,expected_cap", [
    (0, 0),       # L0 — нельзя банить
    (149, 0),     # ещё L0
    (150, 0),    # L1 — всё ещё нельзя
    (599, 0),    # L1
    (600, 1),     # L2 — 1 слот
    (1800, 2),    # L3 — 2 слота
    (4000, 3),    # L4 — 3 слота
])
def test_bans_capacity_by_grade(grade_xp, expected_cap):
    meta = _fresh_meta()
    meta["grade_xp"] = grade_xp
    assert casino.bans_capacity(meta) == expected_cap


def test_ban_item_requires_l2():
    """На L0/L1 ban_item возвращает False, бан не записан."""
    meta = _fresh_meta()                                   # L0
    target = next(iter(progression.casino_pool_cards()))
    assert casino.ban_item(meta, target) is False
    assert meta["casino_bans"] == []


def test_ban_item_at_l2_works():
    meta = _fresh_meta()
    meta["grade_xp"] = 600                                  # L2
    target = next(iter(progression.casino_pool_cards()))
    assert casino.ban_item(meta, target) is True
    assert target in meta["casino_bans"]


def test_ban_item_respects_capacity():
    """L2 даёт ОДИН слот: первый бан — ок, второй — False."""
    meta = _fresh_meta()
    meta["grade_xp"] = 600                                  # L2 = capacity 1
    pool = sorted(progression.casino_pool_cards())
    a, b = pool[0], pool[1]
    assert casino.ban_item(meta, a) is True
    assert casino.ban_item(meta, b) is False                # capacity исчерпан
    assert meta["casino_bans"] == [a]


def test_ban_item_rejects_non_pool_items():
    """Запретить можно только то, что выпадает в казино."""
    meta = _fresh_meta()
    meta["grade_xp"] = 600
    assert casino.ban_item(meta, "strike") is False         # стартовая, не в пуле
    assert casino.ban_item(meta, "Warrior") is False        # это класс, не предмет
    assert meta["casino_bans"] == []


def test_ban_item_rejects_dupe():
    meta = _fresh_meta()
    meta["grade_xp"] = 1800                                 # L3 = capacity 2
    target = next(iter(progression.casino_pool_cards()))
    assert casino.ban_item(meta, target) is True
    assert casino.ban_item(meta, target) is False           # уже забанен


def test_ban_item_no_meta():
    assert casino.ban_item(None, "anything") is False
