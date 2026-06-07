# tests/test_enemy_intercept.py
# Позиционка v2 — §8: ВРАГИ НА СЕТКЕ + симметричный перехват игрок→враг.
# Зеркало v1: пока жив ФРОНТ врага, одиночная атака игрока не доходит до тыла.
# Гейт opt-in (player.positioning_enabled) → без флага всё как раньше (baseline).
from core.players import Warrior
from core.enemies.cultist import Cultist
from core.cards import create_strike, create_defend
from core.positioning import Rank
from managers.CombatManager import CombatManager


def _deck():
    return [create_strike(), create_strike(), create_defend()]


def _cm(enemies, positioning=False):
    player = Warrior()
    if positioning:
        player.positioning_enabled = True
    return CombatManager(player, list(enemies), _deck())


def _enemies(n):
    return [Cultist(f"Культист{i}", 30, 30) for i in range(n)]


# ═══════════════════════════════════════════════════════════
# Позиционка OFF → байт-в-байт как раньше (baseline зелёный)
# ═══════════════════════════════════════════════════════════

def test_off_враги_без_рангов():
    es = _enemies(3)
    _cm(es, positioning=False)
    assert all(e.rank is None for e in es)


def test_off_get_target_первый_живой():
    es = _enemies(3)
    cm = _cm(es, positioning=False)
    assert cm.get_target_enemy() is es[0]
    es[0].hp = 0
    assert cm.get_target_enemy() is es[1]   # первый живой, как раньше


# ═══════════════════════════════════════════════════════════
# Позиционка ON → враги расставлены, перехват работает
# ═══════════════════════════════════════════════════════════

def test_on_враги_получили_ранги():
    es = _enemies(3)
    _cm(es, positioning=True)
    # 3 врага → 2 фронт / 1 тыл (assign_enemy_ranks).
    assert [e.rank for e in es] == [Rank.FRONT, Rank.FRONT, Rank.BACK]


def test_on_авто_цель_только_фронт():
    es = _enemies(3)
    cm = _cm(es, positioning=True)
    assert cm.get_target_enemy() in (es[0], es[1])   # тыл es[2] недостижим


def test_on_фронт_пал_открывается_тыл():
    es = _enemies(3)
    cm = _cm(es, positioning=True)
    es[0].hp = 0
    es[1].hp = 0
    assert cm.get_target_enemy() is es[2]            # тыл открылся


def test_on_явная_цель_в_тыл_снапается_на_фронт():
    es = _enemies(3)
    cm = _cm(es, positioning=True)
    back_enemy = es[2]                                # прикрыт живым фронтом
    resolved = cm._resolve_attack_target(back_enemy)
    assert resolved in (es[0], es[1])                # снап на фронт
    assert resolved is not back_enemy


def test_on_явная_цель_во_фронт_не_трогается():
    es = _enemies(3)
    cm = _cm(es, positioning=True)
    front_enemy = es[0]
    assert cm._resolve_attack_target(front_enemy) is front_enemy


def test_on_удар_картой_не_проходит_в_тыл():
    # Полный путь: одиночная атака с явной целью в тыл бьёт фронт, тыл цел.
    es = _enemies(3)
    cm = _cm(es, positioning=True)
    back_hp_before = es[2].hp
    # Кладём «Удар» в руку и играем по тыловой цели.
    cm.deck_manager.hand = [create_strike()]
    cm.player.energy = 3
    cm.play_card_by_index(0, target=es[2])
    assert es[2].hp == back_hp_before                # тыл не задет
    assert es[0].hp < 30 or es[1].hp < 30           # фронт принял урон
