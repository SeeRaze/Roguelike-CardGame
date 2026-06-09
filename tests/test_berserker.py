# tests/test_berserker.py
# Передел Берсерка «Отрицание Смерти» (этап 1) на долговом фундаменте (§4):
# hp_overdraft + строгая смерть + пик |HP|→FP + «Кровавая ярость» через lose_hp.
import core.debt as debt
from core.players import Berserker
from core.enemies.cultist import Cultist
from core.cards import create_strike
from core.EffectCalculator import EffectCalculator
from managers.CombatManager import CombatManager


def _cm(enemy_hp=999):
    p = Berserker()
    cm = CombatManager(p, Cultist("Враг", enemy_hp, enemy_hp), [create_strike()])
    return cm, p


def test_берсерк_включает_hp_овердрафт():
    p = Berserker()
    assert p.hp_overdraft is True
    assert p._hp_floor() == debt.hp_debt_floor(p.max_hp)  # пол = −50% max HP (масштаб-инвар.)


# ── строгая расплата ──────────────────────────────────────────────────────────
def test_строгая_смерть_в_минусе_без_победы():
    cm, p = _cm()                     # враг жив
    p.hp = -3
    p.on_hp_debt_settle(cm)
    assert p.hp == p._hp_floor()      # форсирована пол-смерть (бой не выигран)


def test_нет_смерти_если_враги_мертвы():
    cm, p = _cm()
    for e in cm.enemies:
        e.hp = 0
    p.hp = -3
    p.on_hp_debt_settle(cm)
    assert p.hp == -3                 # победа обрабатывается on_combat_won, не здесь


# ── пик |HP|→FP ───────────────────────────────────────────────────────────────
def test_пик_конвертирует_минус_в_fp():
    cm, p = _cm()
    fp0 = p.forge_points
    p.hp = -7
    p.on_combat_won(cm)
    assert p.forge_points == fp0 + 7
    assert p.hp == 1                  # выжил «в коме»


def test_пик_ноп_в_плюсе():
    cm, p = _cm()
    fp0 = p.forge_points
    p.hp = 20
    p.on_combat_won(cm)
    assert p.forge_points == fp0 and p.hp == 20


# ── «Безумие»: карты за 0 энергии ценой HP (проактивный нырок) ────────────────
def test_безумие_ставит_флаг_и_сбрасывается_за_ход():
    cm, p = _cm()
    assert p.active_ability.activate(cm) is True
    assert p.madness_active is True
    assert p.active_ability.activate(cm) is False   # уже в безумии — повтор не активирует
    cm.start_turn_phase()
    assert p.madness_active is False                 # длится один ход


def test_безумие_карта_берёт_hp_не_энергию():
    cm, p = _cm()
    p.active_ability.activate(cm)
    idx = next(i for i, c in enumerate(cm.deck_manager.hand)
               if getattr(c, 'temp_cost', c.cost) >= 1)
    card = cm.deck_manager.hand[idx]
    cost = getattr(card, 'temp_cost', card.cost)
    hp0, e0 = p.hp, p.energy
    cm.play_card_by_index(idx)
    assert p.energy == e0                            # энергия НЕ тронута
    assert p.hp == hp0 - cost * p.madness_hp_per_cost  # HP-цена (стоимость × ставка)


# ── множитель урона от минуса (foundation) ────────────────────────────────────
def test_множитель_от_минуса_в_бою():
    cm, p = _cm()
    p.hp = -5                         # долг 5 от 60 → ×1.5 (доля 5/60, масштаб-инвар.)
    dmg = EffectCalculator.calculate_damage(p, cm.enemies[0], 10,
                                            game_manager=cm.gm, combat_manager=cm)
    assert dmg == 15
