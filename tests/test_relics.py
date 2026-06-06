# tests/test_relics.py
# Проверяем реликвии: каждая срабатывает на своём хуке и даёт нужный эффект.
from types import SimpleNamespace
from core.players import Warrior
from core.relics import (
    ALL_RELICS,
    ФлаконСЖелчью, ЗасохшийКлевер, ЗаточенныйОсколок, ПроклятаяКорона,
    СтараяПиявка, ШипастаяБроня, ОкровавленныйШприц, СвинцовыйНабалдашник,
    ПанцирьДикобраза, ГрозоваяБатарея, МеткаОхотника, ТотемЯрости,
    ФлаконКатализатора,
)


def test_в_пуле_27_уникальные_реликвии():
    assert len(ALL_RELICS) == 27
    имена = [r().name for r in ALL_RELICS]
    assert len(set(имена)) == 27


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


# --- Аудит cm.enemy: статусы реликвий в групповом бою не мажут в труп ---
# Реликвии на mid-combat хуках (on_card_played/on_shield_gained) били enemies[0]
# напрямую через cm.enemy. В групповом бою enemies[0] может быть трупом → статус
# уходил мимо. Фикс: get_target_enemy() (первый ЖИВОЙ враг).

def test_окровавленный_шприц_травит_живого_а_не_труп(make_combat, make_creature):
    """enemies[0] мёртв → Яд ложится на живого enemies[1], труп не задет."""
    cm = make_combat(player=Warrior())
    cm.player.energy = 0
    труп  = cm.enemies[0]
    труп.hp = 0
    живой = make_creature("Живой", 50, 50)
    cm.enemies.append(живой)
    ОкровавленныйШприц().on_card_played(SimpleNamespace(exile=True), cm)
    assert живой.poison == 2
    assert труп.poison == 0


def test_свинцовый_набалдашник_слабит_живого_а_не_труп(make_combat, make_creature):
    cm = make_combat()
    труп  = cm.enemies[0]
    труп.hp = 0
    живой = make_creature("Живой", 50, 50)
    cm.enemies.append(живой)
    СвинцовыйНабалдашник().on_card_played(SimpleNamespace(card_type="attack"), cm)
    assert живой.weak == 1
    assert труп.weak == 0


def test_шипастая_броня_кровит_живого_а_не_труп(make_combat, make_creature):
    cm = make_combat()
    труп  = cm.enemies[0]
    труп.hp = 0
    живой = make_creature("Живой", 50, 50)
    cm.enemies.append(живой)
    ШипастаяБроня().on_shield_gained(5, cm.player, cm)
    assert живой.bleed == 1
    assert труп.bleed == 0


def test_реликвии_без_живых_врагов_не_падают(make_combat):
    """Все враги мертвы → get_target_enemy()=None → реликвия тихо no-op (без краша)."""
    cm = make_combat(player=Warrior())
    cm.player.energy = 0
    cm.enemies[0].hp = 0
    ОкровавленныйШприц().on_card_played(SimpleNamespace(exile=True), cm)
    СвинцовыйНабалдашник().on_card_played(SimpleNamespace(card_type="attack"), cm)
    ШипастаяБроня().on_shield_gained(5, cm.player, cm)
    # Энергия от Шприца всё равно начисляется (до проверки цели)? Нет — return до лога,
    # но += energy идёт ДО target-проверки → +1 ожидаемо.
    assert cm.player.energy == 1


# --- Новые обычные артефакты (флэт-статы под непокрытые механики) ---

def test_панцирь_дикобраза_даёт_шипы(make_combat):
    cm = make_combat()
    ПанцирьДикобраза().on_combat_start(cm)
    assert cm.player.thorns == 3


def test_грозовая_батарея_шокирует_врага(make_combat):
    cm = make_combat()
    ГрозоваяБатарея().on_combat_start(cm)
    assert cm.enemy.shock == 2


def test_метка_охотника_вешает_уязвимость(make_combat):
    cm = make_combat()
    МеткаОхотника().on_combat_start(cm)
    assert cm.enemy.vulnerable == 1


def test_тотем_ярости_даёт_ярость(make_combat):
    cm = make_combat()
    ТотемЯрости().on_combat_start(cm)
    assert cm.player.strength == 1


def test_флакон_катализатора_мочит_врага(make_combat):
    cm = make_combat()
    ФлаконКатализатора().on_combat_start(cm)
    # Враг один — он гарантированно становится Мокрым (2 хода).
    assert cm.enemy.wet == 2
