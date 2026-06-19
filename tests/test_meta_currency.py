# tests/test_meta_currency.py
# Этап 1 С70: фундамент мета-валюты Опыт+Грейд (core/meta_currency.py) +
# merge-safe загрузка SaveManager на старых сейвах + +50 за забег в record_run.

import json

import pytest

from core import meta_currency as mc
from managers import SaveManager as SM


@pytest.fixture
def isolated_save(tmp_path, monkeypatch):
    """SaveManager пишет в tmp_path; кэш сброшен до и после."""
    save_file = tmp_path / "meta_save.json"
    monkeypatch.setattr(SM, "get_save_path", lambda: save_file)
    SM.reset_cache()
    yield save_file
    SM.reset_cache()


# ─── grant_xp / spend_xp ──────────────────────────────────────────────────────

def test_grant_xp_grows_both_counters():
    meta = {"xp": 0, "grade_xp": 0}
    mc.grant_xp(meta, 50)
    assert meta["xp"] == 50
    assert meta["grade_xp"] == 50


def test_grant_xp_accumulates():
    meta = {"xp": 0, "grade_xp": 0}
    mc.grant_xp(meta, 10)
    mc.grant_xp(meta, 30)
    mc.grant_xp(meta, 5)
    assert meta["xp"] == 45
    assert meta["grade_xp"] == 45


def test_grant_xp_zero_or_negative_no_op():
    meta = {"xp": 100, "grade_xp": 100}
    mc.grant_xp(meta, 0)
    mc.grant_xp(meta, -50)
    assert meta["xp"] == 100
    assert meta["grade_xp"] == 100


def test_grant_xp_none_meta_is_no_op():
    # Контракт «sim/baseline слеп»: при meta=None функция не падает и не мутирует.
    mc.grant_xp(None, 100)   # просто не должно упасть


def test_grant_xp_works_on_missing_keys():
    # Старый сейв без xp/grade_xp — функция подставит 0 и начислит.
    meta = {}
    mc.grant_xp(meta, 25)
    assert meta["xp"] == 25
    assert meta["grade_xp"] == 25


def test_spend_xp_returns_true_when_enough():
    meta = {"xp": 200, "grade_xp": 500}
    assert mc.spend_xp(meta, 100) is True
    assert meta["xp"] == 100
    # grade_xp НЕ трогаем (фиксированный «жизненный опыт»).
    assert meta["grade_xp"] == 500


def test_spend_xp_returns_false_when_not_enough():
    meta = {"xp": 50, "grade_xp": 1000}
    assert mc.spend_xp(meta, 100) is False
    assert meta["xp"] == 50            # не списано
    assert meta["grade_xp"] == 1000    # тоже не тронут


def test_spend_xp_none_or_invalid_returns_false():
    assert mc.spend_xp(None, 100) is False
    assert mc.spend_xp({"xp": 100}, 0) is False
    assert mc.spend_xp({"xp": 100}, -10) is False


# ─── Грейд (current_grade / next_threshold / xp_to_next) ──────────────────────

@pytest.mark.parametrize("gx,expected", [
    (0, 0),
    (149, 0),
    (150, 1),
    (599, 1),
    (600, 2),
    (1799, 2),
    (1800, 3),
    (3999, 3),
    (4000, 4),
    (10000, 4),       # выше потолка — L4 фиксируется
])
def test_current_grade_thresholds(gx, expected):
    meta = {"grade_xp": gx}
    assert mc.current_grade(meta) == expected


def test_current_grade_none_meta_is_zero():
    assert mc.current_grade(None) == 0


def test_next_threshold_steps_up():
    assert mc.next_threshold({"grade_xp": 0}) == 150
    assert mc.next_threshold({"grade_xp": 200}) == 600
    assert mc.next_threshold({"grade_xp": 700}) == 1800
    assert mc.next_threshold({"grade_xp": 2000}) == 4000


def test_next_threshold_none_at_max_grade():
    assert mc.next_threshold({"grade_xp": 4000}) is None
    assert mc.next_threshold({"grade_xp": 99999}) is None


def test_xp_to_next_counts_down():
    assert mc.xp_to_next({"grade_xp": 0})    == 150
    assert mc.xp_to_next({"grade_xp": 100})  == 50
    assert mc.xp_to_next({"grade_xp": 150})  == 450    # к L2 (600 - 150)
    assert mc.xp_to_next({"grade_xp": 4000}) is None


# ─── SaveManager: merge-safe + +50 за забег ───────────────────────────────────

def test_default_meta_has_progression_keys(isolated_save):
    meta = SM.get_meta()
    assert meta["xp"] == 0
    assert meta["grade_xp"] == 0
    assert meta["achievements"] == []
    assert meta["casino_bans"] == []
    assert meta["casino_seen"] == []
    assert meta["keepsake"] is None


def test_load_old_save_merges_progression_keys(isolated_save):
    # Сейв старой версии без полей прогрессии — после загрузки они должны быть
    # подставлены дефолтами, а stats — сохранены.
    old = {
        "version": SM.SAVE_VERSION,
        "stats": {"total_runs": 5, "best_floor": 12, "total_kills": 30,
                  "total_bosses": 1, "max_damage_ever": 80},
        "class_best": {"Warrior": {"best_floor": 12, "kills": 30,
                                   "max_damage": 80, "runs": 5}},
        "runs":    [{"username": "x", "class": "Warrior", "max_floor": 12,
                     "kills": 30, "max_damage": 80}],
        "unlocks": [],
    }
    isolated_save.write_text(json.dumps(old), encoding="utf-8")
    SM.reset_cache()
    meta = SM.get_meta()
    # Старые данные сохранены.
    assert meta["stats"]["best_floor"] == 12
    assert meta["runs"][0]["username"] == "x"
    # Новые поля прогрессии добавлены merge-safe.
    assert meta["xp"] == 0
    assert meta["grade_xp"] == 0
    assert meta["achievements"] == []
    assert meta["keepsake"] is None


def test_record_run_grants_50_xp(isolated_save):
    meta = SM.get_meta()
    assert meta["xp"] == 0
    SM.record_run({"username": "t", "class": "Warrior", "max_floor": 3,
                   "kills": 5, "bosses": 0, "max_damage": 20})
    meta = SM.get_meta()
    assert meta["xp"] == 50
    assert meta["grade_xp"] == 50


def test_record_run_xp_accumulates_across_runs(isolated_save):
    for _ in range(4):
        SM.record_run({"username": "t", "class": "Warrior", "max_floor": 1,
                       "kills": 0, "bosses": 0, "max_damage": 0})
    meta = SM.get_meta()
    assert meta["xp"] == 200
    assert meta["grade_xp"] == 200
    # 200 grade_xp → ещё L1 (≥150).
    assert mc.current_grade(meta) == 1
