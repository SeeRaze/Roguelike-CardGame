# tests/test_chest_data.py
# Гард пула проклятых баффов сундука (Блок 5-стретч, С65): целостность данных +
# поведение новых баффов (FP-ось / max HP). У сундуков не было тестов — заводим.
from types import SimpleNamespace
from ui.chest.data import CURSED_BUFF_POOL, generate_cursed_buffs
from core.players import Warrior


def _gm():
    gm = SimpleNamespace(player=Warrior(), player_gold=0)
    gm.player.forge_points = 0
    return gm


def test_пул_баффов_цел_и_без_протухшего_лейбла():
    assert len(CURSED_BUFF_POOL) == 8
    labels = [b[0] for b in CURSED_BUFF_POOL]
    assert len(set(labels)) == 8                 # уникальные лейблы
    assert "+3 Ярости" not in labels             # переименован в Оптимизацию (С58)
    assert "+3 Оптимизации" in labels


def test_каждый_бафф_применяется_без_ошибок():
    for name, desc, cost, apply in CURSED_BUFF_POOL:
        gm = _gm()
        apply(gm)                                # не должно падать
        assert isinstance(cost, int) and cost > 0


def test_бафф_fp_растит_forge_points():
    gm = _gm()
    _, _, _, apply = next(b for b in CURSED_BUFF_POOL if b[0] == "+8 FP")
    apply(gm)
    assert gm.player.forge_points == 8


def test_бафф_max_hp_растит_потолок_без_хила():
    gm = _gm()
    base_max, base_hp = gm.player.max_hp, gm.player.hp
    _, _, _, apply = next(b for b in CURSED_BUFF_POOL if "макс. HP" in b[0])
    apply(gm)
    assert gm.player.max_hp == base_max + 30      # потолок +30
    assert gm.player.hp == base_hp                # БЕЗ лечения (честный трейд)


def test_generate_cursed_buffs_возвращает_n():
    assert len(generate_cursed_buffs(3)) == 3
