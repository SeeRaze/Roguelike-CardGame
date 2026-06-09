# tests/test_balance_hp_debt.py
# Sim-интеграция ДОЛГА HP (§4, субстрат Берсерка): run_single_run(hp_debt=...).
# Ось развязана с энерго-долгом (debt=) — чистый A/B по каждой.
#
# NB (находка С49): HP-долг = отложенная смерть (буфер до пола −50% max HP + множитель
# урона в минусе). На глубоких этажах это делает классы со ЩИТОМ (Воин) ПОЧТИ
# НЕУБИВАЕМЫМИ — бой упирается в max_turns каждый этаж, прогон до 100 этажей стопорится
# («стол»). Поэтому медиана death_floor на 100 этажей здесь НЕинформативна; механика
# доказана юнит-тестами (test_hp_debt.py). Сим-слой проверяет интеграцию: регресс-
# нейтральность флага + детерминизм на МЕЛКОМ капе (без глубокого стола).
import contextlib
import os
import random

from core.players import Warrior
from managers.balance.runner import run_single_run


def _run(seed, cap=100, **kw):
    random.seed(seed)
    with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
        return run_single_run(Warrior, cap, **kw)


def test_hp_debt_false_равно_без_аргумента():
    """Базовый забег: hp_debt=False не отличается от вызова без аргумента (регресс-нейтр.)."""
    a = _run(99)
    b = _run(99, hp_debt=False)
    assert a["death_floor"] == b["death_floor"]


def test_hp_debt_не_трогает_энерго_ось():
    """Развязка осей: hp_debt не меняет результат относительно debt-флага в отдельности
    (HP-долг ставит только hp_overdraft, не energy_overdraft)."""
    a = _run(99, debt=True)
    b = _run(99, debt=True, hp_debt=False)
    assert a["death_floor"] == b["death_floor"]


def test_hp_debt_детерминирован():
    """HP-овердрафт в симе детерминирован (мелкий кап — без глубокого стола)."""
    a = _run(99, cap=8, hp_debt=True)
    b = _run(99, cap=8, hp_debt=True)
    assert a["death_floor"] == b["death_floor"]


def test_hp_debt_интегрируется_без_падений():
    """Бот floor-aware: прогон с hp_overdraft проходит без исключений и даёт валидный
    результат (death_floor = int или None при выживании). Интеграция runner+bot+ядро."""
    r = _run(7, cap=8, hp_debt=True)
    assert r["death_floor"] is None or isinstance(r["death_floor"], int)
