# tests/test_debt_combat.py
# Долговой движок — механика овердрафта в бою (§7, подзадача 2): гейт энергии в
# минус (с капом DEBT_MAX_OVERDRAFT) + гашение HP в конце хода. Флаг
# player.energy_overdraft (дефолт off) → инертно (регресс-нейтрально).
import core.debt as debt
from core.players import Warrior
from core.enemies.cultist import Cultist
from core.cards import create_strike, create_defend
from managers.CombatManager import CombatManager


def _cm(energy=0, overdraft=False):
    p = Warrior()
    cm = CombatManager(p, Cultist("Культист", 30, 30),
                       [create_strike(), create_strike(), create_defend()])
    p.energy = energy
    if overdraft:
        p.energy_overdraft = True
    return cm, p


def _strike_idx(cm):
    return next(i for i, c in enumerate(cm.deck_manager.hand) if c.cost == 1)


# ── use_energy: param allow_debt ──────────────────────────────────────────────
def test_use_energy_клампит_без_долга():
    p = Warrior(); p.energy = 1
    p.use_energy(3)                      # дефолт allow_debt=False
    assert p.energy == 0                 # клампинг на 0


def test_use_energy_уходит_в_минус_с_долгом():
    p = Warrior(); p.energy = 1
    p.use_energy(3, allow_debt=True)
    assert p.energy == -2                # овердрафт


# ── гейт розыгрыша ────────────────────────────────────────────────────────────
def test_без_флага_карта_дороже_энергии_отклонена():
    """Регресс: без овердрафта поведение прежнее — карту не сыграть в долг."""
    cm, p = _cm(energy=0, overdraft=False)
    assert cm.play_card_by_index(_strike_idx(cm)) is False
    assert p.energy == 0                 # энергия не тронута


def test_с_флагом_карта_уходит_в_долг():
    cm, p = _cm(energy=0, overdraft=True)
    assert cm.play_card_by_index(_strike_idx(cm)) is True
    assert p.energy == -1                # овердрафт на стоимость карты


def test_гард_рейл_не_пускает_глубже_пола():
    """Долг не может превысить DEBT_MAX_OVERDRAFT (амплитудный гард-рейл)."""
    cm, p = _cm(energy=-debt.DEBT_MAX_OVERDRAFT, overdraft=True)  # уже на полу
    assert cm.play_card_by_index(_strike_idx(cm)) is False        # +1 → за пол
    assert p.energy == -debt.DEBT_MAX_OVERDRAFT                   # без изменений


# ── гашение ───────────────────────────────────────────────────────────────────
def test_гашение_снимает_hp_по_проценту():
    cm, p = _cm(energy=-3, overdraft=True)
    hp0 = p.hp
    cm._settle_energy_debt()
    assert p.hp == hp0 - 3 * debt.DEBT_HP_INTEREST   # долг × процент
    assert p.energy == 0                              # долг погашен


def test_гашение_бьёт_сквозь_щит():
    cm, p = _cm(energy=-2, overdraft=True)
    p.shield = 50
    hp0 = p.hp
    cm._settle_energy_debt()
    assert p.hp == hp0 - 2 * debt.DEBT_HP_INTEREST    # щит не спасает (lose_hp)
    assert p.shield == 50
