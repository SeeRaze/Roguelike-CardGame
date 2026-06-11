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


def _pooled_median(seeds, n=30, cls=Warrior, **kw):
    """Медиана этажа смерти по ПУЛУ прогонов с нескольких seed.

    Тенденц-тесты Ставок мерят НАПРАВЛЕНИЕ сдвига (Ставка роняет выживаемость).
    Один seed × малый n даёт хрупкий замер: любой RNG-сдвиг от нового контента
    (новая элита/реликвия меняет порядок random.choice) может качнуть медиану на
    1 этаж и опрокинуть строгое неравенство, хотя тенденция сохраняется. Пул по
    нескольким seed усредняет это дрожание → устойчивый прибор тенденции."""
    vals = []
    for seed in seeds:
        random.seed(seed)
        with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
            for _ in range(n):
                r = run_single_run(cls, 100, **kw)
                vals.append(r["death_floor"] if r["death_floor"] is not None else 100)
    return statistics.median(vals)


_TENDENCY_SEEDS = (1, 2, 3, 4, 5)


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


def test_хрупкость_роняет_выживаемость():
    """«Хрупкость» (30% HP) — универсальный ascension-штраф: медиана падает у Воина.
    Замер на ПУЛЕ seed (устойчив к RNG-сдвигам от нового контента)."""
    base    = _pooled_median(_TENDENCY_SEEDS, cls=Warrior, stakes=None)
    fragile = _pooled_median(_TENDENCY_SEEDS, cls=Warrior, stakes=["fragile"])
    assert fragile < base


def test_ставка_по_id_и_по_объекту_эквивалентны():
    """stakes принимает и id-строку, и объект Stake."""
    from core.rules import STAKES
    by_id  = _run(99, stakes=["fragile"])
    by_obj = _run(99, stakes=[STAKES["fragile"]])
    assert by_id["death_floor"] == by_obj["death_floor"]
