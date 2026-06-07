# tests/test_tactical_move.py
# Позиционка §5a — Тактический Манёвр: эффект [Tactical_Move] переворачивает строй,
# живое включение позиционки, рантайм formation_mirrored (тоггл/сброс между боями).
from core.players import Warrior, Summoner
from core.enemies.cultist import Cultist
from core.Summon import Summon
from core.cards import create_strike, create_defend, create_tactical_reposition
from core.cards.base import TacticalMoveEffect
from core.cards.catalog import GENERIC_FACTORIES
from core.positioning import Rank
from managers.CombatManager import CombatManager


def _deck():
    return [create_strike(), create_strike(), create_defend()]


def _live_cm(player):
    """Живой бой с ВКЛЮЧЁННОЙ позиционкой (как ставит GameManager)."""
    player.positioning_enabled = True
    return CombatManager(player, Cultist("Культист", 30, 30), _deck(), game_manager=None)


# ═══════════════════════════════════════════════════════════
# Строй на старте боя — по классовому дефолту
# ═══════════════════════════════════════════════════════════

def test_живой_строй_дефолт_воин_во_фронте():
    cm = _live_cm(Warrior())
    assert cm.player.rank == Rank.FRONT
    assert cm.player.formation_mirrored is False


def test_живой_строй_зеркало_призыватель_в_тылу():
    cm = _live_cm(Summoner())
    assert cm.player.rank == Rank.BACK
    assert cm.player.formation_mirrored is True


def test_зеркало_саммон_встаёт_во_фронт():
    cm = _live_cm(Summoner())
    wolf = Summon(name="Волк", hp=12, attack_power=4)
    cm.allies.append(wolf)
    cm._apply_positioning()
    assert wolf.rank == Rank.FRONT       # саммоны танкуют в зеркале
    assert cm.player.rank == Rank.BACK


# ═══════════════════════════════════════════════════════════
# flip_formation — атомарный переворот
# ═══════════════════════════════════════════════════════════

def test_flip_formation_переворачивает_строй():
    cm = _live_cm(Warrior())
    assert cm.player.rank == Rank.FRONT
    cm.flip_formation()
    assert cm.player.formation_mirrored is True
    assert cm.player.rank == Rank.BACK
    cm.flip_formation()
    assert cm.player.rank == Rank.FRONT   # вернулось


# ═══════════════════════════════════════════════════════════
# Карта-носитель [Tactical_Move]
# ═══════════════════════════════════════════════════════════

def test_карта_перестроение_триггерит_манёвр():
    cm = _live_cm(Warrior())
    card = create_tactical_reposition()
    card.apply(cm.player, cm.enemies[0], cm)
    assert cm.player.rank == Rank.BACK    # фронт↔тыл
    assert any("МАНЁВР" in m for m in cm.combat_log)


def test_карта_перестроение_вне_generic_пула():
    # baseline-безопасность: бот не должен драфтить и тратить ход на флип.
    names = [f.__name__ for f in GENERIC_FACTORIES]
    assert "create_tactical_reposition" not in names
    card = create_tactical_reposition()
    assert any(isinstance(e, TacticalMoveEffect) for e in card.effects)


# ═══════════════════════════════════════════════════════════
# Сброс строя между боями + гард позиционки
# ═══════════════════════════════════════════════════════════

def test_флип_не_переносится_в_следующий_бой():
    player = Warrior()
    cm1 = _live_cm(player)
    cm1.flip_formation()
    assert player.formation_mirrored is True
    # Новый бой тем же игроком — конструктор сбрасывает строй к классовому дефолту.
    CombatManager(player, Cultist("К", 30, 30), _deck(), game_manager=None)
    assert player.formation_mirrored is False
    assert player.rank == Rank.FRONT


def test_позиционка_off_манёвр_no_op():
    player = Warrior()  # без positioning_enabled (как сим baseline)
    cm = CombatManager(player, Cultist("К", 30, 30), _deck(), game_manager=None)
    assert player.rank is None
    cm.flip_formation()
    assert player.rank is None            # гард: без флага ничего не делает
