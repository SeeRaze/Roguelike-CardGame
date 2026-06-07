# tests/test_positioning_sim.py
# Позиционка §4 — сим-нативность: гейт-хелпер _apply_positioning (opt-in флагом),
# зеркальный класс Призывателя, смоук opt-in в runner. baseline зелёный (off → no-op).
from types import SimpleNamespace

from core.Creature import Creature
from core.positioning import Rank
from managers.CombatManager import CombatManager


def _c(name, hp=10, rank=None):
    cr = Creature(name=name, hp=hp, max_hp=10)
    cr.rank = rank
    return cr


# ═══════════════════════════════════════════════════════════
# Гейт-хелпер _apply_positioning (вызывается на stub — только player/allies)
# ═══════════════════════════════════════════════════════════

def test_apply_positioning_без_флага_no_op():
    hero = _c("hero")
    ally = _c("ally")
    stub = SimpleNamespace(player=hero, allies=[ally])  # нет positioning_enabled
    CombatManager._apply_positioning(stub)
    assert hero.rank is None and ally.rank is None       # ранги не тронуты


def test_apply_positioning_дефолт_герой_фронт():
    hero = _c("hero")
    hero.positioning_enabled = True                      # mirrored_layout по дефолту нет → False
    a1, a2 = _c("a1"), _c("a2")
    stub = SimpleNamespace(player=hero, allies=[a1, a2])
    CombatManager._apply_positioning(stub)
    assert hero.rank == Rank.FRONT
    assert a1.rank == Rank.BACK and a2.rank == Rank.BACK


def test_apply_positioning_зеркало_саммоны_фронт():
    hero = _c("hero")
    hero.positioning_enabled = True
    hero.mirrored_layout = True                          # инстанс-флаг зеркала
    a1, a2 = _c("a1"), _c("a2")
    stub = SimpleNamespace(player=hero, allies=[a1, a2])
    CombatManager._apply_positioning(stub)
    assert hero.rank == Rank.BACK
    assert a1.rank == Rank.FRONT and a2.rank == Rank.FRONT


def test_apply_positioning_переставляет_свежих_саммонов():
    # Идемпотентность: новый союзник, появившийся между вызовами, получает ранг.
    hero = _c("hero")
    hero.positioning_enabled = True
    stub = SimpleNamespace(player=hero, allies=[])
    CombatManager._apply_positioning(stub)
    assert hero.rank == Rank.FRONT
    new_ally = _c("новый")
    stub.allies.append(new_ally)
    CombatManager._apply_positioning(stub)
    assert new_ally.rank == Rank.BACK                    # свежий саммон расставлен


# ═══════════════════════════════════════════════════════════
# Зеркальный класс Призывателя
# ═══════════════════════════════════════════════════════════

def test_призыватель_зеркальный_класс():
    from core.players.summoner import Summoner
    assert Summoner.mirrored_layout is True


def test_прочие_классы_не_зеркальные():
    from core.players.warrior import Warrior
    from core.players.mage import Mage
    assert Warrior.mirrored_layout is False
    assert Mage.mirrored_layout is False


# ═══════════════════════════════════════════════════════════
# Смоук: opt-in в runner не падает и доходит
# ═══════════════════════════════════════════════════════════

def test_runner_positioning_opt_in_смоук():
    from core.players.summoner import Summoner
    from managers.balance.runner import run_single_run
    import random
    random.seed(99)
    res = run_single_run(Summoner, max_floor=5, positioning=True)
    assert "death_floor" in res and "hp_by_floor" in res


# ═══════════════════════════════════════════════════════════
# §10 — сим-нативность ПЕРЕХВАТА ВРАГА: BotCombatManager (наследует
# _init_positioning) ранжирует врагов; авто-таргет бота идёт во фронт.
# ═══════════════════════════════════════════════════════════

def _bot_cm(positioning):
    from core.players.warrior import Warrior
    from core.enemies.cultist import Cultist
    from core.cards import create_strike
    from managers.balance.bot import BotCombatManager
    player = Warrior()
    if positioning:
        player.positioning_enabled = True
    enemies = [Cultist(f"К{i}", 30, 30) for i in range(3)]
    cm = BotCombatManager(player, enemies, [create_strike()])
    return cm, enemies


def test_sim_враги_ранжируются_в_боте():
    cm, es = _bot_cm(positioning=True)
    assert [e.rank for e in es] == [Rank.FRONT, Rank.FRONT, Rank.BACK]


def test_sim_бот_автоцель_во_фронт():
    cm, es = _bot_cm(positioning=True)
    assert cm.get_target_enemy() in (es[0], es[1])    # тыл недостижим
    es[0].hp = 0
    es[1].hp = 0
    assert cm.get_target_enemy() is es[2]             # фронт пал → тыл открыт


def test_sim_off_враги_без_рангов_baseline():
    cm, es = _bot_cm(positioning=False)
    assert all(e.rank is None for e in es)
    assert cm.get_target_enemy() is es[0]             # первый живой, как раньше

