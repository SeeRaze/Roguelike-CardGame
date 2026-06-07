# tests/test_hp_debt.py
# Долг HP (§4, С49, субстрат Берсерка «Отрицание Смерти»): HP уходит в МИНУС при флаге
# hp_overdraft → клампы Creature по _hp_floor() + множитель урона + смерть на дне долга +
# хук расплаты. Дефолт (нет флага) → пол 0 → байт-в-байт со старым поведением.
from types import SimpleNamespace

import core.debt as debt
from core.Creature import Creature
from core.EffectCalculator import EffectCalculator
from core.players import Warrior
from core.enemies.cultist import Cultist
from core.cards import create_strike, create_defend
from managers.CombatManager import CombatManager


# ── _hp_floor: пол HP ─────────────────────────────────────────────────────────
def test_пол_hp_дефолт_0():
    c = Creature("X", 30, 30)
    assert c._hp_floor() == 0                     # нет флага → старое поведение


def test_пол_hp_сдвинут_при_овердрафте():
    c = Creature("X", 30, 30)
    c.hp_overdraft = True
    assert c._hp_floor() == -debt.HP_DEBT_MAX_OVERDRAFT


# ── клампы урона уходят в минус только с флагом ───────────────────────────────
def test_take_damage_клампит_на_0_без_флага():
    c = Creature("X", 10, 10)
    c.take_damage(999)
    assert c.hp == 0                              # регресс: без овердрафта дно = 0


def test_take_damage_уходит_в_минус_с_флагом():
    c = Creature("X", 10, 10)
    c.hp_overdraft = True
    c.take_damage(999)
    assert c.hp == -debt.HP_DEBT_MAX_OVERDRAFT    # дно = пол долга, не глубже


def test_lose_hp_уходит_в_минус_с_флагом():
    c = Creature("X", 5, 5)
    c.hp_overdraft = True
    lost = c.lose_hp(999)
    assert c.hp == -debt.HP_DEBT_MAX_OVERDRAFT
    assert lost == 5 + debt.HP_DEBT_MAX_OVERDRAFT  # фактически снято до пола


def test_lose_hp_клампит_на_0_без_флага():
    c = Creature("X", 5, 5)
    assert c.lose_hp(999) == 5                    # регресс: дно 0
    assert c.hp == 0


# ── множитель урона от глубины минуса HP ──────────────────────────────────────
def _hit(player, base=10):
    target = Creature("Враг", 100, 100)
    gm = SimpleNamespace(relics=[], stats={}, rulestack=None)
    cm = SimpleNamespace(player=player, gm=gm, add_log_message=lambda _: None)
    return EffectCalculator.calculate_damage(player, target, base,
                                             game_manager=gm, combat_manager=cm)


def test_минус_hp_множит_урон():
    p = Creature("Игрок", 50, 50)
    p.hp = -2                                     # долг HP 2 → ×1.20
    assert _hit(p, 10) == 12


def test_положительный_hp_не_трогает_урон():
    p = Creature("Игрок", 50, 50)
    p.hp = 30
    assert _hit(p, 10) == 10                      # инертно


# ── смерть: выживание в минусе, гибель на дне ─────────────────────────────────
def _cm(overdraft=False):
    p = Warrior()
    cm = CombatManager(p, Cultist("Культист", 30, 30),
                       [create_strike(), create_strike(), create_defend()])
    if overdraft:
        p.hp_overdraft = True
    return cm, p


def test_выживает_в_минусе_не_на_дне():
    """HP-долг: игрок в минусе, но выше пола → НЕ умирает (долг жизни даёт множитель)."""
    cm, p = _cm(overdraft=True)
    p.hp = -3                                     # минус, но пол = -10
    assert cm.check_player_defeat() is False
    assert p.hp == -3                             # не обнулён — продолжает в долге


def test_смерть_на_дне_долга(monkeypatch):
    """На дне (hp <= пол) — смерть (как старая смерть на 0, со сдвигом пола)."""
    import managers.combat.defeat as defeat_mod
    import managers.network_manager as nm
    monkeypatch.setattr(defeat_mod.SaveManager, "record_run", lambda *a, **k: None)
    monkeypatch.setattr(defeat_mod, "send_run_record", lambda *a, **k: None)
    monkeypatch.setattr(nm, "_get_username", lambda *a, **k: "test")
    cm, p = _cm(overdraft=True)
    p.hp = -debt.HP_DEBT_MAX_OVERDRAFT           # на дне
    assert cm.check_player_defeat() is True
    assert p.hp == 0                              # обнулён на смерти


def test_смерть_на_0_без_флага():
    """Регресс: без овердрафта пол = 0 → смерть на 0, как раньше (I/O не трогаем —
    hp>0 ветка возвращает False до диска/сети)."""
    cm, p = _cm(overdraft=False)
    p.hp = 5
    assert cm.check_player_defeat() is False      # жив → ранний выход без I/O


# ── хук расплаты — сеам под Берсерка, инертен по умолчанию ─────────────────────
def test_settle_hp_debt_ноп_без_хука():
    cm, p = _cm(overdraft=True)
    p.hp = -3
    cm._settle_hp_debt()                          # нет on_hp_debt_settle → ничего
    assert p.hp == -3


def test_settle_hp_debt_зовёт_хук_класса():
    cm, p = _cm(overdraft=True)
    p.hp = -3
    called = []
    p.on_hp_debt_settle = lambda c: called.append(c)
    cm._settle_hp_debt()
    assert called == [cm]                          # сеам сработал, получил cm


def test_settle_hp_debt_ноп_в_плюсе():
    cm, p = _cm(overdraft=True)
    p.hp = 20
    p.on_hp_debt_settle = lambda c: (_ for _ in ()).throw(AssertionError("не должен"))
    cm._settle_hp_debt()                          # hp>=0 → хук не зовётся
