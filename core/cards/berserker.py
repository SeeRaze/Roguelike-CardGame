# core/cards/berserker.py
# Классовые карты Берсерка «Отрицание Смерти». Идентичность — «кровь в мощь»:
# уход в HP-долг (минус HP) кормит и урон, и Forge Power. Каждая сигнатурка = ОТДЕЛЬНАЯ
# ГРАНЬ движка (долг→урон · корм Аврала · долг→FP), но НИ ОДНА не закрывает билд сама —
# это «учителя», не замкнутый комбо-луп ([[starter-deck-reveals-passive]]). Билд игрок
# собирает по ходу забега; пассив (hp_overdraft + Аврал) — сквозная нить.
#
# Числа — ЗАГЛУШКИ; калибровка тройки = отдельный капстоун на финальном контенте.
from core.cards.base import Card, DamageEffect, DrawEffect
from core.EffectCalculator import EffectCalculator
from core.rarity import Rarity


class DebtScalingDamageEffect:
    """Урон, растущий с ГЛУБИНОЙ HP-долга игрока (signature Берсерка; движок кат.4 в
    карте — роль «Возмездия» у Воина). Урон = base + per_depth × |min(0, hp)|.

    Это АДДИТИВНЫЙ рост БАЗЫ. Универсальный множитель долга (EffectCalculator шаг 8-ter)
    композируется поверх отдельно — двойного счёта нет (там множитель, тут база). Вне
    долга (hp >= 0) → просто base, поэтому карта «учит грань» долг=мощь, но работает от
    ЛЮБОГО источника долга (Аврал / вражеский урон / самоурон) → открыто, не рельсы."""

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


