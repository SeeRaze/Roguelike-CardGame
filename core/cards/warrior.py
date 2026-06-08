# core/cards/warrior.py
# Классовые карты Воина. Идентичность класса (С56, передел) — «Дисциплина-как-ресурс»:
# Воин копит Дисциплину обороной (пассив: держишь строй → +1; +урон ПОКА держишь,
# EffectCalculator шаг 2d), а сигнатурки её ТРАТЯТ (сжигают стаки) в разовый пик —
# урон («Карающий строй») или щит-стену («Стена щитов»). Выбор «копи vs слей».
# Ось класса = ВЫЖИВАЕМОСТЬ, поэтому НИ ОДНА сигнатурка не генерит FP (в отличие от
# Берсерка); связь с золотом-выживаемостью — отдельная эконом-дуга ([[economy-axis-trinity]]).
#
# Каждая грань — «учитель», не замкнутый луп: спендеры вознаграждают Дисциплину от
# ЛЮБОГО источника (пассив/карты), билд игрок собирает по ходу забега.
#
# Прежняя ось «защита=атака» (Возмездие = щит→урон, Барьер) сохранена как ДРАФТ-ПУЛ
# класса (ниже) — достижима, но вне стартера. Числа = ЗАГЛУШКИ под капстоун-калибровку.
from core.cards.base import Card, ShieldEffect, BarrierEffect
from core.EffectCalculator import EffectCalculator
from core.rarity import Rarity


# ─── Кирпичи движка Дисциплины (С56) ──────────────────────────────────────────
class DisciplineBurstDamageEffect:
    """Грань «Дисциплина → бурст» (роль Возмездия в новой идентичности). Сжигает ВСЮ
    Дисциплину игрока и наносит урон = base + per×(сожжено). Трата ОБНУЛЯЕТ стак ДО
    EffectCalculator → шаг 2d (+N урона за стак) не задваивает: карта САМА и есть payoff
    накопленного. Вне Дисциплины → просто base, поэтому учит грань, работая от любого
    источника стаков. Урон через EffectCalculator (уязвимость/Заточка учитываются)."""

    def __init__(self, base_val, upgrade_val, per_disc, upgrade_per_disc):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.per_disc = per_disc
        self.upgrade_per_disc = upgrade_per_disc

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        per = self.upgrade_per_disc if is_upgraded else self.per_disc
        spent = max(0, getattr(player, "discipline", 0))
        player.set_status("discipline", 0)          # сжечь стак ДО расчёта (без задвоя 2d)
        amount = base + per * spent
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final = EffectCalculator.calculate_damage(
            player, enemy, amount, gm_ref, combat_manager
        )
        enemy.take_damage(final, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Карающий строй: {final} урона "
                f"(сожжено {spent} Дисциплины → +{per * spent})."
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
                f" -> Стена щитов: +{amount} щита "
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
                f" -> Стойка: +{amount} Дисциплины (всего {player.discipline})."
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
                    " -> Возмездие: нет щита для удара!"
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
                    f" -> Возмездие: {base} урона всем врагам "
                    f"({len(targets)}) от щита {player.shield}. "
                    f" [ВОИН] +{heal} HP (Боевой дух)!"
                )
            else:
                combat_manager.add_log_message(
                    f" -> Возмездие: {base} урона всем врагам "
                    f"({len(targets)}) от щита {player.shield}."
                )


def create_retribution():
    """«Возмездие» — урон = текущий щит Воина (улучшение: 130% щита). Щит не
    тратится. Классовая карта Воина (защита = атака). Стоит 1 энергии: щит
    сбрасывается до 30% каждый ход, поэтому копить-и-бить нужно в один ход —
    дешёвая стоимость оставляет энергию на накопление щита."""
    return Card(
        name="Возмездие",
        cost=1,
        card_type="attack",
        description="Урон ВСЕМ врагам = текущему щиту (130% при улучшении). "
                    "Щит не тратится.",
        effects=[ShieldDamageEffect(1.0, 1.3)],
        rarity=Rarity.UNCOMMON,
    )


def create_steel_barricade():
    """«Стальной заслон» — Барьер 2(3). Чистый энейблер движка Воина:
    каждый стак барьера = +1 щита в начале КАЖДОГО хода (не сгорает).
    Компаунд: барьер копится → щит растёт → Возмездие бьёт сильнее."""
    return Card(
        name="Стальной заслон",
        cost=1,
        card_type="skill",
        description="Барьер 2(3): несгораемый щит каждый ход.",
        effects=[BarrierEffect(2, 3)],
        rarity=Rarity.COMMON,
    )


def create_bastion():
    """«Бастион» — щит 6(9) + Барьер 2(3). Гибрид: защищает сейчас
    И строит несгораемый щит на будущие ходы."""
    return Card(
        name="Бастион",
        cost=2,
        card_type="defense",
        description="Щит 6(9). Барьер 2(3): несгораемый щит каждый ход.",
        effects=[ShieldEffect(6, 9), BarrierEffect(2, 3)],
        rarity=Rarity.UNCOMMON,
    )
