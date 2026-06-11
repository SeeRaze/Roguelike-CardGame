# tests/test_relics.py
# Проверяем реликвии: каждая срабатывает на своём хуке и даёт нужный эффект.
from types import SimpleNamespace
from core.players import Warrior
from core.relics import (
    ALL_RELICS,
    GitBlame, ФоновоеИндексирование, УтреннийСозвон, МаршСмерти,
    СнекБар, Санитайзер, СборщикМусора, Дедлайн,
    Антивирус, БагРепорт, ЛидЗаСпиной,
    Кофемашина,
)


def test_в_пуле_33_уникальные_реликвии():
    # С57 (1d-pre): −Марш смерти (32→31). 2b/2c HP-ось: +ДМС (платиновый пакет)
    # (UNCOMMON), +Аптайм (EPIC) → 31→33. Срез Берсерка: +Овердрафт
    # (UNCOMMON, классовый компаунд) → 33→34. C3b: −Грозовая Батарея
    # (shock удалён) → 34→33.
    assert len(ALL_RELICS) == 33
    имена = [r().name for r in ALL_RELICS]
    assert len(set(имена)) == 33


def test_флакон_с_желчью_травит_врага_в_начале_боя(make_combat):
    cm = make_combat()
    GitBlame().on_combat_start(cm)
    assert cm.enemy.legacy == 3


def test_засохший_клевер_даёт_регенерацию(make_combat):
    cm = make_combat()
    ФоновоеИндексирование().on_combat_start(cm)
    assert cm.player.regen == 3


def test_заточенный_осколок_усиливает_первую_атаку(make_combat):
    cm = make_combat()
    relic = УтреннийСозвон()
    relic.on_combat_start(cm)
    assert relic.on_damage_calculated(10, is_player_attack=True) == 13   # первая +3
    assert relic.on_damage_calculated(10, is_player_attack=True) == 10   # дальше без бонуса


def test_проклятая_корона_удваивает_урон_игрока():
    relic = МаршСмерти()
    assert relic.on_damage_calculated(10, is_player_attack=True) == 20
    assert relic.on_damage_calculated(10, is_player_attack=False) == 10


def test_старая_пиявка_добавляет_к_хилу():
    c = SimpleNamespace(hp=40, max_hp=50)
    СнекБар().on_heal(5, c)
    assert c.hp == 42           # бонус +2 (ограничен нехваткой HP)


def test_санитайзер_вешает_legacy_при_получении_щита(make_combat):
    cm = make_combat()
    Санитайзер().on_shield_gained(5, cm.player, cm)
    assert cm.enemy.legacy == 1


def test_окровавленный_шприц_на_карте_изгнания(make_combat):
    cm = make_combat(player=Warrior())
    cm.player.energy = 0
    карта = SimpleNamespace(exile=True)
    СборщикМусора().on_card_played(карта, cm)
    assert cm.player.energy == 1
    assert cm.enemy.legacy == 2


def test_дедлайн_токсичит_первой_атакой(make_combat):
    cm = make_combat()
    relic = Дедлайн()
    атака = SimpleNamespace(card_type="attack")
    relic.on_card_played(атака, cm)
    assert cm.enemy.tox == 1
    # Вторая атака в том же ходу токсичность уже не накладывает.
    relic.on_card_played(атака, cm)
    assert cm.enemy.tox == 1


# --- Аудит cm.enemy: статусы реликвий в групповом бою не мажут в труп ---
# Реликвии на mid-combat хуках (on_card_played/on_shield_gained) били enemies[0]
# напрямую через cm.enemy. В групповом бою enemies[0] может быть трупом → статус
# уходил мимо. Фикс: get_target_enemy() (первый ЖИВОЙ враг).

def test_окровавленный_шприц_травит_живого_а_не_труп(make_combat, make_creature):
    """enemies[0] мёртв → Legacy-код ложится на живого enemies[1], труп не задет."""
    cm = make_combat(player=Warrior())
    cm.player.energy = 0
    труп  = cm.enemies[0]
    труп.hp = 0
    живой = make_creature("Живой", 50, 50)
    cm.enemies.append(живой)
    СборщикМусора().on_card_played(SimpleNamespace(exile=True), cm)
    assert живой.legacy == 2
    assert труп.legacy == 0


def test_свинцовый_набалдашник_слабит_живого_а_не_труп(make_combat, make_creature):
    cm = make_combat()
    труп  = cm.enemies[0]
    труп.hp = 0
    живой = make_creature("Живой", 50, 50)
    cm.enemies.append(живой)
    Дедлайн().on_card_played(SimpleNamespace(card_type="attack"), cm)
    assert живой.tox == 1
    assert труп.tox == 0


def test_шипастая_броня_кровит_живого_а_не_труп(make_combat, make_creature):
    cm = make_combat()
    труп  = cm.enemies[0]
    труп.hp = 0
    живой = make_creature("Живой", 50, 50)
    cm.enemies.append(живой)
    Санитайзер().on_shield_gained(5, cm.player, cm)
    assert живой.legacy == 1
    assert труп.legacy == 0


def test_реликвии_без_живых_врагов_не_падают(make_combat):
    """Все враги мертвы → get_target_enemy()=None → реликвия тихо no-op (без краша)."""
    cm = make_combat(player=Warrior())
    cm.player.energy = 0
    cm.enemies[0].hp = 0
    СборщикМусора().on_card_played(SimpleNamespace(exile=True), cm)
    Дедлайн().on_card_played(SimpleNamespace(card_type="attack"), cm)
    Санитайзер().on_shield_gained(5, cm.player, cm)
    # Энергия от Шприца всё равно начисляется (до проверки цели)? Нет — return до лога,
    # но += energy идёт ДО target-проверки → +1 ожидаемо.
    assert cm.player.energy == 1


