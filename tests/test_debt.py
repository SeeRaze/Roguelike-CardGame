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


# ── ДОЛГ HP (С49 субстрат Берсерка; С57 — ПРОЦЕНТНАЯ, МАСШТАБ-ИНВАРИАНТНАЯ ось) ────

def test_hp_формула_инертна_без_долга():
    from core.debt import hp_debt_multiplier
    assert hp_debt_multiplier(0, 60) == 1.0
    assert hp_debt_multiplier(-5, 60) == 1.0           # «отрицат. долг» = нет долга
    assert hp_debt_multiplier(10, 0) == 1.0            # max_hp<=0 → инертно (защита)


def test_hp_линейная_от_доли_дефолт():
    """Множитель от ДОЛИ max HP. На 60 HP ≡ прежней 1+0.10·глубина (дно −30 → ×4.0)."""
    from core.debt import hp_debt_multiplier
    assert round(hp_debt_multiplier(1, 60), 4) == 1.10    # 1 + 6·(1/60)
    assert round(hp_debt_multiplier(10, 60), 4) == 2.0    # 1 + 6·(10/60)
    assert round(hp_debt_multiplier(30, 60), 4) == 4.0    # дно (−50% от 60) → ×4.0


def test_hp_множитель_масштаб_инвариантен():
    """Нырок на ТУ ЖЕ долю пула → ТА ЖЕ награда при любом max HP (суть С57-фикса):
    дно (−50%) даёт ×4.0 и на 60, и на 1000 HP — механика не отмирает с ростом max HP."""
    from core.debt import hp_debt_multiplier
    assert round(hp_debt_multiplier(30, 60), 4) == 4.0      # −50% от 60
    assert round(hp_debt_multiplier(500, 1000), 4) == 4.0   # −50% от 1000 → то же ×4.0
    assert round(hp_debt_multiplier(100, 1000), 4) == 1.6   # −10% от 1000 → ×1.6


def test_hp_пол_процент_от_max_hp():
    from core.debt import hp_debt_floor
    assert hp_debt_floor(60) == -30        # −50% (на 60 ≡ прежний фикс −30)
    assert hp_debt_floor(1000) == -500     # растёт с max HP (масштаб-инвариантно)
    assert hp_debt_floor(0) == 0           # защита


def test_общая_формула_ресурс_агностична():
    """_debt_multiplier — одна кривая для обоих ресурсов (energy/hp читают её по своим ручкам)."""
    from core.debt import _debt_multiplier
    assert _debt_multiplier(0, "linear", 0.25, 0.2) == 1.0
    assert _debt_multiplier(4, "linear", 0.25, 0.2) == 2.0
    assert _debt_multiplier(2, "exp", 0.25, 0.2) == 1.44
