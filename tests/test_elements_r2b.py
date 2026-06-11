# tests/test_elements_r2b.py
# R2b — со-присутственные реакции саботажа (нужны новые примитивы):
#   Дилюция (Кофе+Токс)     — враг не может спец-намерения (debuff/heal).
#   Crash Reboot (Утечка+Токс) — снос щита+баффов + блок восстановления (heal_block).
from core.Creature import Creature
from core.players.warrior import Warrior
from core.enemies import Cultist
from core.cards.basic import create_strike
from managers.CombatManager import CombatManager
from managers.combat.phases import CRASH_REBOOT_TURNS


def _cm(enemies=None):
    if enemies is None:
        enemies = Cultist("K", 100, 100)
    return CombatManager(Warrior(), enemies, [create_strike()])


# ─── Дилюция: спец-намерения обезврежены ─────────────────────────────────────
def test_dilution_neutralizes_debuff_intent():
    cm = _cm()
    e = cm.enemies[0]
    p = cm.player
    p.tox = 0
    e.coffee = 1
    e.tox = 1
    e.set_intent("debuff", 3)
    e.execute_intent(p, cm)
    assert p.tox == 0          # спец-намерение (debuff) обезврежено


def test_dilution_allows_basic_attack():
    cm = _cm()
    e = cm.enemies[0]
    p = cm.player
    p.hp = 50
    p.shield = 0
    e.coffee = 1
    e.tox = 1
    e.set_intent("attack", 6)
    e.execute_intent(p, cm)
    assert p.hp < 50            # базовая атака проходит


def test_no_dilution_without_both_elements():
    cm = _cm()
    e = cm.enemies[0]
    p = cm.player
    p.tox = 0
    e.coffee = 1                # только Кофе, без Токса
    e.set_intent("debuff", 3)
    e.execute_intent(p, cm)
    assert p.tox == 3          # спец-намерение проходит


# ─── Crash Reboot: снос баффов/щита + блок восстановления ─────────────────────
def test_crash_reboot_strips_and_blocks():
    cm = _cm()
    e = cm.enemies[0]
    e.shield = 10
    e.optimize = 5
    e.healthcheck = 4
    e.leak = 1
    e.tox = 1
    cm.apply_copresence_reactions()
    assert e.shield == 0
    assert e.optimize == 0
    assert e.healthcheck == 0
    assert e.get_status("heal_block") == CRASH_REBOOT_TURNS


def test_no_crash_reboot_without_both():
    cm = _cm()
    e = cm.enemies[0]
    e.shield = 10
    e.tox = 1                   # только Токс, без Утечки
    cm.apply_copresence_reactions()
    assert e.shield == 10       # не сработало


# ─── heal_block: блокирует восстановление ────────────────────────────────────
def test_heal_block_suppresses_healing():
    c = Creature("враг", 30, 100)
    c.set_status("heal_block", 1)
    healed = c.heal(20)
    assert healed == 0
    assert c.hp == 30


def test_heal_works_without_block():
    c = Creature("враг", 30, 100)
    healed = c.heal(20)
    assert healed == 20
    assert c.hp == 50
