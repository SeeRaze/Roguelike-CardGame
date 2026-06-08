# tests/test_discipline.py
# Ярус-1 крючок Воина «Дисциплина» (С50): накопитель-статус растёт, когда Воин
# держит строй (начал ход со щитом), и даёт +урон. Стабильная ступень лестницы.

from core.EffectCalculator import EffectCalculator
from core.players import Warrior
from core.enemies import Cultist


class FakeCombat:
    """Минимальный combat_manager: игрок + враг + лог, без gm (реликвии не зовутся)."""
    def __init__(self):
        self.player = Warrior()
        self.enemy = Cultist("Тест", hp=200, max_hp=200)
        self.enemies = [self.enemy]
        self.log = []
        self.gm = None

    def add_log_message(self, msg):
        self.log.append(msg)

    def get_target_enemy(self):
        return self.enemy


# ─── статус в реестре ────────────────────────────────────────────────────────────

def test_discipline_в_status_registry():
    from core.StatusRegistry import STATUSES, get
    assert "discipline" in STATUSES
    data = get("discipline")
    assert data["is_stack"] is True
    assert data["is_duration"] is False


# ─── бонус урона ──────────────────────────────────────────────────────────────────

def test_дисциплина_добавляет_флат_урон():
    cm = FakeCombat()
    p = cm.player
    base = EffectCalculator.calculate_damage(p, cm.enemy, 10, None, cm, dry_run=True)
    p.discipline = 4
    boosted = EffectCalculator.calculate_damage(p, cm.enemy, 10, None, cm, dry_run=True)
    assert boosted == base + 4


def test_дисциплина_только_у_игрока():
    """Дисциплина врага НЕ усиливает его удар (гейт is_player_attack)."""
    cm = FakeCombat()
    cm.enemy.discipline = 5                       # враг как атакующий
    dmg = EffectCalculator.calculate_damage(cm.enemy, cm.player, 10, None, cm, dry_run=True)
    assert dmg == 10                              # бонус не применился


# ─── триггер «держал строй» ────────────────────────────────────────────────────────

def test_щит_на_старте_хода_даёт_дисциплину():
    cm = FakeCombat()
    p = cm.player
    p.shield = 8                                  # держал строй с прошлого хода
    p.on_turn_start_passive(cm)
    assert p.discipline == 1


def test_без_щита_дисциплина_не_растёт():
    cm = FakeCombat()
    p = cm.player
    p.shield = 0
    p.on_turn_start_passive(cm)
    assert p.discipline == 0


def test_дисциплина_копится_по_ходам():
    cm = FakeCombat()
    p = cm.player
    for _ in range(3):
        p.shield = 5                              # каждый ход держит строй
        p.on_turn_start_passive(cm)
    assert p.discipline == 3


# ─── сброс между боями ──────────────────────────────────────────────────────────────

def test_дисциплина_сбрасывается_между_боями():
    p = Warrior()
    p.discipline = 7
    p.reset_combat_statuses()
    assert p.discipline == 0
