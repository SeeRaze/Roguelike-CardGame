# tests/test_instability.py
# Ярус-1 крючок Мага «Нестабильность» (С50): на пороге Мастерства бонус усиливается
# (перегруз мощи), ценой глитч-урона в начале хода. Ступень «Гни» лестницы.

from core.EffectCalculator import EffectCalculator
from core.players import Mage
from core.players.mage import INSTABILITY_HP_COST
from core.enemies import Cultist


class FakeCombat:
    def __init__(self):
        self.player = Mage()
        self.enemy = Cultist("Тест", hp=200, max_hp=200)
        self.enemies = [self.enemy]
        self.log = []
        self.gm = None

    def add_log_message(self, msg):
        self.log.append(msg)

    def get_target_enemy(self):
        return self.enemy


_THR = EffectCalculator.MASTERY_INSTABILITY_THRESHOLD
_MULT = EffectCalculator.MASTERY_INSTABILITY_MULT


# ─── амплификация Мастерства на пороге ──────────────────────────────────────────────

def test_ниже_порога_мастерство_флатом():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR - 1                              # перегруза нет
    dmg = EffectCalculator.calculate_damage(p, cm.enemy, 10, None, cm, dry_run=True)
    assert dmg == 10 + (_THR - 1)                     # обычный флат


def test_на_пороге_мастерство_усиливается():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR                                  # перегруз включается
    dmg = EffectCalculator.calculate_damage(p, cm.enemy, 10, None, cm, dry_run=True)
    assert dmg == 10 + int(_THR * _MULT)              # ×MULT


def test_перегруз_растёт_с_мастерством():
    cm = FakeCombat()
    p = cm.player
    p.mastery = 10
    dmg = EffectCalculator.calculate_damage(p, cm.enemy, 10, None, cm, dry_run=True)
    assert dmg == 10 + int(10 * _MULT)                # 15 при mult=1.5


# ─── глитч-цена ──────────────────────────────────────────────────────────────────────

def test_перегруз_искрит_теряет_hp_в_начале_хода():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR
    hp0 = p.hp
    p.on_turn_start_passive(cm)
    assert p.hp == hp0 - INSTABILITY_HP_COST


def test_ниже_порога_не_искрит():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR - 1
    hp0 = p.hp
    p.on_turn_start_passive(cm)
    assert p.hp == hp0                                # цены нет


def test_глитч_идёт_сквозь_щит():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR
    p.shield = 50
    hp0 = p.hp
    p.on_turn_start_passive(cm)
    assert p.shield == 50                             # щит не тронут
    assert p.hp == hp0 - INSTABILITY_HP_COST          # урон прямо в HP