# --- Новые обычные артефакты (флэт-статы под непокрытые механики) ---

def test_панцирь_дикобраза_даёт_файрвол(make_combat):
    cm = make_combat()
    Антивирус().on_combat_start(cm)
    assert cm.player.firewall == 3


def test_баг_репорт_вешает_кофе(make_combat):
    cm = make_combat()
    БагРепорт().on_combat_start(cm)
    assert cm.enemy.coffee == 1


def test_лид_за_спиной_даёт_оптимизацию(make_combat):
    cm = make_combat()
    ЛидЗаСпиной().on_combat_start(cm)
    assert cm.player.optimize == 1


def test_флакон_катализатора_обливает_кофе(make_combat):
    cm = make_combat()
    Кофемашина().on_combat_start(cm)
    # Враг один — он гарантированно облит Разлитым кофе (2 стака).
    assert cm.enemy.coffee == 2


# --- Высокотировые движки (EPIC): Автоматизация / Аутсорс ---

def test_эхо_вечности_даёт_эхо_в_начале_хода(make_combat):
    from core.relics import Автоматизация
    cm = make_combat()
    Автоматизация().on_turn_start(cm)
    assert cm.player.echo == 1


def test_несокрушимый_бастион_половину_щита_в_барьер(make_combat):
    """Половина полученного щита → несгораемый Барьер (игроку)."""
    from core.relics import Аутсорс
    cm = make_combat()
    Аутсорс().on_shield_gained(8, cm.player, cm)
    assert cm.player.barrier == 4          # 50% от 8


def test_бастион_малый_щит_не_даёт_барьер(make_combat):
    from core.relics import Аутсорс
    cm = make_combat()
    Аутсорс().on_shield_gained(1, cm.player, cm)
    assert cm.player.barrier == 0          # int(1*0.5)=0


def test_бастион_игнорирует_щит_не_игрока(make_combat):
    """Щит получил враг/союзник — Барьер игроку не начисляется."""
    from core.relics import Аутсорс
    cm = make_combat()
    Аутсорс().on_shield_gained(8, cm.enemy, cm)
    assert cm.player.barrier == 0


# --- LEGENDARY-джокер: Деплой в пятницу (×3 урон + 10% сжечь карту) ---

def test_стеклянный_глаз_утраивает_урон_атак():
    from core.relics import ДеплойВПятницу
    relic = ДеплойВПятницу()
    assert relic.on_damage_calculated(10, is_player_attack=True) == 30
    assert relic.on_damage_calculated(10, is_player_attack=False) == 10   # не атака игрока


def test_стеклянный_глаз_сжигает_карту_при_неудаче(make_combat, monkeypatch):
    """random < 0.10 → карта удаляется из gm.current_deck навсегда."""
    from core.relics import ДеплойВПятницу
    import core.relics.advanced.epic_legendary as mod
    cm = make_combat()
    карта = SimpleNamespace(name="Удар")
    cm.gm.current_deck = [карта, SimpleNamespace(name="Защита")]
    monkeypatch.setattr(mod.random, "random", lambda: 0.05)   # < BURN_CHANCE
    ДеплойВПятницу().on_card_played(карта, cm)
    assert карта not in cm.gm.current_deck
    assert len(cm.gm.current_deck) == 1


def test_стеклянный_глаз_не_сжигает_при_удаче(make_combat, monkeypatch):
    """random >= 0.10 → колода не трогается."""
    from core.relics import ДеплойВПятницу
    import core.relics.advanced.epic_legendary as mod
    cm = make_combat()
    карта = SimpleNamespace(name="Удар")
    cm.gm.current_deck = [карта]
    monkeypatch.setattr(mod.random, "random", lambda: 0.5)    # >= BURN_CHANCE
    ДеплойВПятницу().on_card_played(карта, cm)
    assert карта in cm.gm.current_deck


# --- LEGENDARY-джокер: Точка отказа (1 HP, щит→барьер→сила) ---

def test_гнилое_сердце_в_пуле_legendary():
    from core.relics import ТочкаОтказа, RELIC_POOL
    from core.rarity import Rarity
    assert ТочкаОтказа in RELIC_POOL[Rarity.LEGENDARY]


def test_гнилое_сердце_сажает_макс_хп_в_1(make_combat):
    from core.relics import ТочкаОтказа
    cm = make_combat()
    ТочкаОтказа().on_combat_start(cm)
    assert cm.player.max_hp == 1
    assert cm.player.hp == 1


def test_гнилое_сердце_банкует_щит_в_барьер_и_растит_силу(make_combat):
    from core.relics import ТочкаОтказа
    cm = make_combat()
    relic = ТочкаОтказа()
    relic.on_combat_start(cm)
    cm.player.shield = 25
    relic.on_turn_end(cm)
    assert cm.player.barrier == 25          # весь щит банкнут в Барьер
    assert cm.player.optimize == 2          # 25 // 10


def test_точка_отказа_не_затирает_чужую_оптимизацию(make_combat):
    """Инкрементальный вклад: внешняя Оптимизация сохраняется."""
    from core.relics import ТочкаОтказа
    cm = make_combat()
    relic = ТочкаОтказа()
    relic.on_combat_start(cm)
    cm.player.optimize = 5                  # оптимизация из другого источника
    cm.player.shield = 30
    relic.on_turn_end(cm)
    assert cm.player.optimize == 5 + 3       # 30//10 поверх внешних 5
