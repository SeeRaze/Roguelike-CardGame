# core/cards/warrior.py
# Классовые карты Воина. Идентичность класса (С56, передел) — «Дисциплина-как-ресурс»:
# Воин копит Дисциплину обороной (пассив: держишь строй → +1; +урон ПОКА держишь,
# EffectCalculator шаг 2d), а сигнатурки её ТРАТЯТ (сжигают стаки) в разовый пик —
# урон («Критический баг») или щит-стену («Релиз-кандидат»). Выбор «копи vs слей».
# Ось класса = ВЫЖИВАЕМОСТЬ, поэтому НИ ОДНА сигнатурка не генерит FP (в отличие от
# Берсерка); связь с золотом-выживаемостью — отдельная эконом-дуга ([[economy-axis-trinity]]).
#
# Каждая грань — «учитель», не замкнутый луп: спендеры вознаграждают Дисциплину от
# ЛЮБОГО источника (пассив/карты), билд игрок собирает по ходу забега.
#
# Прежняя ось «защита=атака» (Регрессионка = щит→урон, Барьер) сохранена как ДРАФТ-ПУЛ
# класса (ниже) — достижима, но вне стартера. Числа = ЗАГЛУШКИ под капстоун-калибровку.
from core.cards.base import Card, DamageEffect, ShieldEffect, BarrierEffect, HealEffect, StatusEffect
from core.EffectCalculator import EffectCalculator
from core.rarity import Rarity


# ─── Кирпичи движка Дисциплины (С56) ──────────────────────────────────────────
class DisciplineBurstDamageEffect:
    """Грань «Дисциплина → бурст» (роль Регрессионки в новой идентичности). Сжигает ВСЮ
    Дисциплину игрока и наносит урон = base × (1 + mult×сожжено) — МУЛЬТИПЛИКАТИВНО
    от стака (С57: флат +N/стак тонул против экспоненты врага в эндгейме; множитель
    масштаб-инвариантен — пик растёт с накоплением и домножается forge/уязвимостью).
    Трата ОБНУЛЯЕТ стак ДО EffectCalculator → шаг 2d (+N урона за стак) не задваивает.
    Вне Дисциплины → просто base (множитель ×1). Числа = ЗАГЛУШКИ под капстоун."""

    def __init__(self, base_val, upgrade_val, mult_per, upgrade_mult_per):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.mult_per = mult_per                 # доля множителя за каждый сожжённый стак
        self.upgrade_mult_per = upgrade_mult_per

    def projected_damage(self, player, is_upgraded):
        """База урона ДО общих модификаторов (для проекции на карте) = base × текущий
        множитель Дисциплины. Совпадает с amount в execute → preview == фактический удар."""
        base = self.upgrade_val if is_upgraded else self.base_val
        mult_per = self.upgrade_mult_per if is_upgraded else self.mult_per
        spent = max(0, getattr(player, "discipline", 0)) if player else 0
        return int(base * (1.0 + mult_per * spent))

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        mult_per = self.upgrade_mult_per if is_upgraded else self.mult_per
        spent = max(0, getattr(player, "discipline", 0))
        player.set_status("discipline", 0)          # сжечь стак ДО расчёта (без задвоя 2d)
        mult = 1.0 + mult_per * spent
        amount = int(base * mult)
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final = EffectCalculator.calculate_damage(
            player, enemy, amount, gm_ref, combat_manager
        )
        enemy.take_damage(final, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Критический баг: {final} урона "
                f"(сожжено {spent} Дисциплины → ×{mult:.2f})."
            )


class DisciplineToShieldEffect:
    """Грань «Дисциплина → выживаемость» (ось класса). Сжигает ВСЮ Дисциплину и даёт
    щит = base + per×(сожжено). Оборонный payoff накопителя: держал строй — конвертируй
    в стену сейчас. Мини-хил компонуется отдельным HealEffect в фабрике."""

    def __init__(self, base_val, upgrade_val, per_disc, upgrade_per_disc):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.per_disc = per_disc
        self.upgrade_per_disc = upgrade_per_disc

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        per = self.upgrade_per_disc if is_upgraded else self.per_disc
        spent = max(0, getattr(player, "discipline", 0))
        player.set_status("discipline", 0)
        amount = base + per * spent
        player.gain_shield(amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Релиз-кандидат: +{amount} щита "
                f"(сожжено {spent} Дисциплины → +{per * spent})."
            )


