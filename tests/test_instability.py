# tests/test_instability.py
# Ярус-1 крючок Мага «Нестабильность» (С50): на пороге Мастерства бонус усиливается
# (перегруз мощи), ценой глитч-урона в начале хода. Ступень «Гни» лестницы.

from core.EffectCalculator import EffectCalculator
from core.players import Mage
from core.players.mage import instability_cost, INSTABILITY_BASE_PCT
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
_MBASE = EffectCalculator.INSTABILITY_MULT_BASE
_MPER = EffectCalculator.INSTABILITY_MULT_PER_OVER


def _inst_mult(mastery):
    """Ожидаемый эскалирующий множитель перегруза (шаг 4c)."""
    over = mastery - _THR
    return 1.0 + _MBASE + _MPER * over


# ─── Мастерство: флат-аддитив + эскалирующий множитель перегруза ─────────────────────

def test_ниже_порога_мастерство_флатом():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR - 1                              # перегруза нет → только флат
    dmg = EffectCalculator.calculate_damage(p, cm.enemy, 10, None, cm, dry_run=True)
    assert dmg == 10 + (_THR - 1)                     # обычный флат, множителя нет


def test_на_пороге_включается_множитель():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR                                  # перегруз включается
    dmg = EffectCalculator.calculate_damage(p, cm.enemy, 10, None, cm, dry_run=True)
    # флат +mastery, затем ×множитель перегруза (шаг 4c)
    assert dmg == int((10 + _THR) * _inst_mult(_THR))


def test_множитель_перегруза_растёт_с_мастерством():
    cm = FakeCombat()
    p = cm.player
    shallow = _inst_mult(_THR)
    deep = _inst_mult(_THR + 10)
    assert deep > shallow                             # множитель эскалирует с глубиной
    p.mastery = _THR + 10
    dmg = EffectCalculator.calculate_damage(p, cm.enemy, 10, None, cm, dry_run=True)
    assert dmg == int((10 + (_THR + 10)) * deep)


# ─── глитч-цена (С56: % от max HP, эскалирует с глубиной Мастерства) ───────────────────

def test_перегруз_искрит_теряет_hp_в_начале_хода():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR
    hp0 = p.hp
    p.on_turn_start_passive(cm)
    assert p.hp == hp0 - instability_cost(p.max_hp, _THR)   # base% на пороге
    assert instability_cost(p.max_hp, _THR) > 0             # цена реальна


def test_ниже_порога_не_искрит():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR - 1
    hp0 = p.hp
    p.on_turn_start_passive(cm)
    assert p.hp == hp0                                # цены нет
    assert instability_cost(p.max_hp, _THR - 1) == 0


def test_цена_эскалирует_с_глубиной_мастерства():
    cm = FakeCombat()
    p = cm.player
    shallow = instability_cost(p.max_hp, _THR)        # на пороге
    deep = instability_cost(p.max_hp, _THR + 10)      # глубже гнём
    assert deep > shallow                             # чем дальше — тем больнее


def test_цена_масштабируется_с_max_hp():
    # %-механика: на «прокачанном» max HP цена в АБСОЛЮТЕ больше (инвариантна в %).
    small = instability_cost(70, _THR)
    big = instability_cost(700, _THR)
    assert small == int(70 * INSTABILITY_BASE_PCT)    # ровно base% на пороге
    assert big == int(700 * INSTABILITY_BASE_PCT)     # тот же % от большего max HP
    assert big > small                                # абсолют растёт с max HP


def test_глитч_идёт_сквозь_щит():
    cm = FakeCombat()
    p = cm.player
    p.mastery = _THR
    p.shield = 50
    hp0 = p.hp
    p.on_turn_start_passive(cm)
    assert p.shield == 50                             # щит не тронут
    assert p.hp == hp0 - instability_cost(p.max_hp, _THR)   # урон прямо в HP
