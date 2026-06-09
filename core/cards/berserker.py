# core/cards/berserker.py
# Классовые карты Берсерка «Отрицание Смерти». Идентичность — «кровь в мощь»:
# уход в HP-долг (минус HP) кормит и урон, и Forge Power. Каждая сигнатурка = ОТДЕЛЬНАЯ
# ГРАНЬ движка (долг→урон · корм Безумия · долг→FP), но НИ ОДНА не закрывает билд сама —
# это «учителя», не замкнутый комбо-луп ([[starter-deck-reveals-passive]]). Билд игрок
# собирает по ходу забега; пассив (hp_overdraft + Безумие) — сквозная нить.
#
# Числа — ЗАГЛУШКИ; калибровка тройки = отдельный капстоун на финальном контенте.
from core.cards.base import Card, DamageEffect
from core.EffectCalculator import EffectCalculator
from core.rarity import Rarity


class DebtScalingDamageEffect:
    """Урон, растущий с ГЛУБИНОЙ HP-долга игрока (signature Берсерка; движок кат.4 в
    карте — роль «Возмездия» у Воина). Урон = base + per_depth × |min(0, hp)|.

    Это АДДИТИВНЫЙ рост БАЗЫ. Универсальный множитель долга (EffectCalculator шаг 8-ter)
    композируется поверх отдельно — двойного счёта нет (там множитель, тут база). Вне
    долга (hp >= 0) → просто base, поэтому карта «учит грань» долг=мощь, но работает от
    ЛЮБОГО источника долга (Безумие / вражеский урон / самоурон) → открыто, не рельсы."""

    def __init__(self, base_val, upgrade_val, per_depth, upgrade_per_depth):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.per_depth = per_depth
        self.upgrade_per_depth = upgrade_per_depth

    def projected_damage(self, player, is_upgraded):
        """База урона ДО общих модификаторов (для проекции на карте) = base + бонус за
        текущую глубину HP-долга. Совпадает с amount в execute → preview == удар.
        (Универсальный множитель долга 8-ter EffectCalculator наложит preview сверх.)"""
        base = self.upgrade_val if is_upgraded else self.base_val
        per = self.upgrade_per_depth if is_upgraded else self.per_depth
        depth = max(0, -getattr(player, "hp", 0)) if player else 0
        return base + per * depth

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        per = self.upgrade_per_depth if is_upgraded else self.per_depth
        depth = max(0, -getattr(player, "hp", 0))
        amount = base + per * depth
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final = EffectCalculator.calculate_damage(
            player, enemy, amount, gm_ref, combat_manager
        )
        enemy.take_damage(final, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            bonus = per * depth
            combat_manager.add_log_message(
                f" -> {enemy.name} получает {final} урона "
                f"(долг {depth} → +{bonus} базы)."
            )


class SelfHarmEffect:
    """Игрок теряет % MAX HP СКВОЗЬ ЩИТ (`player.lose_hp`). Для Берсерка (hp_overdraft)
    уводит в МИНУС (долг жизни). Однофункциональный кирпич «заплати кровью»: ставится ПЕРЕД
    атакующим кирпичом → удар уже кормится свежим долгом (8-ter), уча связку «нырни → бей».
    Реюзабелен любой картой «ценой HP». Вне овердрафта lose_hp клампится на 0 → инертно-
    безопасен для не-Берсерков.

    С57: цена в ПРОЦЕНТАХ от max HP, не флат → нырок растёт с max HP (масштаб-инвариантно
    к экспоненте, [[balance-curve-framework]]). На 60 HP ≡ прежним флат-числам (0.07·60≈4)."""

    def __init__(self, base_pct, upgrade_pct):
        self.base_pct = base_pct
        self.upgrade_pct = upgrade_pct

    def execute(self, player, enemy, combat_manager, is_upgraded):
        pct = self.upgrade_pct if is_upgraded else self.base_pct
        amount = int(pct * getattr(player, "max_hp", 0))
        lost = player.lose_hp(amount)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Вы платите {lost} HP кровью (нырок в долг)."
            )


class DebtToForgeOnKillEffect:
    """Если ЭТОЙ картой ДОБИТ враг И игрок в HP-долге → часть долга мгновенно
    конвертируется в Forge Points, и НА СТОЛЬКО ЖЕ гасится долг (hp → к 0): долг
    «потрачен» в ковку. Грань долг→FP в карте; GATED НА УБИЙСТВО — награда за
    АГРЕССИЮ (добил), а не кнопка-выживания. Полный пик |долг|→FP остаётся на
    `on_combat_won` (победа в коме), и он берёт ОСТАТОК долга → двойного счёта нет.
    Ставится ПОСЛЕ атакующего кирпича."""

    def __init__(self, ratio, upgrade_ratio):
        self.ratio = ratio
        self.upgrade_ratio = upgrade_ratio

    def execute(self, player, enemy, combat_manager, is_upgraded):
        ratio = self.upgrade_ratio if is_upgraded else self.ratio
        if enemy is None or enemy.hp > 0:
            return                              # враг жив → не добили
        hp = getattr(player, "hp", 0)
        if hp >= 0:
            return                              # нет долга → нечего конвертировать
        gained = int(-hp * ratio)
        if gained <= 0:
            return
        player.forge_points = getattr(player, "forge_points", 0) + gained
        player.hp += gained                     # гасим часть долга (к 0)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Добивание! {gained} HP-долга → +{gained} FP."
            )


