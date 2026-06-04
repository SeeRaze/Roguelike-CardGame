# tests/test_detonations.py
# Фундамент детонационных комбо: DetonationRegistry + DetonateEffect.
# Детонации — мгновенный эффект (бурст/AoE), в отличие от множительных комбо.
from core.DetonationRegistry import (
    DETONATIONS, all_detonations,
    _electro_blast, _lava, _thermo_blast, _acid, _poison_blast,
    ELECTRO_DAMAGE_PER_SHOCK, LAVA_DAMAGE_PER_IGNITE, THERMO_DAMAGE_MULT,
)
from core.cards.base import DetonateEffect
from core.cards.basic import create_catalyst
from core.cards.catalog import GENERIC_FACTORIES
from core.Creature import Creature
from core.enemies import Enemy


# ═══════════════════════════════════════════════════════════
# Реестр
# ═══════════════════════════════════════════════════════════

def test_реестр_содержит_электро_взрыв():
    det = DETONATIONS.get("electro_blast")
    assert det is not None
    assert det["requires"] == ("wet", "shock")
    assert callable(det["handler"])
    assert "ЭЛЕКТРО-ВЗРЫВ" in det["name"]


def test_all_detonations_возвращает_тот_же_словарь():
    assert all_detonations() is DETONATIONS


# ═══════════════════════════════════════════════════════════
# Хендлер Электро-взрыва
# ═══════════════════════════════════════════════════════════

def test_электро_взрыв_бьёт_по_шоку_и_снимает_статусы(make_combat):
    target = Creature("Цель", 50, 50)
    target.wet = 2
    target.shock = 3
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    burst = _electro_blast(target, cm)
    assert burst == 3 * ELECTRO_DAMAGE_PER_SHOCK     # 18
    assert target.hp == 32                           # 50 - 18
    assert target.wet == 0 and target.shock == 0     # статусы потрачены


def test_электро_взрыв_aoe_по_всем_врагам(make_combat):
    target = Creature("Цель", 50, 50)
    other  = Creature("Враг2", 50, 50)
    target.wet = 1
    target.shock = 2
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    cm.enemies = [target, other]
    _electro_blast(target, cm)
    burst = 2 * ELECTRO_DAMAGE_PER_SHOCK             # 12
    assert target.hp == 50 - burst
    assert other.hp == 50 - burst                    # AoE задел второго


# ═══════════════════════════════════════════════════════════
# DetonateEffect — триггер
# ═══════════════════════════════════════════════════════════

def test_детонатор_срабатывает_при_мокром_и_шоке(make_combat):
    target = Creature("Цель", 50, 50)
    target.wet = 1
    target.shock = 2
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    DetonateEffect().execute(cm.player, target, cm, is_upgraded=False)
    assert target.hp == 50 - 2 * ELECTRO_DAMAGE_PER_SHOCK
    assert target.wet == 0 and target.shock == 0


def test_детонатор_молчит_без_полного_набора(make_combat):
    # Только Шок, без Мокрого → детонация не срабатывает.
    target = Creature("Цель", 50, 50)
    target.shock = 3
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    DetonateEffect().execute(cm.player, target, cm, is_upgraded=False)
    assert target.hp == 50                           # урона нет
    assert target.shock == 3                          # статус на месте


def test_детонатор_без_боя_не_падает():
    target = Creature("Цель", 50, 50)
    target.wet = 1
    target.shock = 1
    DetonateEffect().execute(None, target, None, is_upgraded=False)   # не бросает
    assert target.hp == 50


# ═══════════════════════════════════════════════════════════
# Реестр содержит все 4 детонации
# ═══════════════════════════════════════════════════════════

def test_реестр_содержит_все_детонации():
    assert set(DETONATIONS) == {
        "electro_blast", "thermo_blast", "lava", "acid", "poison_blast",
    }
    assert DETONATIONS["thermo_blast"]["requires"] == ("ignited", "shock")
    assert DETONATIONS["lava"]["requires"] == ("shatter", "ignited")
    assert DETONATIONS["acid"]["requires"] == ("wet", "poison")
    assert DETONATIONS["poison_blast"]["requires"] == ("poison", "ignited")


# ═══════════════════════════════════════════════════════════
# Лава (Раскол + Горение)
# ═══════════════════════════════════════════════════════════

def test_лава_урон_и_ослабление_намерения(make_combat):
    target = Enemy("Враг", 50, 50)
    target.set_intent("attack", 10)
    target.shatter = 2
    target.ignited = 3
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    burst = _lava(target, cm)
    assert burst == 3 * LAVA_DAMAGE_PER_IGNITE       # 12
    assert target.hp == 38
    assert target.intent_value == 5                  # 10 // 2 — атака ослаблена
    assert target.shatter == 0 and target.ignited == 0


