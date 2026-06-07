# tests/test_enemy_targeting.py
# Случайный таргетинг атак врага (этап S — Призыватель): атакующее намерение
# бьёт СЛУЧАЙНУЮ цель из {игрок + живые союзники}. Фундамент под будущий статус
# «провокация» и под призывные классы (стая поглощает часть ударов).
#
# Инвариант surgical: без союзников цель = игрок (поведение не меняется для
# классов без стаи). Дебаффы остаются на игроке.
import core.enemies.base as enemy_base
from core.enemies.base import Enemy
from core.positioning import Rank
from core.Summon import Summon


class _GM:
    """Минимальный игровой контекст для EffectCalculator (relics/stats)."""
    def __init__(self):
        self.relics = []
        self.stats = {"max_damage_dealt": 0}


class _Combat:
    """Лёгкий бой со стаей союзников для проверки таргетинга."""
    def __init__(self, player, allies=None):
        self.player  = player
        self.allies  = allies if allies is not None else []
        self.enemies = []
        self.gm      = _GM()
        self.log     = []

    def add_log_message(self, msg):
        self.log.append(msg)

    def _check_ally_death(self, ally):
        if ally.hp <= 0 and ally in self.allies:
            self.allies.remove(ally)


def _wolf(hp=12, atk=4):
    return Summon(name="Волк", hp=hp, attack_power=atk)


# ═══════════════════════════════════════════════════════════
# Атака бьёт случайную цель (игрок ИЛИ союзник)
# ═══════════════════════════════════════════════════════════

def test_атака_может_попасть_в_союзника(make_creature, monkeypatch):
    player = make_creature("Игрок", 50, 50)
    wolf   = _wolf(hp=12)
    cm     = _Combat(player, allies=[wolf])
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 8)
    # Форсируем выбор союзника.
    monkeypatch.setattr(enemy_base.random, "choice", lambda seq: wolf)
    enemy.execute_intent(player, cm)
    assert player.hp == 50            # игрок не задет
    assert wolf.hp == 4              # 12 - 8


def test_атака_может_попасть_в_игрока(make_creature, monkeypatch):
    player = make_creature("Игрок", 50, 50)
    wolf   = _wolf(hp=12)
    cm     = _Combat(player, allies=[wolf])
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 8)
    monkeypatch.setattr(enemy_base.random, "choice", lambda seq: player)
    enemy.execute_intent(player, cm)
    assert player.hp == 42            # 50 - 8
    assert wolf.hp == 12             # союзник не задет


def test_пул_целей_включает_игрока_и_живых_союзников(make_creature, monkeypatch):
    player = make_creature("Игрок", 50, 50)
    wolf   = _wolf(hp=12)
    cm     = _Combat(player, allies=[wolf])
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 5)
    captured = {}

    def _capture(seq):
        captured["pool"] = list(seq)
        return seq[0]
    monkeypatch.setattr(enemy_base.random, "choice", _capture)
    enemy.execute_intent(player, cm)
    assert player in captured["pool"]
    assert wolf in captured["pool"]
    assert len(captured["pool"]) == 2


def test_мёртвый_союзник_не_в_пуле(make_creature, monkeypatch):
    player    = make_creature("Игрок", 50, 50)
    dead_wolf = _wolf(hp=12)
    dead_wolf.hp = 0
    cm        = _Combat(player, allies=[dead_wolf])
    enemy     = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 5)
    captured = {}
    monkeypatch.setattr(enemy_base.random, "choice",
                        lambda seq: captured.setdefault("pool", list(seq))[0])
    enemy.execute_intent(player, cm)
    # Живых союзников нет → пул не строился через random (бьём игрока напрямую).
    assert player.hp == 45            # 50 - 5
    assert "pool" not in captured     # random.choice не звали (нет живых союзников)


# ═══════════════════════════════════════════════════════════
# Surgical: без союзников / без боя — цель всегда игрок
# ═══════════════════════════════════════════════════════════

def test_без_союзников_цель_игрок(make_creature):
    player = make_creature("Игрок", 50, 50)
    cm     = _Combat(player, allies=[])
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 10)
    enemy.execute_intent(player, cm)
    assert player.hp == 40


def test_без_combat_manager_цель_игрок(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 10)
    enemy.execute_intent(player, combat_manager=None)
    assert player.hp == 40


