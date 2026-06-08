# tests/test_warrior_cards.py
# Эффект-кирпичи сигнатурок Воина «Дисциплина-как-ресурс» (С56): спендеры Дисциплины.
# Тестируются НАПРЯМУЮ (инертно — фабрики/регистрация идут отдельным шагом).
from core.cards.base import Card
from core.cards.warrior import (
    DisciplineBurstDamageEffect, DisciplineToShieldEffect, DisciplineGainEffect,
)
from core.cards.catalog import CLASS_FACTORIES, get_pool_for_class, get_class_cards

_SIGNATURES = {"Карающий строй", "Стена щитов", "Стойка"}


def _warrior(make_creature, hp=90, max_hp=90):
    return make_creature("Воин", hp, max_hp)


# ═══════════════════════════════════════════════════════════
# DisciplineBurstDamageEffect — сжечь Дисциплину → урон base+per×spent
# ═══════════════════════════════════════════════════════════

def test_карающий_строй_вне_дисциплины_бьёт_базой(make_creature):
    player = _warrior(make_creature)                 # discipline = 0
    enemy = make_creature("Враг", 50, 50)
    DisciplineBurstDamageEffect(6, 9, 2, 3).execute(player, enemy, None, False)
    assert enemy.hp == 44                             # ровно base=6, бонуса нет


def test_карающий_строй_сжигает_дисциплину_в_урон(make_creature):
    player = _warrior(make_creature)
    player.set_status("discipline", 5)                # накоплено 5
    enemy = make_creature("Враг", 50, 50)
    DisciplineBurstDamageEffect(6, 9, 2, 3).execute(player, enemy, None, False)
    assert enemy.hp == 50 - (6 + 2 * 5)               # 6 + 2×5 = 16
    assert player.discipline == 0                     # стак сожжён (теряем +урон 2d)


def test_карающий_строй_улучшенный_сильнее(make_creature):
    player = _warrior(make_creature)
    player.set_status("discipline", 5)
    enemy = make_creature("Враг", 50, 50)
    DisciplineBurstDamageEffect(6, 9, 2, 3).execute(player, enemy, None, True)
    assert enemy.hp == 50 - (9 + 3 * 5)               # улучш: 9 + 3×5 = 24
    assert player.discipline == 0


# ═══════════════════════════════════════════════════════════
# DisciplineToShieldEffect — сжечь Дисциплину → щит-стена
# ═══════════════════════════════════════════════════════════

def test_стена_щитов_вне_дисциплины_даёт_базу(make_creature):
    player = _warrior(make_creature)
    DisciplineToShieldEffect(5, 8, 1, 2).execute(player, None, None, False)
    assert player.shield == 5                         # ровно base


def test_стена_щитов_сжигает_дисциплину_в_щит(make_creature):
    player = _warrior(make_creature)
    player.set_status("discipline", 4)
    DisciplineToShieldEffect(5, 8, 1, 2).execute(player, None, None, False)
    assert player.shield == 5 + 1 * 4                 # 5 + 4 = 9
    assert player.discipline == 0


def test_стена_щитов_суммируется_с_имеющимся_щитом(make_creature):
    player = _warrior(make_creature)
    player.shield = 10
    player.set_status("discipline", 3)
    DisciplineToShieldEffect(5, 8, 1, 2).execute(player, None, None, False)
    assert player.shield == 10 + (5 + 1 * 3)          # прибавляет к текущему


# ═══════════════════════════════════════════════════════════
# DisciplineGainEffect — билдер (+N Дисциплины)
# ═══════════════════════════════════════════════════════════

def test_стойка_копит_дисциплину(make_creature):
    player = _warrior(make_creature)
    DisciplineGainEffect(2, 3).execute(player, None, None, False)
    assert player.discipline == 2
    DisciplineGainEffect(2, 3).execute(player, None, None, True)
    assert player.discipline == 2 + 3                 # стаки складываются


# ═══════════════════════════════════════════════════════════
# Композиция: накопил Дисциплину → один спендер тратит её ВСЮ
# ═══════════════════════════════════════════════════════════

def test_спендер_тратит_всю_дисциплину_второй_бьёт_базой(make_creature):
    player = _warrior(make_creature)
    player.set_status("discipline", 6)
    enemy = make_creature("Враг", 99, 99)
    burst = Card("Карающий строй", 1, "attack", "",
                 [DisciplineBurstDamageEffect(6, 9, 2, 3)])
    burst.apply(player, enemy)
    assert enemy.hp == 99 - (6 + 2 * 6)               # 18 урона
    # Дисциплина обнулена — второй спендер бьёт только базой.
    burst2 = Card("Карающий строй", 1, "attack", "",
                  [DisciplineBurstDamageEffect(6, 9, 2, 3)])
    burst2.apply(player, enemy)
    assert player.discipline == 0


# ═══════════════════════════════════════════════════════════
# Регистрация: сигнатурки достижимы в пуле Воина (StS-инфра)
# ═══════════════════════════════════════════════════════════

def test_воин_сигнатурки_зарегистрированы():
    names = {f().name for f in CLASS_FACTORIES["Warrior"]}
    assert _SIGNATURES <= names                      # 3 новых + старая ось в пуле


def test_воин_сигнатурки_в_пуле_класса():
    pool_names = {f().name for f in get_pool_for_class("Warrior")}
    assert _SIGNATURES <= pool_names


def test_воин_сигнатурки_тегированы_классом():
    for card in (f() for f in get_class_cards("Warrior")):
        assert card.card_class == "Warrior"


def test_воин_сигнатурки_не_в_generic():
    from core.cards.catalog import GENERIC_FACTORIES
    generic_names = {f().name for f in GENERIC_FACTORIES}
    for n in _SIGNATURES:
        assert n not in generic_names
