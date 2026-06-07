# tests/test_balance_stakes.py
# Sim-интеграция Ставок (RuleStack сим-нативен): run_single_run(stakes=...).
# Проверяем: stakes=None регресс-нейтрально (== без аргумента), активная Ставка
# детерминирована и измеримо сдвигает исход. Быстрые прогоны (без маркера balance).
import contextlib
import os
import random
import statistics

from core.players import Mage, Warrior
from managers.balance.runner import run_single_run


def _run(seed, **kw):
    random.seed(seed)
    with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
        return run_single_run(Warrior, 100, **kw)


def _median(seed, n=20, cls=Warrior, **kw):
    random.seed(seed)
    with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
        runs = [run_single_run(cls, 100, **kw) for _ in range(n)]
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


def test_аскет_роняет_выживаемость():
    """Калибровка С46 (true ascension): «Аскет» (≤6 карт, без награды) роняет
    медиану смерти — для Мага (несовместим с обрезкой). Доказывает сим-нативность
    слома: RuleStack измеримо влияет на симуляцию, причём ВНИЗ (опт-ин сложность)."""
    base    = _median(99, cls=Mage, stakes=None)
    ascetic = _median(99, cls=Mage, stakes=["ascetic"])
    assert ascetic < base


def test_хрупкость_роняет_выживаемость():
    """«Хрупкость» (30% HP) — универсальный ascension-штраф: медиана падает у Воина."""
    base    = _median(99, cls=Warrior, stakes=None)
    fragile = _median(99, cls=Warrior, stakes=["fragile"])
    assert fragile < base


def test_ставка_по_id_и_по_объекту_эквивалентны():
    """stakes принимает и id-строку, и объект Stake."""
    from core.rules import STAKES
    by_id  = _run(99, stakes=["fragile"])
    by_obj = _run(99, stakes=[STAKES["fragile"]])
    assert by_id["death_floor"] == by_obj["death_floor"]
