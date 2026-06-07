# tests/test_balance_debt.py
# Sim-интеграция долгового движка (§7 сим-нативен): run_single_run(debt=...).
# Проверяем: debt=False регресс-нейтрально (== без аргумента), долг детерминирован
# и измеримо сдвигает исход (бот «надевает» овердрафт). Быстрые прогоны.
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


def test_debt_false_равно_без_аргумента():
    """Базовый забег: debt=False не отличается от вызова без debt (регресс-нейтр.)."""
    a = _run(99)
    b = _run(99, debt=False)
    assert a["death_floor"] == b["death_floor"]


def test_долг_детерминирован():
    a = _run(99, debt=True)
    b = _run(99, debt=True)
    assert a["death_floor"] == b["death_floor"]


def test_долг_измеримо_сдвигает_медиану():
    """Овердрафт энергии заметно двигает медиану — доказывает сим-нативность
    долгового примитива (бот уходит в долг, power now → pay later)."""
    base = _median(99, debt=False)
    debt = _median(99, debt=True)
    assert debt != base
