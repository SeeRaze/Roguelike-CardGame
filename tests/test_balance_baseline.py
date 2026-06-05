# tests/test_balance_baseline.py
# Регресс-гард баланса как pytest (маркер `balance`, МЕДЛЕННЫЙ ~15с).
# Дефолтный `pytest` его ПРОПУСКАЕТ (pytest.ini: addopts -m "not balance").
# Запуск: pytest -m balance. Машинерия и эталон — managers/balance/baseline.py.
# В CI тот же гард гоняется plain-python (без pytest/pygame):
#   python -m managers.balance.baseline --check
import pytest

from managers.balance.baseline import (
    CLASSES, BASELINE, BASELINE_MAX_DROP, BASELINE_MAX_RISE, measure_class,
)

pytestmark = pytest.mark.balance


@pytest.mark.parametrize("player_class", CLASSES, ids=lambda c: c.__name__)
def test_класс_в_допуске_баланса(player_class):
    """Медианы wall/ceiling класса не вышли за допуск относительно эталона.
    Просадка > MAX_DROP = регресс (контент ослабил класс); рост > MAX_RISE =
    подозрительный всплеск (баг). Переблагословить: python -m managers.balance.baseline."""
    name = player_class.__name__
    cur = measure_class(player_class)
    base = BASELINE[name]
    for metric in ("wall", "ceiling"):
        diff = cur[metric] - base[metric]
        assert diff >= -BASELINE_MAX_DROP, (
            f"{name} {metric} ОБВАЛ: {cur[metric]:g} vs эталон {base[metric]:g}. "
            f"Осознанно? Переблагослови: python -m managers.balance.baseline")
        assert diff <= BASELINE_MAX_RISE, (
            f"{name} {metric} ВСПЛЕСК: {cur[metric]:g} vs эталон {base[metric]:g} "
            f"(возможен баг вроде несброса статусов между боями).")
