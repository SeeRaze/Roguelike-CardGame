# tests/test_enemies.py
# Проверяем врагов: базовый Enemy (намерения, обратная совместимость,
# выполнение намерений) и конкретных врагов (Cultist, SlimeAndGoblins, BossTitan).
from core.enemies.base import Enemy, IntentAttack, IntentDefend, IntentDebuff, IntentNone
from core.enemies.cultist import Cultist
from core.enemies.slime import SlimeAndGoblins
from core.enemies.boss import BossTitan


# ═══════════════════════════════════════════════════════════
# Enemy — намерения (set_intent + обратная совместимость)
# ═══════════════════════════════════════════════════════════

def test_создание_врага_имеет_пустое_намерение():
    e = Enemy("ТестВраг", 30, 30)
    assert isinstance(e.intent, IntentNone)
    assert e.intent_type == "none"
    assert e.intent_value == 0


def test_set_intent_атака():
    e = Enemy("ТестВраг", 30, 30)
    e.set_intent("attack", 8)
    assert e.intent_type == "attack"
    assert e.intent_value == 8
    assert isinstance(e.intent, IntentAttack)


def test_set_intent_защита():
    e = Enemy("ТестВраг", 30, 30)
    e.set_intent("defend", 6)
    assert e.intent_type == "defend"
    assert e.intent_value == 6
    assert isinstance(e.intent, IntentDefend)


def test_set_intent_дебафф():
    e = Enemy("ТестВраг", 30, 30)
    e.set_intent("debuff", 2)
    assert e.intent_type == "debuff"
    assert e.intent_value == 2
    assert isinstance(e.intent, IntentDebuff)


def test_обратная_совместимость_intent_type_устанавливает_класс():
    """Старый код пишет enemy.intent_type = 'attack' — должно работать."""
    e = Enemy("ТестВраг", 30, 30)
    e.intent_type = "attack"
    e.intent_value = 10
    assert isinstance(e.intent, IntentAttack)
    assert e.intent.value == 10


def test_intent_value_на_IntentNone_меняет_значение_но_не_тип():
    """IntentNone имеет класс-атрибут value=0, поэтому hasattr(...) == True.
    Установка intent_value меняет значение, но не превращает в атаку."""
    e = Enemy("ТестВраг", 30, 30)
    assert isinstance(e.intent, IntentNone)
    e.intent_value = 7
    # Тип остаётся IntentNone, но значение изменилось
    assert isinstance(e.intent, IntentNone)
    assert e.intent.value == 7


# ═══════════════════════════════════════════════════════════
# Enemy.execute_intent — исполнение намерений
# ═══════════════════════════════════════════════════════════

def test_execute_intent_атака_наносит_урон_игроку(make_creature):
    enemy  = Enemy("Враг", 30, 30)
    player = make_creature("Игрок", 50, 50)
    enemy.set_intent("attack", 10)
    enemy.execute_intent(player, combat_manager=None)
    assert player.hp == 40            # 50 - 10


def test_execute_intent_защита_даёт_щит_врагу(make_creature):
    enemy  = Enemy("Враг", 30, 30)
    player = make_creature("Игрок", 50, 50)
    enemy.set_intent("defend", 8)
    enemy.execute_intent(player, combat_manager=None)
    assert enemy.shield == 8


def test_execute_intent_дебафф_вешает_токсичность(make_creature):
    enemy  = Enemy("Враг", 30, 30)
    player = make_creature("Игрок", 50, 50)
    enemy.set_intent("debuff", 2)
    enemy.execute_intent(player, combat_manager=None)
    assert player.tox == 2


def test_execute_intent_инкрементирует_turn_count(make_creature):
    enemy  = Enemy("Враг", 30, 30)
    player = make_creature("Игрок", 50, 50)
    assert enemy.turn_count == 0
    enemy.set_intent("attack", 5)
    enemy.execute_intent(player, combat_manager=None)
    assert enemy.turn_count == 1


# ═══════════════════════════════════════════════════════════
# Cultist — первый ход защита, дальше атака с усилением
# ═══════════════════════════════════════════════════════════

def test_культист_первый_ход_защищается():
    c = Cultist("Культист", 30, 30)
    c.base_test_shield = 6
    c.base_test_damage = 8
    c.choose_intent()
    assert c.intent_type == "defend"
    assert c.intent_value == 6


def test_культист_второй_ход_атакует():
    c = Cultist("Культист", 30, 30)
    c.base_test_shield = 6
    c.base_test_damage = 8
    c.turn_count = 1                 # не первый ход
    c.choose_intent()
    assert c.intent_type == "attack"
    assert c.intent_value == 9       # base 8 + turn_count 1


def test_культист_третий_ход_атакует_сильнее():
    c = Cultist("Культист", 30, 30)
    c.base_test_damage = 8
    c.turn_count = 2
    c.choose_intent()
    assert c.intent_type == "attack"
    assert c.intent_value == 10      # base 8 + turn_count 2


# ═══════════════════════════════════════════════════════════
# SlimeAndGoblins — чередование атака/защита
# ═══════════════════════════════════════════════════════════

def test_слизень_чётный_ход_атакует():
    s = SlimeAndGoblins("Слизень", 25, 25)
    s.base_test_damage = 6
    s.base_test_shield = 4
    s.turn_count = 0                 # чётный
    s.choose_intent()
    assert s.intent_type == "attack"
    assert s.intent_value == 6


def test_слизень_нечётный_ход_защищается():
    s = SlimeAndGoblins("Слизень", 25, 25)
    s.base_test_shield = 4
    s.turn_count = 1                 # нечётный
    s.choose_intent()
    assert s.intent_type == "defend"
    assert s.intent_value == 6       # base_shield + 2


# ═══════════════════════════════════════════════════════════
# BossTitan — паттерн из 3 ходов: щит → дебафф → атака
# ═══════════════════════════════════════════════════════════

def test_босс_первый_ход_щит():
    b = BossTitan("Титан", 80, 80)
    b.base_test_shield = 10
    b.base_test_damage = 15
    b.turn_count = 0                 # step 0
    b.choose_intent()
    assert b.intent_type == "defend"
    assert b.intent_value == 20      # shield * 2


def test_босс_второй_ход_дебафф():
    b = BossTitan("Титан", 80, 80)
    b.base_test_damage = 15
    b.turn_count = 1                 # step 1
    b.choose_intent()
    assert b.intent_type == "debuff"
    assert b.intent_value == 2


def test_босс_третий_ход_атака():
    b = BossTitan("Титан", 80, 80)
    b.base_test_damage = 15
    b.turn_count = 2                 # step 2
    b.choose_intent()
    assert b.intent_type == "attack"
    assert b.intent_value == 30      # damage * 2


def test_босс_четвёртый_ход_снова_щит():
    """Паттерн цикличный: после 3 ходов всё повторяется."""
    b = BossTitan("Титан", 80, 80)
    b.base_test_shield = 10
    b.turn_count = 3                 # step 0 опять
    b.choose_intent()
    assert b.intent_type == "defend"
    assert b.intent_value == 20