# ═══════════════════════════════════════════════════════════
# Дебафф всегда на игроке (таргетинг — только для атак)
# ═══════════════════════════════════════════════════════════

def test_дебафф_всегда_на_игроке(make_creature, monkeypatch):
    player = make_creature("Игрок", 50, 50)
    wolf   = _wolf(hp=12)
    cm     = _Combat(player, allies=[wolf])
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("debuff", 2)
    # Даже если random выбрал бы союзника — дебафф уходит игроку.
    monkeypatch.setattr(enemy_base.random, "choice", lambda seq: wolf)
    enemy.execute_intent(player, cm)
    assert player.weak == 2


# ═══════════════════════════════════════════════════════════
# Смерть союзника от атаки снимает его со стаи
# ═══════════════════════════════════════════════════════════

def test_союзник_гибнет_от_атаки_и_снимается(make_creature, monkeypatch):
    player = make_creature("Игрок", 50, 50)
    wolf   = _wolf(hp=5)
    cm     = _Combat(player, allies=[wolf])
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 8)        # больше HP волка
    monkeypatch.setattr(enemy_base.random, "choice", lambda seq: wolf)
    enemy.execute_intent(player, cm)
    assert wolf.hp <= 0
    assert wolf not in cm.allies         # снят через _check_ally_death


# ═══════════════════════════════════════════════════════════
# ПОЗИЦИОНКА §2 — полный перехват: жив фронт → урон не в тыл
# ═══════════════════════════════════════════════════════════


def test_перехват_дефолт_герой_фронт_тыл_защищён(make_creature, monkeypatch):
    # Дефолт: герой ФРОНТ, саммон ТЫЛ. Пока жив фронт — урон только в героя,
    # даже если random попытался бы выбрать союзника.
    player = make_creature("Игрок", 50, 50)
    player.rank = Rank.FRONT
    wolf   = _wolf(hp=12)
    wolf.rank = Rank.BACK
    cm     = _Combat(player, allies=[wolf])
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 8)
    captured = {}
    monkeypatch.setattr(enemy_base.random, "choice",
                        lambda seq: captured.setdefault("pool", list(seq))[0])
    enemy.execute_intent(player, cm)
    assert player.hp == 42               # 50 - 8, герой принял удар
    assert wolf.hp == 12                 # тыл защищён
    assert "pool" not in captured        # единственный кандидат → без random


def test_перехват_зеркало_саммоны_фронт_герой_тыл(make_creature, monkeypatch):
    # Зеркало: саммон ФРОНТ танкует, герой ТЫЛ защищён.
    player = make_creature("Игрок", 50, 50)
    player.rank = Rank.BACK
    wolf   = _wolf(hp=12)
    wolf.rank = Rank.FRONT
    cm     = _Combat(player, allies=[wolf])
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 8)
    enemy.execute_intent(player, cm)
    assert player.hp == 50               # тыл защищён
    assert wolf.hp == 4                  # 12 - 8, фронт принял


def test_перехват_фронт_пал_открывается_тыл(make_creature):
    # Фронт-саммон мёртв → урон доходит до героя в тылу.
    player = make_creature("Игрок", 50, 50)
    player.rank = Rank.BACK
    dead   = _wolf(hp=12)
    dead.hp = 0
    dead.rank = Rank.FRONT
    cm     = _Combat(player, allies=[dead])
    enemy  = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 7)
    enemy.execute_intent(player, cm)
    assert player.hp == 43               # 50 - 7, тыл открылся


def test_перехват_два_фронта_пул_только_фронт(make_creature, monkeypatch):
    # Зеркало 2/1: двое саммонов ФРОНТ → пул выбора = только они, герой (ТЫЛ) вне пула.
    player = make_creature("Игрок", 50, 50)
    player.rank = Rank.BACK
    w1 = _wolf(hp=12)
    w1.rank = Rank.FRONT
    w2 = _wolf(hp=12)
    w2.rank = Rank.FRONT
    cm = _Combat(player, allies=[w1, w2])
    enemy = Enemy("Враг", 30, 30)
    enemy.set_intent("attack", 5)
    captured = {}
    monkeypatch.setattr(enemy_base.random, "choice",
                        lambda seq: captured.setdefault("pool", list(seq))[0])
    enemy.execute_intent(player, cm)
    assert w1 in captured["pool"] and w2 in captured["pool"]
    assert player not in captured["pool"]
    assert len(captured["pool"]) == 2
