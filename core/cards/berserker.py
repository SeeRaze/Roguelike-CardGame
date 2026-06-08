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
    """Игрок теряет HP СКВОЗЬ ЩИТ (`player.lose_hp`). Для Берсерка (hp_overdraft) уводит
    в МИНУС (долг жизни). Однофункциональный кирпич «заплати кровью»: ставится ПЕРЕД
    атакующим кирпичом → удар уже кормится свежим долгом (8-ter), уча связку «нырни →
    бей». Реюзабелен любой картой «ценой HP». Вне овердрафта lose_hp клампится на 0
    (нельзя уйти ниже пола) → инертно-безопасен для не-Берсерков."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
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
        description="Платите 4(3) HP, наносите 8(11) урона. При добивании: "
                    "половина HP-долга → Forge Power.",
        effects=[SelfHarmEffect(4, 3), DamageEffect(8, 11),
                 DebtToForgeOnKillEffect(0.5, 0.5)],
        rarity=Rarity.UNCOMMON,
    )