class DebtPierceDamageEffect:
    """Урон с ПРОБИТИЕМ ЩИТА, растущим с ГЛУБИНОЙ HP-долга (вторая, ОТДЕЛЬНАЯ грань
    долга — «обход защиты», в пару к DebtScalingDamageEffect = «голый рост базы»).
    Тема «Коммита в обход CI»: чем глубже ты в долге, тем больше удара проходит МИМО
    щита врага (как коммит, проскользнувший мимо гейта CI).

    Развод с Эскалацией: там долг растит ЧИСЛО урона, тут число фиксировано, а долг
    растит ДОЛЮ, идущую СКВОЗЬ ЩИТ. Вне долга (hp >= 0) → пробитие 0 → обычная атака,
    полностью блокируемая щитом. Так карта «учит грань» долг=пробитие, не запирая билд.

    База прогоняется через EffectCalculator (универсальные моды + множитель долга 8-ter
    как у любой атаки — это НЕ сигнатура карты). Затем `pierce = per_depth × depth` единиц
    итогового урона уходят СКВОЗЬ щит (идиом `lose_hp` — как яд/детонации), остаток бьёт
    щит штатно (`take_damage`). Двойного счёта нет: 8-ter масштабирует ЧИСЛО, долг здесь
    решает только КУДА (сквозь щит vs в щит)."""

    def __init__(self, base_val, upgrade_val, per_depth, upgrade_per_depth):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.per_depth = per_depth
        self.upgrade_per_depth = upgrade_per_depth

    def projected_damage(self, player, is_upgraded):
        """База урона для проекции на карте (ДО общих модов). Число НЕ зависит от долга
        (долг меняет лишь пробитие, не урон) → совпадает с base; универсальные моды
        наложит preview сверх, как у обычной атаки."""
        return self.upgrade_val if is_upgraded else self.base_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        per = self.upgrade_per_depth if is_upgraded else self.per_depth
        depth = max(0, -getattr(player, "hp", 0))
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final = EffectCalculator.calculate_damage(
            player, enemy, base, gm_ref, combat_manager
        )
        pierce = min(final, per * depth)        # сколько итогового урона идёт сквозь щит
        direct = final - pierce                 # остаток бьёт щит штатно
        if pierce > 0:
            enemy.lose_hp(pierce)               # сквозь щит, как яд/детонации
        if direct > 0:
            enemy.take_damage(direct, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            if pierce > 0:
                combat_manager.add_log_message(
                    f" -> {enemy.name} получает {final} урона "
                    f"(долг {depth} → {pierce} сквозь щит)."
                )
            else:
                combat_manager.add_log_message(
                    f" -> {enemy.name} получает {final} урона."
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
                f" -> Добивание! {gained} HP-долга → +{gained} CR."
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

class AllInFinisherEffect:
    """«Финальный Деплой» — финишер ВА-БАНК (Этап 3, Rare/ЗАЛОК). Бьёт врага обычным
    числом (через EffectCalculator — универсальные моды + множитель долга 8-ter как у
    любой атаки). Затем РАСПЛАТА СРАЗУ на резолве, без грации-хода:

      • Если игрок В ЛЮБОМ HP-долге (hp < 0) И враги ВЫЖИЛИ → МГНОВЕННАЯ строгая смерть.
        Обычный долг даёт climb-out (грацию до конца хода — можно ещё добить/выйти в плюс);
        тут расплата мгновенная — не закрыл бой в минусе значит пал прямо здесь.
      • Если добил В минусе → бой выигран; пик «в коме» (|HP|→FP, hp=1) выдаст
        on_combat_won штатным путём победы — здесь его НЕ дёргаем.
      • Вне долга (hp >= 0) → обычный сильный удар, без расплаты.

    Карта САМА в минус НЕ толкает (нет SelfHarm) — это payoff за УЖЕ набранный долг:
    ныряешь Авралом/кровью, потом ва-банк закрывает бой (или убивает тебя). Ловит ТОЛЬКО
    исход ЭТОГО розыгрыша; свою отложенную строгую смерть (on_hp_debt_settle) не трогает."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def projected_damage(self, player, is_upgraded):
        return self.upgrade_val if is_upgraded else self.base_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final = EffectCalculator.calculate_damage(player, enemy, base, gm_ref, combat_manager)
        enemy.take_damage(final, attacker=player, combat_manager=combat_manager)
        if combat_manager is None:
            return
        combat_manager.add_log_message(f" -> {enemy.name} получает {final} урона (ва-банк).")
        # Расплата СРАЗУ: в минусе и бой не закрыт → мгновенная строгая смерть (без climb-out).
        if player.hp < 0 and any(e.hp > 0 for e in combat_manager.enemies):
            player.hp = player._hp_floor()       # форсируем пол-смерть
            combat_manager.add_log_message(
                "[СТАЖЁР] Финальный Деплой не закрыл бой в минусе — строгая смерть на резолве.")
            check = getattr(combat_manager, "check_player_defeat", None)
            if callable(check):
                check()                          # ИНСТАНТ: фиксируем смерть прямо сейчас


class HotfixInsuranceEffect:
    """«Костыль на Проде» — карта-СТРАХОВКА (Этап 3, Rare/ЗАЛОК, версия A). С руки вешает
    на игрока заряд статуса `hotfix`. Хук в `Creature.take_damage` (ядро): первый
    ВРАЖЕСКИЙ летал (удар, доведший до пола-смерти) съедает заряд → откат к hp=1 +
    отложенный форс-Аврал на следующий ход (firefighting). Ловит ТОЛЬКО урон через
    take_damage (вражеский удар); СВОЮ строгую смерть (lose_hp / on_hp_debt_settle) НЕ
    ловит — собственный овердрафт не застрахован. Само-баф, как Барьер/Дисциплина."""

    def __init__(self, stacks, upgrade_stacks):
        self.stacks = stacks
        self.upgrade_stacks = upgrade_stacks

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_stacks if is_upgraded else self.stacks
        player.add_status("hotfix", amount, combat_manager)
        if combat_manager is not None:
            combat_manager.add_log_message(
                f" -> Костыль на Проде: +{amount} заряд(а) хотфикса "
                "(первый вражеский летал → hp=1 + Аврал).")


def create_escalation():
    """«Эскалация» — урон растёт с глубиной HP-долга (+1/+2 за единицу долга).
    Движок кат.4 в карте: грань «долг = урон» (роль Возмездия у Воина). Бьёт базой
    вне долга → учит, не запирает. UNCOMMON."""
    return Card(
        name="Эскалация",
        cost=1,
        card_type="attack",
        description="Урон 6(8) + 1(2) за каждую единицу HP-долга.",
        effects=[DebtScalingDamageEffect(6, 8, 1, 2)],
        rarity=Rarity.UNCOMMON,
    )


def create_force_push():
    """«Форс-пуш» — дорогая мощная атака (cost 3). Нормально дорогая →
    «корм» для Аврала: каст за 0 энергии ценой HP → нырок в долг → множитель.
    Учит грань «Аврал = каст дорогого ценой HP». Обычный DamageEffect. COMMON."""
    return Card(
        name="Форс-пуш",
        cost=3,
        card_type="attack",
        description="Мощный удар: 18(24) урона.",
        effects=[DamageEffect(18, 24)],
        rarity=Rarity.COMMON,
    )


def create_refactoring():
    """«Переработка» — заплати HP (нырок в долг) → бей; при ДОБИВАНИИ часть долга
    мгновенно в Forge Power (и гасит долг). Грань «долг → FP», gated на убийство
    (награда за агрессию, не турель). Порядок кирпичей: самоурон → удар (кормится
    свежим долгом) → банк FP. UNCOMMON."""
    return Card(
        name="Переработка",
        cost=1,
        card_type="attack",
        description="Платите 7%(5%) макс. HP, наносите 8(11) урона. При добивании: "
                    "половина HP-долга → CR.",
        effects=[SelfHarmEffect(0.07, 0.05), DamageEffect(8, 11),
                 DebtToForgeOnKillEffect(0.5, 0.5)],
        rarity=Rarity.UNCOMMON,
    )


def create_crunch():
    """«Кранч» (рабочее имя — трек имён юзера) — атака-финишер. Грань движка «добил в
    долге → второе дыхание»: при ДОБИВАНИИ возвращает кровь (хил % max HP), окупая нырок
    В БОЮ сразу (а не отложенной ковкой) и НЕ ломая строгую расплату. Пара к «Переработке»
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


def create_ci_bypass():
    """«Коммит в обход CI» — атака с ПРОБИТИЕМ ЩИТА по глубине HP-долга. КЛАССОВАЯ
    СТАРТОВАЯ Стажёра (Этап 2). Грань «долг = обход защиты» (отлична от Эскалации =
    «долг = больше урона»): число урона фиксировано, но чем глубже долг, тем больше
    удара проходит МИМО щита врага. Вне долга → обычная блокируемая атака → учит грань,
    не запирает билд. Числа = ЗАГЛУШКИ. UNCOMMON."""
    return Card(
        name="Коммит в обход CI",
        cost=1,
        card_type="attack",
        description="Урон 8(11). За каждую единицу HP-долга 1(2) урона проходит "
                    "сквозь щит врага.",
        effects=[DebtPierceDamageEffect(8, 11, 1, 2)],
        rarity=Rarity.UNCOMMON,
    )


def create_burning_sprint():
    """«Горящий Спринт» — cost 0: платишь кровью (нырок в HP-долг) → добор карты.
    КЛАССОВАЯ СТАРТОВАЯ Стажёра. Грань «кровь → темп»: SelfHarm ставит свежий долг
    (кормит 8-ter и сигнатурки долга), Draw даёт топливо. Энергию НЕ даёт — осознанная
    анти-синергия с Авралом (Аврал — отдельная педаль, не складываем «бесплатный темп»).
    Развод с generic-«Кофеин-овердосом»: класс = добор 1 + синергия долга, generic =
    добор 2. Числа = ЗАГЛУШКИ. COMMON."""
    return Card(
        name="Горящий Спринт",
        cost=0,
        card_type="skill",
        description="Платите 7%(5%) макс. HP, доберите 1(2) карту.",
        effects=[SelfHarmEffect(0.07, 0.05), DrawEffect(1, 2)],
        rarity=Rarity.COMMON,
    )


def create_final_deploy():
    """«Финальный Деплой» — Rare/ЗАЛОК, КЛАССОВАЯ Стажёра. Финишер ва-банк: сильный
    удар; если ты В HP-долге и не закрыл бой — мгновенная строгая смерть на резолве
    (без грации-хода). Добил в минусе → пик «в коме» (|HP|→FP) штатным путём победы.
    Карта сама в минус НЕ толкает — payoff за уже набранный долг. Числа = ЗАГЛУШКИ."""
    return Card(
        name="Финальный Деплой",
        cost=2,
        card_type="attack",
        description="Ва-банк: 20(28) урона. Если вы в HP-долге и не закрыли бой этим "
                    "ударом — мгновенная строгая смерть (без грации-хода).",
        effects=[AllInFinisherEffect(20, 28)],
        rarity=Rarity.RARE,
    )


def create_prod_crutch():
    """«Костыль на Проде» — Rare/ЗАЛОК, КЛАССОВАЯ Стажёра. Карта-страховка (версия A):
    вешает заряд `hotfix`. Первый ВРАЖЕСКИЙ летал → hp=1 + форс-Аврал на след. ход,
    заряд съедается. Свою строгую смерть НЕ ловит (только вражеский удар). Числа =
    ЗАГЛУШКИ."""
    return Card(
        name="Костыль на Проде",
        cost=1,
        card_type="skill",
        description="Страховка: 1(2) заряд хотфикса. Первый вражеский смертельный удар "
                    "не убивает — откат к 1 HP и Аврал на следующий ход (заряд тратится).",
        effects=[HotfixInsuranceEffect(1, 2)],
        rarity=Rarity.RARE,
    )
