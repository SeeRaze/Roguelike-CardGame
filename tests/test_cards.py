# tests/test_cards.py
# Проверяем класс Card и все классы эффектов (DamageEffect, ShieldEffect,
# HealEffect, StatusEffect, PoisonEffect, RegenEffect, BuffEffect,
# BleedEffect, VampireBuffEffect).
# Эффекты — фундамент боя: если execute() работает неверно, ломаются все карты.
from core.cards.base import (
    Card, DamageEffect, ShieldEffect, HealEffect,
    StatusEffect, PoisonEffect, RegenEffect,
)
from core.cards.buff.strength import BuffEffect
from core.cards.buff.vampirism import VampireBuffEffect
from core.cards.debuff.bleed import BleedEffect
from core.rarity import Rarity


# ═══════════════════════════════════════════════════════════
# Card — создание и методы
# ═══════════════════════════════════════════════════════════

def test_создание_карты_сохраняет_все_атрибуты():
    эффекты = [DamageEffect(5, 8)]
    card = Card(
        name="Пробный Удар",
        cost=2,
        card_type="attack",
        description="Тестовая атака.",
        effects=эффекты,
        rarity=Rarity.UNCOMMON,
        exile=True,
    )
    assert card.name == "Пробный Удар"
    assert card.cost == 2
    assert card.card_type == "attack"
    assert card.description == "Тестовая атака."
    assert card.effects == эффекты
    assert card.rarity == Rarity.UNCOMMON
    assert card.exile is True
    assert card.upgraded is False


def test_редкость_карты_по_умолчанию_common():
    card = Card("Обычная Карта", 1, "skill", "...", [])
    assert card.rarity == Rarity.COMMON


def test_улучшение_карты_меняет_флаг_и_добавляет_плюс_к_имени():
    card = Card("Удар", 1, "attack", "...", [DamageEffect(6, 9)])
    card.upgrade()
    assert card.upgraded is True
    assert card.name == "Удар+"


def test_повторное_улучшение_не_имеет_эффекта():
    card = Card("Удар", 1, "attack", "...", [DamageEffect(6, 9)])
    card.upgrade()
    card.upgrade()                      # второй раз — заглушка
    assert card.name == "Удар+"         # не "Удар++"


def test_apply_вызывает_каждый_эффект_по_очереди(make_creature):
    """Card.apply() дёргает effect.execute() для всех эффектов в списке."""
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)

    # Два DamageEffect: 3 + 4 = 7 урона
    card = Card("Двойной Удар", 1, "attack", "...", [
        DamageEffect(3, 5),
        DamageEffect(4, 6),
    ])
    card.apply(player, enemy)
    assert enemy.hp == 43              # 50 - 7


# ═══════════════════════════════════════════════════════════
# DamageEffect
# ═══════════════════════════════════════════════════════════

def test_damage_effect_базовый_урон(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    DamageEffect(6, 9).execute(player, enemy, combat_manager=None, is_upgraded=False)
    assert enemy.hp == 44              # 50 - 6


def test_damage_effect_улучшенный_урон(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    DamageEffect(6, 9).execute(player, enemy, combat_manager=None, is_upgraded=True)
    assert enemy.hp == 41              # 50 - 9


def test_damage_effect_пишет_в_лог(make_combat, make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    cm = make_combat(player=player, enemy=enemy)
    DamageEffect(5, 8).execute(player, enemy, combat_manager=cm, is_upgraded=False)
    assert len(cm.log) == 1            # DamageEffect пишет одно сообщение
    assert "5 урона" in cm.log[0]


# ═══════════════════════════════════════════════════════════
# ShieldEffect
# ═══════════════════════════════════════════════════════════

def test_shield_effect_базовый_щит(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    ShieldEffect(5, 8).execute(player, enemy, combat_manager=None, is_upgraded=False)
    assert player.shield == 5


def test_shield_effect_улучшенный_щит(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    ShieldEffect(5, 8).execute(player, enemy, combat_manager=None, is_upgraded=True)
    assert player.shield == 8


# ═══════════════════════════════════════════════════════════
# HealEffect
# ═══════════════════════════════════════════════════════════

def test_heal_effect_восстанавливает_hp(make_creature):
    player = make_creature("Игрок", 30, 50)
    enemy  = make_creature("Враг", 50, 50)
    HealEffect(8, 12).execute(player, enemy, combat_manager=None, is_upgraded=False)
    assert player.hp == 38             # 30 + 8


def test_heal_effect_не_превышает_max_hp(make_creature):
    player = make_creature("Игрок", 45, 50)
    enemy  = make_creature("Враг", 50, 50)
    HealEffect(10, 15).execute(player, enemy, combat_manager=None, is_upgraded=False)
    assert player.hp == 50             # не 55


def test_heal_effect_улучшенный(make_creature):
    player = make_creature("Игрок", 20, 50)
    enemy  = make_creature("Враг", 50, 50)
    HealEffect(8, 12).execute(player, enemy, combat_manager=None, is_upgraded=True)
    assert player.hp == 32             # 20 + 12


# ═══════════════════════════════════════════════════════════
# StatusEffect
# ═══════════════════════════════════════════════════════════

def test_status_effect_накладывает_статус_на_врага(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    StatusEffect("vulnerable", 2, 3).execute(player, enemy, combat_manager=None, is_upgraded=False)
    assert enemy.vulnerable == 2


def test_status_effect_улучшенный(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    StatusEffect("weak", 1, 2).execute(player, enemy, combat_manager=None, is_upgraded=True)
    assert enemy.weak == 2             # upgrade_turns=2, не base_turns=1


# ═══════════════════════════════════════════════════════════
# PoisonEffect
# ═══════════════════════════════════════════════════════════

def test_poison_effect_накладывает_яд(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    PoisonEffect(3, 5).execute(player, enemy, combat_manager=None, is_upgraded=False)
    assert enemy.poison == 3


def test_poison_effect_улучшенный(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    PoisonEffect(3, 5).execute(player, enemy, combat_manager=None, is_upgraded=True)
    assert enemy.poison == 5


# ═══════════════════════════════════════════════════════════
# BuffEffect (strength, thorns, etc.)
# ═══════════════════════════════════════════════════════════

def test_buff_effect_накладывает_бафф_на_игрока(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    player.strength = 1
    BuffEffect("strength", 2, 3).execute(player, enemy, combat_manager=None, is_upgraded=False)
    assert player.strength == 3        # 1 + 2


def test_buff_effect_улучшенный(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    BuffEffect("thorns", 3, 5).execute(player, enemy, combat_manager=None, is_upgraded=True)
    assert player.thorns == 5


# ═══════════════════════════════════════════════════════════
# BleedEffect (кровотечение на врага)
# ═══════════════════════════════════════════════════════════

def test_bleed_effect_накладывает_кровотечение(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    BleedEffect(3, 4).execute(player, enemy, combat_manager=None, is_upgraded=False)
    assert enemy.bleed == 3


def test_bleed_effect_улучшенный(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    BleedEffect(3, 4).execute(player, enemy, combat_manager=None, is_upgraded=True)
    assert enemy.bleed == 4


# ═══════════════════════════════════════════════════════════
# VampireBuffEffect (вампиризм на игрока)
# ═══════════════════════════════════════════════════════════

def test_vampire_effect_накладывает_вампиризм(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    VampireBuffEffect(4, 6).execute(player, enemy, combat_manager=None, is_upgraded=False)
    assert player.vampire == 4