class DisciplineGainEffect:
    """Грань-билдер: +N Дисциплины напрямую (учит «оборона = накопитель», ускоряет
    пассив). Тонкий кирпич; обычно компонуется со ShieldEffect в защитной карте."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.add_status("discipline", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Тест-план: +{amount} Дисциплины (всего {player.discipline})."
            )


class DisciplineScaledShieldEffect:
    """Грань «компаунд» (С-добор Тестировщика): щит = base + per×(текущая Дисциплина),
    Дисциплину НЕ тратит. Пара-противовес спендеру «Релиз-кандидат» (тот СЖИГАЕТ стак):
    выбор «копить (Чеклист читает, не жжёт) vs слить (Релиз-кандидат жжёт в пик)».
    Зеркало Маговой «Сгенерить фичу» (читает Мастерство) — трио классов симметрично.
    ⚠️ Баланс: payoff-за-стак ДОЛЖЕН быть слабее спендера, иначе выбор «копи/слей»
    умирает (Дисциплина = чистый value). Числа = ЗАГЛУШКИ под капстоун."""

    def __init__(self, base_val, upgrade_val, per_disc, upgrade_per_disc):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.per_disc = per_disc
        self.upgrade_per_disc = upgrade_per_disc

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        per = self.upgrade_per_disc if is_upgraded else self.per_disc
        stacks = max(0, getattr(player, "discipline", 0))
        amount = base + per * stacks
        player.gain_shield(amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Чеклист: +{amount} щита "
                f"(Дисциплина {stacks} НЕ тратится, +{per * stacks})."
            )


class ShieldGatedDrawEffect:
    """Условный темп: если у игрока есть щит (держит оборону) → бесплатный добор N карт.
    Награда за стабильное состояние (off-axis утилита, прокрутка колоды). Без щита —
    ничего. Числа = ЗАГЛУШКИ под капстоун."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        n = self.upgrade_val if is_upgraded else self.base_val
        has_shield = getattr(player, "shield", 0) > 0
        if has_shield and combat_manager is not None and \
                hasattr(combat_manager, "deck_manager"):
            drew = combat_manager.deck_manager.draw_cards(n)
            combat_manager.add_log_message(
                f" -> Отчёт о баге: щит держит → бесплатный добор {drew} карт(ы)."
            )
        elif combat_manager:
            combat_manager.add_log_message(
                " -> Отчёт о баге: нет щита — добора нет."
            )


