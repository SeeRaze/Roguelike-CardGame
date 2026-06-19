# tests/test_grade_rewards.py
# С70 полировка (П2b): разовые бонусы ступеней Грейда — claim_grade_rewards +
# бесплатная крутка казино (L1 «Первый PR»).

import random

from core import meta_currency, casino


def _meta(grade_xp=0, **extra):
    m = {"xp": 0, "grade_xp": grade_xp, "free_spins": 0, "claimed_grades": [],
         "casino_seen": [], "casino_bans": [], "unlocks": [], "achievements": []}
    m.update(extra)
    return m


# ─── claim_grade_rewards ──────────────────────────────────────────────────────

def test_no_claim_below_l1():
    m = _meta(grade_xp=149)
    assert meta_currency.claim_grade_rewards(m) == []
    assert m["free_spins"] == 0
    assert m["claimed_grades"] == []


def test_claim_l1_grants_free_spin():
    m = _meta(grade_xp=150)
    newly = meta_currency.claim_grade_rewards(m)
    assert newly == [1]
    assert m["free_spins"] == 1
    assert 1 in m["claimed_grades"]


def test_claim_is_idempotent():
    m = _meta(grade_xp=200)
    meta_currency.claim_grade_rewards(m)
    again = meta_currency.claim_grade_rewards(m)
    assert again == []
    assert m["free_spins"] == 1          # не задвоилось


def test_claim_jump_to_l3_only_l1_gives_spin():
    # Перепрыгнули сразу на L3 (1800): отмечаются ступени 1..3, но бесплатную
    # крутку даёт только L1 (L2/L3 — пассивные права).
    m = _meta(grade_xp=1800)
    newly = meta_currency.claim_grade_rewards(m)
    assert newly == [1, 2, 3]
    assert m["free_spins"] == 1
    assert m["claimed_grades"] == [1, 2, 3]


def test_claim_none_meta_safe():
    assert meta_currency.claim_grade_rewards(None) == []


# ─── Казино: бесплатная крутка ────────────────────────────────────────────────

def test_free_spin_used_without_xp():
    m = _meta(grade_xp=0, free_spins=1, xp=0)
    res = casino.try_spin(m, rng=random.Random(1))
    assert res["ok"] is True
    assert res["free"] is True
    assert m["free_spins"] == 0
    assert m["xp"] == 0                    # Опыт не тронут


def test_free_spin_consumed_before_xp():
    # Есть и бесплатная, и Опыт — тратится сперва бесплатная.
    m = _meta(grade_xp=0, free_spins=1, xp=200)
    res = casino.try_spin(m, rng=random.Random(2))
    assert res["ok"] and res["free"] is True
    assert m["free_spins"] == 0
    assert m["xp"] == 200                  # Опыт не списан


def test_paid_spin_when_no_free():
    m = _meta(grade_xp=0, free_spins=0, xp=200)
    res = casino.try_spin(m, rng=random.Random(3))
    assert res["ok"] and res["free"] is False
    assert m["xp"] == 100                  # списано 100 Опыта


def test_no_spin_without_free_or_xp():
    m = _meta(grade_xp=0, free_spins=0, xp=50)
    res = casino.try_spin(m, rng=random.Random(4))
    assert res["ok"] is False
    assert res["reason"] == "not_enough_xp"
    assert m["xp"] == 50                    # ничего не списано
