# tests/test_elements_r2a.py
# R2a — реакции на НОВЫХ статусах (мирно сосуществуют с ХОТФИКСом):
#   Кислотный дождь (Legacy+Токс) — тики Legacy ПРОБИВАЮТ щит.
#   Гидродинамика (Кофе+Утечка)   — leak-тик добирает ещё карту.
#   Рекурсия (Legacy+Утечка)      — добор стакает Legacy; >порога → крит.
from core.Creature import Creature
from core.players.warrior import Warrior
from core.enemies import Cultist
from core.cards.basic import create_strike
from managers.CombatManager import CombatManager
from managers.combat.phases import RECURSION_THRESHOLD


def _cm(enemies=None):
    if enemies is None:
        enemies = Cultist("K", 100, 100)
    return CombatManager(Warrior(), enemies, [create_strike()])


# ─── Кислотный дождь: Legacy пробивает щит при Токсе ─────────────────────────
def test_acid_rain_legacy_pierces_shield_with_tox():
    c = Creature("враг", 50, 50)
    c.shield = 10
    c.legacy = 4
    c.tox = 2
    c.tick_statuses()
    # Пробитие: щит цел, 4 прямо в HP; Legacy −1; Токс персист.
    assert c.shield == 10
    assert c.hp == 46
    assert c.legacy == 3
    assert c.tox == 2


def test_legacy_respects_shield_without_tox():
    c = Creature("враг", 50, 50)
    c.shield = 10
    c.legacy = 4
    c.tick_statuses()
    # Без Токса — щит впитал, HP цел.
    assert c.shield == 6
    assert c.hp == 50
    assert c.legacy == 3


# ─── Гидродинамика: leak-тик добирает карту ──────────────────────────────────
def test_hydrodynamics_draws_extra_card():
    cm = _cm()
    e = cm.enemies[0]
    e.leak = 1
    e.coffee = 1
    cm.deck_manager.hand = [create_strike(), create_strike()]   # рука 2
    cm.deck_manager.draw_pile = [create_strike()]               # 1 на добор
    cm.apply_leak_on_draw()
    assert len(cm.deck_manager.hand) == 3                        # +1 от Гидродинамики


def test_no_hydrodynamics_without_coffee():
    cm = _cm()
    e = cm.enemies[0]
    e.leak = 1
    cm.deck_manager.hand = [create_strike(), create_strike()]
    cm.deck_manager.draw_pile = [create_strike()]
    cm.apply_leak_on_draw()
    assert len(cm.deck_manager.hand) == 2                        # без Кофе — без добора


# ─── Рекурсия: добор стакает Legacy; >порога → крит ──────────────────────────
def test_recursion_stacks_legacy_on_draw():
    cm = _cm()
    e = cm.enemies[0]
    e.leak = 1
    e.legacy = 3
    cm.deck_manager.hand = [create_strike()]
    cm.apply_leak_on_draw()
    assert e.legacy == 4                                         # +1 стак, ниже порога


def test_recursion_crit_above_threshold():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 100
    e.leak = 1
    e.legacy = RECURSION_THRESHOLD                # 10 → +1 = 11 > порога
    cm.deck_manager.hand = [create_strike()]      # leak урон = 1
    cm.apply_leak_on_draw()
    # leak 1 + крит (11×2=22) = 23; Legacy сожжён.
    assert e.legacy == 0
    assert e.hp == 100 - 1 - 22
