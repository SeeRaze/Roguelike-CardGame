# tests/test_creature_statuses.py
# Проверяем существо (Creature): получение урона, щит, шипы, вампиризм, кровотечение
# и «тик» статусов в конце хода (яд/горение/реген/спад временных эффектов).
from core.Creature import Creature
from core.relics import ГнилойКлык


def test_щит_поглощает_урон_до_hp():
    c = Creature("Цель", 50, 50)
    c.shield = 5
    c.take_damage(3)            # 3 < 5 щита
    assert c.shield == 2 and c.hp == 50


def test_урон_пробивает_щит_и_бьёт_по_hp():
    c = Creature("Цель", 50, 50)
    c.shield = 5
    c.take_damage(8)            # 5 в щит, 3 в HP
    assert c.shield == 0 and c.hp == 47


def test_hp_не_уходит_ниже_нуля():
    c = Creature("Цель", 5, 50)
    c.take_damage(100)
    assert c.hp == 0


def test_шипы_отражают_урон_в_атакующего():
    target = Creature("Цель", 50, 50)
    attacker = Creature("Враг", 50, 50)
    target.thorns = 2
    target.take_damage(5, attacker=attacker)
    assert attacker.hp == 48    # 2 урона отражено шипами


def test_вампиризм_лечит_атакующего_и_гаснет_втрое():
    target = Creature("Цель", 50, 50)
    attacker = Creature("Вампир", 40, 50)
    attacker.vampire = 4
    target.take_damage(10, attacker=attacker)
    # хил = max(1, 10*2//5) = 4 -> 40 + 4 = 44; вампиризм 4 -> 4//3 = 1
    assert attacker.hp == 44
    assert attacker.vampire == 1


def test_кровотечение_наносит_доп_урон_при_получении_удара():
    c = Creature("Цель", 50, 50)
    c.bleed = 3
    c.take_damage(5)            # 5 обычного + 3 от кровотечения
    assert c.hp == 42


def test_тик_яда_наносит_урон_и_уменьшает_стак():
    c = Creature("Цель", 50, 50)
    c.poison = 3
    c.tick_statuses()
    assert c.hp == 47 and c.poison == 2


def test_тик_горения_наносит_три_урона():
    c = Creature("Цель", 50, 50)
    c.ignited = 2
    c.tick_statuses()
    assert c.hp == 47 and c.ignited == 1


def test_тик_регенерации_лечит():
    c = Creature("Цель", 40, 50)
    c.regen = 2
    c.tick_statuses()
    assert c.hp == 42 and c.regen == 1


def test_тик_регенерации_ограничен_потолком_за_ход():
    c = Creature("Цель", 10, 100)
    c.regen = 20                       # стак выше потолка
    c.tick_statuses()
    # лечение срезано до REGEN_HEAL_CAP_PER_TURN, стак убывает на 1
    assert c.hp == 10 + Creature.REGEN_HEAL_CAP_PER_TURN
    assert c.regen == 19


def test_временные_статусы_спадают_на_один():
    c = Creature("Цель", 50, 50)
    c.vulnerable = 2
    c.weak = 2
    c.wet = 2
    c.tick_statuses()
    assert c.vulnerable == 1 and c.weak == 1 and c.wet == 1


def test_кровотечение_сбрасывается_в_ноль_без_гнилого_клыка():
    c = Creature("Цель", 50, 50)
    c.bleed = 4
    c.tick_statuses()           # без реликвии -> обнуляется
    assert c.bleed == 0


def test_гнилой_клык_уменьшает_кровотечение_вдвое(make_combat):
    c = Creature("Цель", 50, 50)
    c.bleed = 4
    cm = make_combat(enemy=c, relics=[ГнилойКлык()])
    c.tick_statuses(cm)         # с «Гнилым Клыком» -> делится пополам
    assert c.bleed == 2


def test_магический_барьер_блокирует_стихию_только_на_враге(make_combat):
    cm = make_combat()
    cm._elemental_blocked = True
    # На враге стихия блокируется...
    cm.enemy.add_status("poison", 3, cm)
    assert cm.enemy.poison == 0
    # ...а на игроке проходит как обычно.
    cm.player.add_status("poison", 3, cm)
    assert cm.player.poison == 3
