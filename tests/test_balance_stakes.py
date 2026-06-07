# tests/test_balance_stakes.py
# Sim-интеграция Ставок (RuleStack сим-нативен): run_single_run(stakes=...).
# Проверяем: stakes=None регресс-нейтрально (== без аргумента), активная Ставка
# детерминирована и измеримо сдвигает исход. Быстрые прогоны (без маркера balance).
import contextlib
import os
import random
import statistics

from core.players import Warrior
from managers.balance.runner import run_single_run


def _run(seed, **kw):
    random.seed(seed)
    with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
        return run_single_run(Warrior, 100, **kw)


def _median(seed, n=20, **kw):
    random.seed(seed)
    with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
        runs = [run_single_run(Warrior, 100, **kw) for _ in range(n)]
    vals = [r["death_floor"] if r["death_floor"] is not None else 100 for r in runs]
    return statistics.median(vals)


def test_stakes_none_равно_без_аргумента():
    """Базовый забег: stakes=None не отличается от вызова без stakes (регресс-нейтр.)."""
    a = _run(99)
    b = _run(99, stakes=None)
    assert a["death_floor"] == b["death_floor"]


def test_активная_ставка_детерминирована():
    """Один seed + одна Ставка → одинаковый исход (моды без per-run состояния)."""
    a = _run(99, stakes=["ascetic"])
    b = _run(99, stakes=["ascetic"])
    assert a["death_floor"] == b["death_floor"]


def test_ставка_измеримо_сдвигает_медиану():
    """«Аскет» (урон ×1.5) заметно двигает медиану относительно базового забега —
    доказывает, что RuleStack влияет на симуляцию (сим-нативность слома)."""
    base    = _median(99, stakes=None)
    ascetic = _median(99, stakes=["ascetic"])
    assert ascetic != base


def test_ставка_по_id_и_по_объекту_эквивалентны():
    """stakes принимает и id-строку, и объект Stake."""
    from core.rules import STAKES
    by_id  = _run(99, stakes=["fragile"])
    by_obj = _run(99, stakes=[STAKES["fragile"]])
    assert by_id["death_floor"] == by_obj["death_floor"]