class LifestealOnKillEffect:
    """Если ЭТОЙ картой ДОБИТ враг → игрок лечится на heal_pct × MAX HP. Для Берсерка в
    долге это CLIMB-OUT: heal поднимает hp от минуса к 0 (и выше). НЕМЕДЛЕННОЕ поощрение
    за добивание В БОЮ («закрыл тикет → второе дыхание») — окупает нырок СРАЗУ, не дожидаясь
    ковки, и НЕ ломает строгую расплату (надо именно ДОБИТЬ, не турель). Грань «добивание →
    сустейн», отлична от blood_thirst (та даёт FP). Ставится ПОСЛЕ атакующего кирпича.
    Хил в % max HP → масштаб-инвариантно (растёт с пулом, [[balance-curve-framework]])."""

    def __init__(self, heal_pct, upgrade_pct):
        self.heal_pct = heal_pct
        self.upgrade_pct = upgrade_pct

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if enemy is None or enemy.hp > 0:
            return                              # враг жив → не добили
        pct = self.upgrade_pct if is_upgraded else self.heal_pct
        amount = int(pct * getattr(player, "max_hp", 0))
        if amount <= 0:
            return
        healed = player.heal(amount, combat_manager)
        if combat_manager and healed:
            combat_manager.add_log_message(
                f" -> Добивание! Второе дыхание: +{healed} HP."
            )


# ─── Фабрики сигнатурных карт ────────────────────────────────────────────────
# Числа = ЗАГЛУШКИ под калибровку (подзадача 4 / капстоун). Каждая карта учит ОДНУ
# грань движка, ни одна не закрывает билд сама ([[starter-deck-reveals-passive]]).

def create_blood_rage():
    """«Кровавая ярость» — урон растёт с глубиной HP-долга (+1/+2 за единицу долга).
    Движок кат.4 в карте: грань «долг = урон» (роль Возмездия у Воина). Бьёт базой
    вне долга → учит, не запирает. UNCOMMON."""
    return Card(
        name="Кровавая ярость",
        cost=1,
        card_type="attack",
        description="Урон 6(8) + 1(2) за каждую единицу HP-долга.",
        effects=[DebtScalingDamageEffect(6, 8, 1, 2)],
        rarity=Rarity.UNCOMMON,
    )


def create_reckless_blow():
    """«Безрассудный удар» — дорогая мощная атака (cost 3). Нормально дорогая →
    «корм» для Безумия: каст за 0 энергии ценой HP → нырок в долг → множитель.
    Учит грань «Безумие = каст дорогого ценой HP». Обычный DamageEffect. COMMON."""
    return Card(
        name="Безрассудный удар",
        cost=3,
        card_type="attack",
        description="Мощный удар: 18(24) урона.",
        effects=[DamageEffect(18, 24)],
        rarity=Rarity.COMMON,
    )


def create_blood_thirst():
    """«Жажда крови» — заплати HP (нырок в долг) → бей; при ДОБИВАНИИ часть долга
    мгновенно в Forge Power (и гасит долг). Грань «долг → FP», gated на убийство
    (награда за агрессию, не турель). Порядок кирпичей: самоурон → удар (кормится
    свежим долгом) → банк FP. UNCOMMON."""
    return Card(
        name="Жажда крови",
        cost=1,
        card_type="attack",
        description="Платите 7%(5%) макс. HP, наносите 8(11) урона. При добивании: "
                    "половина HP-долга → Forge Power.",
        effects=[SelfHarmEffect(0.07, 0.05), DamageEffect(8, 11),
                 DebtToForgeOnKillEffect(0.5, 0.5)],
        rarity=Rarity.UNCOMMON,
    )


def create_crunch():
    """«Кранч» (рабочее имя — трек имён юзера) — атака-финишер. Грань движка «добил в
    долге → второе дыхание»: при ДОБИВАНИИ возвращает кровь (хил % max HP), окупая нырок
    В БОЮ сразу (а не отложенной ковкой) и НЕ ломая строгую расплату. Пара к «Жажде крови»
    (та → FP, эта → HP-сустейн): кормит ЦЕПОЧКУ нырков (добил → откачался → нырнул снова).
    Бьёт и без добивания → учит грань, не запирает. COMMON."""
    return Card(
        name="Кранч",
        cost=1,
        card_type="attack",
        description="Наносите 7(10) урона. При добивании: восстановите 20%(25%) макс. HP "
                    "(второе дыхание — выход из долга).",
        effects=[DamageEffect(7, 10), LifestealOnKillEffect(0.20, 0.25)],
        rarity=Rarity.COMMON,
    )