def test_лава_не_трогает_не_атакующее_намерение(make_combat):
    target = Enemy("Враг", 50, 50)
    target.set_intent("defend", 8)                   # защита, не атака
    target.shatter = 1
    target.ignited = 1
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    _lava(target, cm)
    assert target.intent_value == 8                  # намерение не тронуто


# ═══════════════════════════════════════════════════════════
# Термодинамический взрыв (Горение + Шок)
# ═══════════════════════════════════════════════════════════

def test_термовзрыв_бьёт_по_сумме_статусов(make_combat):
    target = Creature("Цель", 50, 50)
    target.ignited = 2
    target.shock = 3
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    burst = _thermo_blast(target, cm)
    assert burst == (2 + 3) * THERMO_DAMAGE_MULT     # 15
    assert target.hp == 35
    assert target.ignited == 0 and target.shock == 0


# ═══════════════════════════════════════════════════════════
# Кислота (Мокрый + Яд)
# ═══════════════════════════════════════════════════════════

def test_кислота_обнуляет_щит_и_оставляет_яд(make_combat):
    target = Creature("Цель", 50, 50)
    target.shield = 20
    target.wet = 1
    target.poison = 4
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    _acid(target, cm)
    assert target.shield == 0
    assert target.wet == 0                           # катализатор потрачен
    assert target.poison == 4                        # яд остаётся тикать


# ═══════════════════════════════════════════════════════════
# Ядовзрыв (Яд + Горение)
# ═══════════════════════════════════════════════════════════

def test_ядовзрыв_детонирует_яд_сквозь_щит_и_удваивает_горение(make_combat):
    target = Creature("Цель", 50, 50)
    target.shield = 30          # щит большой — но яд бьёт СКВОЗЬ него
    target.poison = 7
    target.ignited = 2
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    burst = _poison_blast(target, cm)
    assert burst == 7
    assert target.hp == 43      # 50 - 7 прямо в HP (щит не тронут)
    assert target.shield == 30  # щит проигнорирован
    assert target.poison == 0   # весь яд сдетонирован
    assert target.ignited == 4  # горение удвоено (2 -> 4)


def test_ядовзрыв_через_детонатор(make_combat):
    target = Creature("Цель", 50, 50)
    target.poison = 5
    target.ignited = 1
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    DetonateEffect().execute(cm.player, target, cm, is_upgraded=False)
    assert target.hp == 45 and target.poison == 0 and target.ignited == 2


# ═══════════════════════════════════════════════════════════
# Приоритет при общих статусах (порядок в DETONATIONS)
# ═══════════════════════════════════════════════════════════

def test_электро_имеет_приоритет_над_кислотой_по_общему_мокрому(make_combat):
    # wet общий для электро (wet+shock) и кислоты (wet+poison). Электро идёт
    # первым → тратит wet → кислота уже не срабатывает.
    target = Creature("Цель", 50, 50)
    target.shield = 20
    target.wet = 2
    target.shock = 2
    target.poison = 3
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    DetonateEffect().execute(cm.player, target, cm, is_upgraded=False)
    assert target.wet == 0 and target.shock == 0     # электро потратил wet+shock
    # Электро-бурст 12 ушёл в щит (20 → 8). Если бы сработала Кислота — щит был
    # бы 0; значит общий wet достался электро, а кислота пропущена.
    assert target.shield == 20 - 2 * ELECTRO_DAMAGE_PER_SHOCK   # == 8
    assert target.hp == 50                           # щит поглотил бурст
    assert target.poison == 3                         # яд не тронут


# ═══════════════════════════════════════════════════════════
# «Катализатор» — нейтральный универсальный детонатор
# ═══════════════════════════════════════════════════════════

def test_катализатор_в_общем_пуле():
    assert create_catalyst in GENERIC_FACTORIES


def test_катализатор_детонирует_кислоту(make_combat):
    # Чистый триггер: сам урона не наносит, но подрывает Кислоту (Мокрый+Яд).
    target = Creature("Цель", 50, 50)
    target.shield = 15
    target.wet = 1
    target.poison = 5
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    create_catalyst().apply(cm.player, target, cm)
    assert target.shield == 0          # кислота растворила щит
    assert target.wet == 0
    assert target.poison == 5          # яд остался


def test_катализатор_без_комбо_ничего_не_ломает(make_combat):
    target = Creature("Цель", 50, 50)
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    create_catalyst().apply(cm.player, target, cm)
    assert target.hp == 50             # ни урона, ни ошибок
