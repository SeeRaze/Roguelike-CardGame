# tests/test_berserker_cards.py
# Эффект-кирпичи сигнатурок Берсерка «Отрицание Смерти» (грани движка HP-долга).
# Тестируются НАПРЯМУЮ (инертно — фабрики/регистрация идут отдельным шагом).
from core.cards.base import Card, DamageEffect
from core.cards.berserker import (
    DebtScalingDamageEffect, SelfHarmEffect, DebtToForgeOnKillEffect,
    LifestealOnKillEffect,
)
from core.cards.catalog import CLASS_FACTORIES, get_pool_for_class, get_class_cards


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
    player = _berserker(make_creature, hp=2)      # овердрафт включён, max 60
    SelfHarmEffect(0.07, 0.05).execute(player, None, None, False)
    assert player.hp == -2                         # 2 − int(0.07·60=4) = −2 (ушёл в долг)


def test_самоурон_клампится_на_полу_долга(make_creature):
    from core import debt
    player = _berserker(make_creature, hp=2)       # пол = −50% max HP (на 60 → −30)
    SelfHarmEffect(1.0, 1.0).execute(player, None, None, False)
    assert player.hp == debt.hp_debt_floor(player.max_hp)  # не глубже пола (динамич.)


def test_самоурон_без_овердрафта_не_ниже_нуля(make_creature):
    player = make_creature("Обычный", 5, 5)        # нет hp_overdraft → пол 0
    SelfHarmEffect(1.0, 1.0).execute(player, None, None, False)
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
        effects=[SelfHarmEffect(0.07, 0.05), DamageEffect(6, 9),
                 DebtToForgeOnKillEffect(0.5, 0.5)],
    )
    card.apply(player, enemy)
    assert enemy.hp == 0
    assert player.forge_points == 1
    assert player.hp == -2


# ═══════════════════════════════════════════════════════════
# LifestealOnKillEffect — добил в долге → второе дыхание (сустейн)
# ═══════════════════════════════════════════════════════════

def test_добивание_лечит_процентом_max_hp(make_creature):
    player = _berserker(make_creature)             # max 60
    player.hp = -20                                # в долге
    enemy = make_creature("Труп", 0, 50)           # уже добит
    LifestealOnKillEffect(0.20, 0.25).execute(player, enemy, None, False)
    assert player.hp == -20 + int(0.20 * 60)       # +12 → climb-out до −8


def test_лайфстил_живой_враг_не_лечит(make_creature):
    player = _berserker(make_creature)
    player.hp = -20
    enemy = make_creature("Живой", 5, 50)
    LifestealOnKillEffect(0.20, 0.25).execute(player, enemy, None, False)
    assert player.hp == -20                        # враг жив → нет хила


def test_лайфстил_не_превышает_max_hp(make_creature):
    player = _berserker(make_creature, hp=55)      # почти полный
    enemy = make_creature("Труп", 0, 50)
    LifestealOnKillEffect(0.20, 0.25).execute(player, enemy, None, False)
    assert player.hp == 60                         # хил клампится на max_hp


# ═══════════════════════════════════════════════════════════
# Регистрация: карты достижимы в пуле своего класса (StS-инфра)
# ═══════════════════════════════════════════════════════════

def test_берсерк_карты_зарегистрированы():
    names = {f().name for f in CLASS_FACTORIES["Berserker"]}
    assert names == {"Кровавая ярость", "Безрассудный удар", "Жажда крови", "Кранч"}


def test_берсерк_карты_в_пуле_класса():
    pool_names = {f().name for f in get_pool_for_class("Berserker")}
    assert {"Кровавая ярость", "Безрассудный удар", "Жажда крови", "Кранч"} <= pool_names


def test_берсерк_карты_тегированы_классом():
    # _tagged проставляет card_class централизованно → выдаются только своему классу.
    for card in (f() for f in get_class_cards("Berserker")):
        assert card.card_class == "Berserker"


def test_берсерк_карты_не_в_generic():
    from core.cards.catalog import GENERIC_FACTORIES
    generic_names = {f().name for f in GENERIC_FACTORIES}
    for n in ("Кровавая ярость", "Безрассудный удар", "Жажда крови", "Кранч"):
        assert n not in generic_names


# ═══════════════════════════════════════════════════════════
# BerserkerPolicy — пилотирование самоурона (честность замера)
# ═══════════════════════════════════════════════════════════

class _StubCombat:
    """Минимальный контекст для _class_pick: игрок + одна цель."""
    def __init__(self, player, enemy):
        self.player = player
        self.enemies = [enemy]
        self._enemy = enemy

    def get_target_enemy(self):
        return self._enemy if self._enemy.hp > 0 else None


def _bloodthirst():
    return Card("Жажда крови", 1, "attack", "",
                [SelfHarmEffect(0.07, 0.05), DamageEffect(8, 11)])


def test_политика_приберегает_самоурон_играет_безопасную(make_creature):
    from managers.balance.policy import BerserkerPolicy
    player = _berserker(make_creature)             # hp=60 (healthy)
    combat = _StubCombat(player, make_creature("Враг", 50, 50))
    safe = Card("Удар", 1, "attack", "", [DamageEffect(6, 8)])
    pick = BerserkerPolicy()._class_pick([safe, _bloodthirst()], combat)
    assert pick is safe                            # безопасную вперёд, нырок приберегаем


def test_политика_завершает_ход_если_нырок_опасен(make_creature):
    from managers.balance.policy import BerserkerPolicy
    player = _berserker(make_creature, hp=5)       # низкий HP (не healthy)
    player.madness_active = False
    combat = _StubCombat(player, make_creature("Враг", 50, 50))  # цель не добиваема
    pick = BerserkerPolicy()._class_pick([_bloodthirst()], combat)
    assert pick is None                            # суицид-нырок → завершаем ход


def test_политика_ныряет_при_добивании(make_creature):
    from managers.balance.policy import BerserkerPolicy
    player = _berserker(make_creature, hp=5)
    player.madness_active = False
    combat = _StubCombat(player, make_creature("Враг", 6, 50))   # добиваем (≤8)
    risky = _bloodthirst()
    pick = BerserkerPolicy()._class_pick([risky], combat)
    assert pick is risky                           # добивание оправдывает нырок