class HeldFormBonusShieldEffect:
    """Бонус-щит, если игрок НАЧАЛ ход со щитом (держал строй) — иначе ничего. Награждает
    поддержание оборонного лупа (атака, что его не ломает). Читает флаг пассива
    `_started_turn_with_shield`. Числа = ЗАГЛУШКИ."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if not getattr(player, "_started_turn_with_shield", False):
            if combat_manager:
                combat_manager.add_log_message(
                    " -> Смоук-тест: строй не держался — бонус-щита нет."
                )
            return
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.gain_shield(amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Смоук-тест: строй держался → +{amount} щита."
            )


class FreezeReleaseEffect:
    """«Заморозка релиза» (#4): разово 100% перенос текущего щита на след. ход (вместо
    штатных 50% Железного задела) + N Дисциплины на следующем старте хода. Реализация =
    отложенные флаги пассива (_pending_full_carry / _pending_freeze_bonus). Карта EXHAUST
    (один раз за бой) — иначе бесконечная стена. Числа = ЗАГЛУШКИ."""

    def __init__(self, disc_base, disc_upgrade):
        self.disc_base = disc_base
        self.disc_upgrade = disc_upgrade

    def execute(self, player, enemy, combat_manager, is_upgraded):
        player._pending_full_carry = True
        bonus = self.disc_upgrade if is_upgraded else self.disc_base
        player._pending_freeze_bonus = getattr(player, "_pending_freeze_bonus", 0) + bonus
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Заморозка релиза: след. ход — 100% переноса щита + {bonus} Дисциплины."
            )


class ShieldDamageEffect:
    """Урон ПО ВСЕМ живым врагам, равный текущему щиту игрока × коэффициент.
    Щит НЕ тратится — это payoff танка: чем больше накопил защиты, тем сильнее
    бьёт. AoE решает главную проблему Воина — мультивражеские этажи (9+).
    Урон проходит через EffectCalculator (ярость/уязвимость учитываются).
    Также восстанавливает игроку HP = 30% нанесённого урона (sustain танка)."""

    HEAL_RATIO = 0.5  # доля урона, возвращаемая как лечение

    def __init__(self, base_ratio, upgrade_ratio):
        self.base_ratio    = base_ratio
        self.upgrade_ratio = upgrade_ratio

    def execute(self, player, enemy, combat_manager, is_upgraded):
        ratio = self.upgrade_ratio if is_upgraded else self.base_ratio
        base  = int(player.shield * ratio)
        if base <= 0:
            if combat_manager:
                combat_manager.add_log_message(
                    " -> Регрессионка: нет щита для удара!"
                )
            return
        gm_ref  = combat_manager.gm if combat_manager is not None else None
        targets = ([e for e in combat_manager.enemies if e.hp > 0]
                   if combat_manager else [enemy])
        total_dmg = 0
        for tgt in targets:
            final_dmg = EffectCalculator.calculate_damage(
                player, tgt, base, gm_ref, combat_manager
            )
            tgt.take_damage(final_dmg, attacker=player, combat_manager=combat_manager)
            total_dmg += final_dmg
        if combat_manager:
            heal = int(total_dmg * self.HEAL_RATIO)
            if heal > 0:
                player.heal(heal, combat_manager)
                combat_manager.add_log_message(
                    f" -> Регрессионка: {base} урона всем врагам "
                    f"({len(targets)}) от щита {player.shield}. "
                    f" [ТЕСТИРОВЩИК] +{heal} HP (Боевой дух)!"
                )
            else:
                combat_manager.add_log_message(
                    f" -> Регрессионка: {base} урона всем врагам "
                    f"({len(targets)}) от щита {player.shield}."
                )


# ─── Фабрики сигнатурок Дисциплины (С56). Числа = ЗАГЛУШКИ под капстоун ─────────
def create_critical_bug():
    """«Критический баг» — сжигает ВСЮ Дисциплину → урон base ×(1 + 30%(40%) за стак).
    Грань «Дисц → бурст» (роль Регрессионки). Мультипликативно (С57): пик растёт со стаком
    и домножается forge/уязвимостью, не тонет в эндгейме. UNCOMMON."""
    return Card(
        name="Критический баг",
        cost=1,
        card_type="attack",
        description="Сжечь всю Дисциплину: урон 6(9) ×(1 + 30%(40%) за сожжённый стак).",
        effects=[DisciplineBurstDamageEffect(6, 9, 0.30, 0.40)],
        rarity=Rarity.UNCOMMON,
    )


def create_release_candidate():
    """«Релиз-кандидат» — сжигает ВСЮ Дисциплину → щит 5(8) + 1(2) за стак + хил 3(5).
    Грань «Дисц → выживаемость» (ось класса). Оборонный payoff накопителя. UNCOMMON."""
    return Card(
        name="Релиз-кандидат",
        cost=1,
        card_type="defense",
        description="Сжечь всю Дисциплину: щит 5(8) + 1(2) за стак. Хил 3(5).",
        effects=[DisciplineToShieldEffect(5, 8, 1, 2), HealEffect(3, 5)],
        rarity=Rarity.UNCOMMON,
    )


def create_test_plan():
    """«Тест-план» — щит 5(8) + сразу +2(3) Дисциплины. Грань-билдер: учит «оборона =
    накопитель», ускоряет пассив. В драфт-пуле (не в стартере). COMMON."""
    return Card(
        name="Тест-план",
        cost=1,
        card_type="skill",
        description="Щит 5(8). +2(3) Дисциплины.",
        effects=[ShieldEffect(5, 8), DisciplineGainEffect(2, 3)],
        rarity=Rarity.COMMON,
    )


def create_checklist_drafting():
    """«Написание чеклиста» — щит base + per×Дисциплина, Дисциплину НЕ тратит.
    Компаунд-payoff накопителя (пара к спендеру «Релиз-кандидат», как Маг «Сгенерить
    фичу»). Без хуков в ядро. Тематика: длиннее чеклист → собраннее тестировщик.
    UNCOMMON. Числа = ЗАГЛУШКИ."""
    return Card(
        name="Написание чеклиста",
        cost=1,
        card_type="defense",
        description="Щит 4(6) + 1(2) за каждый стак Дисциплины. Дисциплина не тратится.",
        effects=[DisciplineScaledShieldEffect(4, 6, 1, 2)],
        rarity=Rarity.UNCOMMON,
    )


def create_bug_report():
    """«Отчёт о баге» — legacy 3(4) на врага; если у игрока есть щит → бесплатный добор 1.
    Off-axis утилита (legacy-DoT + прокрутка колоды) — одобрено как кросс-классовая
    вариативность (не всё замыкать строго в пассив). Без хуков в ядро. UNCOMMON. Заглушки."""
    return Card(
        name="Отчёт о баге",
        cost=1,
        card_type="skill",
        description="Накладывает Legacy-код 3(4) на врага. "
                    "Если у вас есть щит — бесплатно доберите 1 карту.",
        effects=[StatusEffect("legacy", 3, 4), ShieldGatedDrawEffect(1, 1)],
        rarity=Rarity.UNCOMMON,
    )


def create_smoke_test():
    """«Смоук-тест» — урон 5(7); если начал ход со щитом (держал строй) → ещё +4(6) щита.
    Атака, которая НЕ ломает оборонный луп Тестировщика. Имя без коллизии со спящей
    «Регрессонкой». Трогает пассив (флаг _started_turn_with_shield). COMMON. Заглушки."""
    return Card(
        name="Смоук-тест",
        cost=1,
        card_type="attack",
        description="Урон 5(7). Если вы начали ход со щитом — получите ещё 4(6) щита.",
        effects=[DamageEffect(5, 7), HeldFormBonusShieldEffect(4, 6)],
        rarity=Rarity.COMMON,
    )


def create_release_freeze():
    """«Заморозка релиза» — одноходовый ломатель: на след. ход 100% перенос щита (вместо
    50% Железного задела) + 2(3) Дисциплины. EXHAUST (изгнание до конца боя) закрывает
    бесконечный оборонный луп — играется раз за бой. LEGENDARY, cost 2. Заглушки."""
    return Card(
        name="Заморозка релиза",
        cost=2,
        card_type="skill",
        description="Следующий ход: весь текущий щит переносится (100%) + 2(3) Дисциплины. "
                    "Изгоняется после игры.",
        effects=[FreezeReleaseEffect(2, 3)],
        rarity=Rarity.LEGENDARY,
        exile=True,
    )


def create_regression_test():
    """«Регрессионка» — урон = текущий щит Тестировщика (улучшение: 130% щита). Щит не
    тратится. Классовая карта Тестировщика (защита = атака). Стоит 1 энергии: щит
    сбрасывается до 30% каждый ход, поэтому копить-и-бить нужно в один ход —
    дешёвая стоимость оставляет энергию на накопление щита."""
    return Card(
        name="Регрессионка",
        cost=1,
        card_type="attack",
        description="Урон ВСЕМ врагам = текущему щиту (130% при улучшении). "
                    "Щит не тратится.",
        effects=[ShieldDamageEffect(1.0, 1.3)],
        rarity=Rarity.UNCOMMON,
    )


def create_steel_barricade():
    """«Failover» — Барьер 2(3). Чистый энейблер движка Воина:
    каждый стак барьера = +1 щита в начале КАЖДОГО хода (не сгорает).
    Компаунд: барьер копится → щит растёт → Регрессионка бьёт сильнее.
    Резервный канал, который всегда подхватывает нагрузку."""
    return Card(
        name="Failover",
        cost=1,
        card_type="skill",
        description="Барьер 2(3): несгораемый щит каждый ход.",
        effects=[BarrierEffect(2, 3)],
        rarity=Rarity.COMMON,
    )


def create_bastion():
    """«Кластер» — щит 6(9) + Барьер 2(3). Гибрид: защищает сейчас
    И строит несгораемый щит на будущие ходы. Узлы держат нагрузку
    разом и резервируют ёмкость на будущие отказы."""
    return Card(
        name="Кластер",
        cost=2,
        card_type="defense",
        description="Щит 6(9). Барьер 2(3): несгораемый щит каждый ход.",
        effects=[ShieldEffect(6, 9), BarrierEffect(2, 3)],
        rarity=Rarity.UNCOMMON,
    )
