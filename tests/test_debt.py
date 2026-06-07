# tests/test_debt.py
# Долговой движок — срез на ЭНЕРГИИ (§7). Подзадача 1: pure-формула множителя +
# шаг 8-bis EffectCalculator (инертен при energy>=0). Чистая логика, без pygame.
from types import SimpleNamespace

import core.debt as debt
from core.debt import energy_debt_multiplier
from core.Creature import Creature
from core.EffectCalculator import EffectCalculator


def test_формула_инертна_без_долга():
    assert energy_debt_multiplier(0) == 1.0
    assert energy_debt_multiplier(-3) == 1.0          # отрицат. debt трактуется как нет долга


def test_линейная_кривая_дефолт():
    assert energy_debt_multiplier(1) == 1.25          # +0.25/ед.
    assert energy_debt_multiplier(4) == 2.0           # кап-глубина → ×2


def test_экспонента_включается_рубильником(monkeypatch):
    monkeypatch.setattr(debt, "DEBT_CURVE_MODE", "exp")
    monkeypatch.setattr(debt, "DEBT_EXP_RATE", 0.2)
    assert energy_debt_multiplier(1) == 1.2
    assert round(energy_debt_multiplier(2), 4) == 1.44   # (1.2)^2


def _hit(player, base=10):
    """Урон игрока по болванке через сквозной расчёт (player ДОЛЖЕН быть cm.player)."""
    target = Creature("Враг", 100, 100)
    gm = SimpleNamespace(relics=[], stats={}, rulestack=None)
    cm = SimpleNamespace(player=player, gm=gm, add_log_message=lambda _: None)
    return EffectCalculator.calculate_damage(player, target, base,
                                             game_manager=gm, combat_manager=cm)


def test_долг_энергии_множит_урон_игрока():
    player = Creature("Игрок", 50, 50)
    player.energy = -2                                  # долг 2 → ×1.5
    assert _hit(player, 10) == 15


def test_положительная_энергия_не_трогает_урон():
    player = Creature("Игрок", 50, 50)
    player.energy = 3                                   # нет долга → инертно
    assert _hit(player, 10) == 10
