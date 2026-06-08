# tests/test_mage_cards.py
# Эффект-кирпичи передела Мага «Гни» (С56): гамбл HP→Мастерство (Разгон) и payoff
# глубины (Резонансный разряд). Тестируются НАПРЯМУЮ (combat_manager=None → шаг 2c
# Мастерства НЕ срабатывает, ассерты урона чистые; двойной учёт — только в живом бою).
from core.cards.base import Card
from core.cards.mage import OverclockEffect, MasteryScalingDamageEffect


def _mage(make_creature, hp=70, max_hp=70):
    return make_creature("Маг", hp, max_hp)


# ═══════════════════════════════════════════════════════════
# OverclockEffect — заплати %max HP → +Мастерство
# ═══════════════════════════════════════════════════════════

def test_разгон_платит_процент_max_hp_за_мастерство(make_creature):
    player = _mage(make_creature)                    # max_hp=70
    OverclockEffect(0.10, 3, 4).execute(player, None, None, False)
    assert player.hp == 70 - 7                        # 10% от 70 = 7
    assert player.mastery == 3


def test_разгон_цена_масштабируется_с_max_hp(make_creature):
    player = _mage(make_creature, hp=200, max_hp=200)  # «прокачанный» max HP
    OverclockEffect(0.10, 3, 4).execute(player, None, None, False)
    assert player.hp == 200 - 20                      # 10% от 200 = 20 (масштаб-инвариант)
    assert player.mastery == 3


def test_разгон_улучшенный_даёт_больше_мастерства(make_creature):
    player = _mage(make_creature)
    OverclockEffect(0.10, 3, 4).execute(player, None, None, True)
    assert player.mastery == 4


def test_разгон_не_уводит_ниже_нуля(make_creature):
    player = _mage(make_creature, hp=3, max_hp=70)    # цена 7 > текущего HP
    OverclockEffect(0.10, 3, 4).execute(player, None, None, False)
    assert player.hp == 0                             # клампится на полу (нет овердрафта)
    assert player.mastery == 3


# ═══════════════════════════════════════════════════════════
# MasteryScalingDamageEffect — урон = base + per×Мастерство (НЕ тратит)
# ═══════════════════════════════════════════════════════════

def test_разряд_вне_мастерства_бьёт_базой(make_creature):
    player = _mage(make_creature)                    # mastery = 0
    enemy = make_creature("Враг", 50, 50)
    MasteryScalingDamageEffect(6, 9, 2, 3).execute(player, enemy, None, False)
    assert enemy.hp == 44                             # ровно base=6


def test_разряд_масштабируется_с_мастерством_не_тратит(make_creature):
    player = _mage(make_creature)
    player.set_status("mastery", 4)
    enemy = make_creature("Враг", 50, 50)
    MasteryScalingDamageEffect(6, 9, 2, 3).execute(player, enemy, None, False)
    assert enemy.hp == 50 - (6 + 2 * 4)               # 6 + 2×4 = 14
    assert player.mastery == 4                        # НЕ потрачено (компаунд держится)


def test_разряд_улучшенный_сильнее(make_creature):
    player = _mage(make_creature)
    player.set_status("mastery", 4)
    enemy = make_creature("Враг", 50, 50)
    MasteryScalingDamageEffect(6, 9, 2, 3).execute(player, enemy, None, True)
    assert enemy.hp == 50 - (9 + 3 * 4)               # улучш: 9 + 3×4 = 21


# ═══════════════════════════════════════════════════════════
# Композиция: Разгон копит Мастерство → Разряд его выжимает (держит)
# ═══════════════════════════════════════════════════════════

def test_разгон_затем_разряд(make_creature):
    player = _mage(make_creature)
    enemy = make_creature("Враг", 99, 99)
    Card("Разгон", 1, "skill", "", [OverclockEffect(0.10, 3, 4)]).apply(player, enemy)
    assert player.mastery == 3
    Card("Резонансный разряд", 2, "attack", "",
         [MasteryScalingDamageEffect(6, 9, 2, 3)]).apply(player, enemy)
    assert enemy.hp == 99 - (6 + 2 * 3)               # урон с накопленным Мастерством 3
    assert player.mastery == 3                        # Разряд Мастерство не сжёг
