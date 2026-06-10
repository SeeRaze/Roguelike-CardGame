# tests/test_detonations.py
# ЗАМЫКАНИЕ-ПОЗВОНОЧНИК (С58): один путь detonate(), вкус по со-элементу.
#   База: снос щита + заряды × DMG_PER_CHARGE по цели.
#   Кофе→Электролиз (AoE) · Legacy→Цикличный повтор (DoT-бурст) ·
#   Токс→Нейротоксин (стан) · Утечка→Аппаратный сбой (→энергия).
from core.players.warrior import Warrior
from core.enemies import Cultist
from core.cards.basic import create_strike
from core.DetonationRegistry import (
    detonate, SHORTCIRCUIT_THRESHOLD, DMG_PER_CHARGE,
)
from managers.CombatManager import CombatManager


def _cm(enemies=None):
    if enemies is None:
        enemies = Cultist("K", 100, 100)
    return CombatManager(Warrior(), enemies, [create_strike()])


def test_threshold_constant():
    assert SHORTCIRCUIT_THRESHOLD == 5


def test_no_charge_is_inert():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 100
    assert detonate(e, cm) == 0
    assert e.hp == 100


def test_base_strips_shield_and_bursts():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 50
    e.shield = 10
    e.shortcircuit = 3
    total = detonate(e, cm)
    # Снос щита → 0; бурст 3 × DMG_PER_CHARGE прямо в HP; заряд потрачен.
    assert e.shield == 0
    assert e.hp == 50 - 3 * DMG_PER_CHARGE
    assert e.shortcircuit == 0
    assert total == 3 * DMG_PER_CHARGE


def test_electrolysis_aoe_splash_with_coffee():
    e1 = Cultist("A", 100, 100)
    e2 = Cultist("B", 100, 100)
    cm = _cm([e1, e2])
    e1.hp = e2.hp = 100
    e1.shortcircuit = 2
    e1.coffee = 1
    detonate(e1, cm)
    # Цель: база 2×2=4. Прочие: сплэш 2×1=2. Кофе потрачен.
    assert e1.hp == 100 - 4
    assert e2.hp == 100 - 2
    assert e1.coffee == 0


def test_cyclic_repeat_burns_legacy():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 50
    e.shortcircuit = 1
    e.legacy = 3
    detonate(e, cm)
    # База 1×2=2 + Цикличный повтор 3×2=6 = 8; Legacy сожжён.
    assert e.hp == 50 - 8
    assert e.legacy == 0


def test_neurotoxin_stuns_keeps_tox():
    cm = _cm()
    e = cm.enemies[0]
    e.shortcircuit = 1
    e.tox = 2
    detonate(e, cm)
    assert e.get_status("stunned") == 1
    assert e.tox == 2          # Токс остаётся саботировать


def test_hardfault_converts_leak_to_energy():
    cm = _cm()
    e = cm.enemies[0]
    p = cm.player
    p.energy = 3
    e.shortcircuit = 1
    e.leak = 5
    detonate(e, cm)
    # Кап +3/ход: +3 энергии, leak частично сожжён (5−3=2).
    assert p.energy == 6
    assert e.leak == 2
