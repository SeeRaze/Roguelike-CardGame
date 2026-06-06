# tests/test_relics.py
# Проверяем реликвии: каждая срабатывает на своём хуке и даёт нужный эффект.
from types import SimpleNamespace
from core.players import Warrior
from core.relics import (
    ALL_RELICS,
    ФлаконСЖелчью, ЗасохшийКлевер, ЗаточенныйОсколок, ПроклятаяКорона,
    СтараяПиявка, ШипастаяБроня, ОкровавленныйШприц, СвинцовыйНабалдашник,
)


def test_в_пуле_22_уникальные_реликвии():
    assert len(ALL_RELICS) == 22
    имена = [r().name for r in ALL_RELICS]
    assert len(set(имена)) == 22


def test_флакон_с_желчью_травит_врага_в_начале_боя(make_combat):
    cm = make_combat()
    ФлаконСЖелчью().on_combat_start(cm)
    assert cm.enemy.poison == 3


def test_засохший_клевер_даёт_регенерацию(make_combat):
    cm = make_combat()
    ЗасохшийКлевер().on_combat_start(cm)
    assert cm.player.regen == 3


def test_заточенный_осколок_усиливает_первую_атаку(make_combat):
    cm = make_combat()
    relic = ЗаточенныйОсколок()
    relic.on_combat_start(cm)
    assert relic.on_damage_calculated(10, is_player_attack=True) == 13   # первая +3
    assert relic.on_damage_calculated(10, is_player_attack=True) == 10   # дальше без бонуса


def test_проклятая_корона_удваивает_урон_игрока():
    relic = ПроклятаяКорона()
    assert relic.on_damage_calculated(10, is_player_attack=True) == 20
    assert relic.on_damage_calculated(10, is_player_attack=False) == 10


def test_старая_пиявка_добавляет_к_хилу():
    c = SimpleNamespace(hp=40, max_hp=50)
    СтараяПиявка().on_heal(5, c)
    assert c.hp == 42           # бонус +2 (ограничен нехваткой HP)


def test_шипастая_броня_вешает_кровотечение_при_получении_щита(make_combat):
    cm = make_combat()
    ШипастаяБроня().on_shield_gained(5, cm.player, cm)
    assert cm.enemy.bleed == 1


def test_окровавленный_шприц_на_карте_изгнания(make_combat):
    cm = make_combat(player=Warrior())
    cm.player.energy = 0
    карта = SimpleNamespace(exile=True)
    ОкровавленныйШприц().on_card_played(карта, cm)
    assert cm.player.energy == 1
    assert cm.enemy.poison == 2


def test_свинцовый_набалдашник_слабит_первой_атакой(make_combat):
    cm = make_combat()
    relic = СвинцовыйНабалдашник()
    атака = SimpleNamespace(card_type="attack")
    relic.on_card_played(атака, cm)
    assert cm.enemy.weak == 1
    # Вторая атака в том же ходу слабость уже не накладывает.
    relic.on_card_played(атака, cm)
    assert cm.enemy.weak == 1
