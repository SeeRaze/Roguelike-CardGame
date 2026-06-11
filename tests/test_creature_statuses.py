# tests/test_creature_statuses.py
# Проверяем существо (Creature): получение урона, щит, шипы, вампиризм, кровотечение
# и «тик» статусов в конце хода (яд/горение/реген/спад временных эффектов).
from core.Creature import Creature
from core.relics import ЗомбиПроцесс


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


def test_файрвол_отражает_урон_в_атакующего():
    target = Creature("Цель", 50, 50)
    attacker = Creature("Враг", 50, 50)
    target.firewall = 2
    target.take_damage(5, attacker=attacker)
    assert attacker.hp == 48    # 2 урона отражено файрволом


def test_вампиризм_лечит_атакующего_и_гаснет_втрое():
    target = Creature("Цель", 50, 50)
    attacker = Creature("Вампир", 40, 50)
    attacker.vampire = 4
    target.take_damage(10, attacker=attacker)
    # хил = max(1, 10*2//5) = 4 -> 40 + 4 = 44; вампиризм 4 -> 4//3 = 1
    assert attacker.hp == 44
    assert attacker.vampire == 1




def test_тик_legacy_наносит_урон_и_уменьшает_стак():
    # Legacy-код без щита: бьёт в HP на величину стака, затем убывает на 1.
    c = Creature("Цель", 50, 50)
    c.legacy = 3
    c.tick_statuses()
    assert c.hp == 47 and c.legacy == 2


def test_тик_хелсчека_лечит():
    c = Creature("Цель", 40, 50)
    c.healthcheck = 2
    c.tick_statuses()
    assert c.hp == 42 and c.healthcheck == 1


def test_тик_хелсчека_ограничен_потолком_за_ход():
    c = Creature("Цель", 10, 100)
    c.healthcheck = 20                 # стак выше потолка
    c.tick_statuses()
    # лечение срезано до HEALTHCHECK_HEAL_CAP_PER_TURN, стак убывает на 1
    assert c.hp == 10 + Creature.HEALTHCHECK_HEAL_CAP_PER_TURN
    assert c.healthcheck == 19


def test_временные_статусы_спадают_на_один():
    c = Creature("Цель", 50, 50)
    c.decomp = 2
    c.stunned = 2
    c.tick_statuses()
    assert c.decomp == 1 and c.stunned == 1


def test_legacy_убывает_на_один_без_зомби_процесса():
    c = Creature("Цель", 50, 50)
    c.legacy = 4
    c.tick_statuses()           # без реликвии -> триангуляр-декей −1
    assert c.legacy == 3


def test_зомби_процесс_держит_legacy(make_combat):
    c = Creature("Цель", 50, 50)
    c.legacy = 4
    cm = make_combat(enemy=c, relics=[ЗомбиПроцесс()])
    c.tick_statuses(cm)         # с «Зомби-процессом» -> Legacy не убывает
    assert c.legacy == 4


def test_магический_барьер_блокирует_стихию_только_на_враге(make_combat):
    cm = make_combat()
    cm._elemental_blocked = True
    # На враге стихия блокируется...
    cm.enemy.add_status("coffee", 3, cm)
    assert cm.enemy.coffee == 0
    # ...а на игроке проходит как обычно.
    cm.player.add_status("coffee", 3, cm)
    assert cm.player.coffee == 3
