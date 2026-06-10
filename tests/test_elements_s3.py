# tests/test_elements_s3.py
# Этап S3 айти-передела стихий: движок «Утечка памяти» + gain_energy.
#   leak — на акт добора враг получает leak × размер руки урона (уважает щит, персист).
from core.players.warrior import Warrior
from core.enemies import Cultist
from core.cards.basic import create_strike
from managers.CombatManager import CombatManager


def _cm():
    return CombatManager(Warrior(), Cultist("K", 50, 50), [create_strike()])


def _set_hand(cm, n):
    cm.deck_manager.hand = [create_strike() for _ in range(n)]


# ─── leak: урон = стаки × размер руки ────────────────────────────────────────
def test_leak_damage_equals_stacks_times_hand():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 50
    e.shield = 0
    e.leak = 2
    _set_hand(cm, 3)            # рука 3 → 2 × 3 = 6 урона
    cm.apply_leak_on_draw()
    assert e.hp == 44


def test_leak_respects_shield():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 50
    e.shield = 4
    e.leak = 2
    _set_hand(cm, 3)            # 6 урона: щит 4 впитал, 2 в HP
    cm.apply_leak_on_draw()
    assert e.shield == 0
    assert e.hp == 48


def test_leak_persists_no_decay():
    cm = _cm()
    e = cm.enemies[0]
    e.leak = 1
    _set_hand(cm, 5)
    cm.apply_leak_on_draw()
    assert e.leak == 1          # движок: не убывает (бьёт каждый добор)


def test_leak_zero_no_damage():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 50
    e.leak = 0
    _set_hand(cm, 5)
    cm.apply_leak_on_draw()
    assert e.hp == 50


def test_leak_empty_hand_no_damage():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 50
    e.leak = 3
    cm.deck_manager.hand = []   # пустая рука → 3 × 0 = 0
    cm.apply_leak_on_draw()
    assert e.hp == 50


# ─── gain_energy: рамп/бурст ─────────────────────────────────────────────────
def test_gain_energy_adds():
    p = Warrior()
    p.energy = p.max_energy     # 3
    p.gain_energy(2)
    assert p.energy == 5        # допускает выход за max (бурст)


def test_gain_energy_ignores_nonpositive():
    p = Warrior()
    p.energy = 3
    p.gain_energy(0)
    p.gain_energy(-5)
    assert p.energy == 3
