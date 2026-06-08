# tests/test_berserker_cards.py
# Эффект-кирпичи сигнатурок Берсерка «Отрицание Смерти» (грани движка HP-долга).
# Тестируются НАПРЯМУЮ (инертно — фабрики/регистрация идут отдельным шагом).
from core.cards.base import Card, DamageEffect
from core.cards.berserker import (
    DebtScalingDamageEffect, SelfHarmEffect, DebtToForgeOnKillEffect,
)


def _berserker(make_creature, hp=60, max_hp=60):
    """Игрок с включённым HP-овердрафтом (как у класса Берсерк) + счётчиком FP."""
    p = make_creature("Берсерк", hp, max_hp)
    p.hp_overdraft = True
    p.forge_points = 0
    return p


# ═══════════════════════════════════════════════════════════
# DebtScalingDamageEffect — урон растёт с глубиной HP-долга
# ═══════════════════════════════════════════════════════════

def test_кровавая_ярость_вне_долга_бьёт_базой(make_creature):
    player = _berserker(make_creature)           # hp=60, долга нет
    enemy = make_creature("Враг", 50, 50)
    DebtScalingDamageEffect(6, 8, 1, 2).execute(player, enemy, None, False)
    assert enemy.hp == 44                         # ровно base=6, без бонуса глубины


def test_кровавая_ярость_в_долге_наращивает_базу(make_creature):
    player = _berserker(make_creature)
    player.hp = -5                                # глубина долга = 5
    enemy = make_creature("Враг", 50, 50)
    DebtScalingDamageEffect(6, 8, 1, 2).execute(player, enemy, None, False)
    assert enemy.hp == 50 - (6 + 1 * 5)           # 6 базы + 5 за глубину = 11


def test_кровавая_ярость_улучшенная_сильнее_масштабируется(make_creature):
    player = _berserker(make_creature)
    player.hp = -5
    enemy = make_creature("Враг", 50, 50)
    DebtScalingDamageEffect(6, 8, 1, 2).execute(player, enemy, None, True)
    assert enemy.hp == 50 - (8 + 2 * 5)           # улучш: 8 базы + 2×5 = 18


# ═══════════════════════════════════════════════════════════
# SelfHarmEffect — заплати кровью (нырок в долг)
# ═══════════════════════════════════════════════════════════

def test_самоурон_уводит_берсерка_в_минус(make_creature):
    player = _berserker(make_creature, hp=2)      # овердрафт включён
    SelfHarmEffect(4, 3).execute(player, None, None, False)
    assert player.hp == -2                         # 2 − 4 = −2 (ушёл в долг)


def test_самоурон_клампится_на_полу_долга(make_creature):
    player = _berserker(make_creature, hp=2)       # пол = -HP_DEBT_MAX_OVERDRAFT (-10)
    SelfHarmEffect(99, 99).execute(player, None, None, False)
    assert player.hp == -10                        # не глубже пола


def test_самоурон_без_овердрафта_не_ниже_нуля(make_creature):
    player = make_creature("Обычный", 5, 5)        # нет hp_overdraft → пол 0
    SelfHarmEffect(99, 99).execute(player, None, None, False)
    assert player.hp == 0                           # инертно-безопасен для не-Берсерков


# ═══════════════════════════════════════════════════════════
# DebtToForgeOnKillEffect — добивание в долге → FP (и гашение долга)
# ═══════════════════════════════════════════════════════════

def test_добивание_в_долге_конвертирует_долг_в_fp(make_creature):
    player = _berserker(make_creature)
    player.hp = -10
    enemy = make_creature("Труп", 0, 50)            # уже добит
    DebtToForgeOnKillEffect(0.5, 0.5).execute(player, enemy, None, False)
    assert player.forge_points == 5                 # int(10 × 0.5)
    assert player.hp == -5                          # долг погашен на 5 (к 0)


def test_живой_враг_не_даёт_fp(make_creature):
    player = _berserker(make_creature)
    player.hp = -10
    enemy = make_creature("Живой", 7, 50)
    DebtToForgeOnKillEffect(0.5, 0.5).execute(player, enemy, None, False)
    assert player.forge_points == 0                 # враг жив → не добили
    assert player.hp == -10


def test_добивание_без_долга_не_даёт_fp(make_creature):
    player = _berserker(make_creature)              # hp=60, долга нет
    enemy = make_creature("Труп", 0, 50)
    DebtToForgeOnKillEffect(0.5, 0.5).execute(player, enemy, None, False)
    assert player.forge_points == 0


# ═══════════════════════════════════════════════════════════
# Композиция «Жажда крови»: нырок → удар → (если добил) банк FP
# ═══════════════════════════════════════════════════════════

def test_жажда_крови_композиция_нырок_удар_банк(make_creature):
    player = _berserker(make_creature, hp=1)        # на грани
    enemy = make_creature("Враг", 6, 50)
    # SelfHarm 4 → hp = 1−4 = −3 (долг 3); Damage 6 → враг 6−6 = 0 (добит);
    # DebtToForgeOnKill 0.5 → int(3×0.5)=1 FP, долг −3 → −2.
    card = Card(
        name="Жажда крови", cost=1, card_type="attack", description="",
        effects=[SelfHarmEffect(4, 3), DamageEffect(6, 9),
                 DebtToForgeOnKillEffect(0.5, 0.5)],
    )
    card.apply(player, enemy)
    assert enemy.hp == 0
    assert player.forge_points == 1
    assert player.hp == -2
