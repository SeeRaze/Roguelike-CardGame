# managers/balance/policy.py
# Политика бота: КАК выбирать карту и КОГДА жать классовую способность.
# Дефолт-бот играл случайно и не жал способности — из-за этого классы (особенно
# Призыватель) мерились искусственно слабыми. Политика делает бота КОМПЕТЕНТНЫМ:
# он играет к ядру своего класса. Цель — честный замер, а не оптимальный ИИ.
#
# Синергийный слой (общий для всех классов): синергийные карты (Шок/Раскол/Поток/
# детонаторы) лежат в generic-пуле, поэтому их получает как награду ЛЮБОЙ класс.
# Случайная игра занижает их ценность (бот тащит энейблеры как мусор) → симулятор
# искусственно роняет глубокие классы. `_synergy_pick` пилотирует эти карты
# осмысленно. Он срабатывает ТОЛЬКО при наличии синергии в руке; иначе выбор падает
# в `_class_pick` (random или класс-специфика) — несинергийные прогоны не меняются.
import random

from core.cards.base import (
    ShieldEffect, DamageEffect, StatusEffect, DetonateEffect,
)
from core.cards.air import FlowEffect
from core.cards.summon import SummonEffect
from core.cards.warrior import ShieldDamageEffect

# --- Пороги «компетентности» (НЕ игровой баланс, а качество игры бота) ---
# Жать реактивную способность, когда набралось осмысленно много стаков/щита.
_WARRIOR_SHIELD_MIN     = 8   # «Щитовой удар»: удар = 50% щита
_WARRIOR_RETRIBUTION_MIN = 10 # «Возмездие»: придержать, пока щит не накоплен
_ROGUE_BLEED_MIN        = 8   # «Вскрытие»: удвоить кровотечение (ценой -1 энергии)
_DRUID_POISON_MIN       = 10  # «Токсичный взрыв»: снять весь яд разом
_MAGE_ELEMENTAL_MIN     = 4   # «Стихийный барьер»: щит = стихийные стаки * 3
# Берсерк «Безумие» = ставка дисперсии: дамп руки за 0 энергии ценой HP (нырок в
# минус → множитель урона), НО конец хода в минусе без победы = строгая смерть.
# Компетентный пилот ныряет ТОЛЬКО когда оба условия сошлись: (1) полный буфер HP,
# чтобы пережить нырок, И (2) залп добиваем (суммарный HP врагов ≤ доли max_hp) —
# иначе нырок не окупится киллом. Слепой газ@0.6 был суицидом (мерил класс гласс-
# пушкой-ловушкой); умный газ раскручивает движок |HP|→FP (см. память glasscannon).
_BERSERK_HP_FRACTION    = 0.9 # нырять только с почти полным буфером HP
_BERSERK_KILLABLE_RATIO = 0.6 # ...и только когда залп врагов добиваем (≤ доля max_hp)

# Стихийные статусы для подсчёта (как в MageAbility).
_ELEMENTAL_STATUSES = ("ignited", "wet", "poison")


def _ability(combat):
    """Готовая к активации способность игрока или None."""
    ab = getattr(combat.player, "active_ability", None)
    return ab if (ab and ab.is_ready()) else None


# ─── Синергийный слой: детекторы карт (по ТИПУ эффекта — устойчиво к новым картам) ──

def _has_effect(card, effect_cls) -> bool:
    """В карте есть эффект указанного типа."""
    return any(isinstance(e, effect_cls) for e in card.effects)


def _status_types(card) -> set:
    """Множество status_type всех StatusEffect карты."""
    return {e.status_type for e in card.effects if isinstance(e, StatusEffect)}


def _is_pure_enabler(card, status_type) -> bool:
    """Карта-энейблер: вешает нужный статус и НЕ наносит урон (чистый сетап,
    сама по себе бесполезна — её и тащит как мусор случайный бот)."""
    return status_type in _status_types(card) and not _has_effect(card, DamageEffect)


def _ready_detonation(target) -> bool:
    """У цели готова хотя бы одна детонация (все requires-статусы > 0)."""
    from core.DetonationRegistry import all_detonations
    return any(
        all(target.get_status(req) > 0 for req in det["requires"])
        for det in all_detonations().values()
    )


class BotPolicy:
    """База: случайный выбор карты, способность не используется.
    Подклассы переопределяют `_class_pick`/`on_turn_*`."""

    def pick_card(self, playable, combat):
        """Шаблон: сначала синергия (общая для всех), затем класс-специфика."""
        synergy = self._synergy_pick(playable, combat)
        if synergy is not None:
            return synergy
        return self._class_pick(playable, combat)

    def _class_pick(self, playable, combat):
        """Класс-специфичный/дефолтный выбор. База — случайно."""
        return random.choice(playable)

    def _synergy_pick(self, playable, combat):
        """Осмысленная игра синергийных карт из generic-пула. Возвращает карту
        или None (тогда выбор делает `_class_pick`). Приоритет — по «отдаче»:
        детонация (мгновенный бурст) → сетап Раскола/Шока → темпо Потока."""
        target = combat.get_target_enemy()
        if target is None:
            return None

        # 1) Готовая детонация на цели — подрываем (наибольшая отдача).
        if _ready_detonation(target):
            detonators = [c for c in playable if _has_effect(c, DetonateEffect)]
            if detonators:
                return detonators[0]

        # 2) Сетап Раскола: только пока у цели есть щит (Раскол множит урон ×3,
        #    лишь пока щит > 0) и Раскол ещё не наложен.
        if target.shield > 0 and target.get_status("shatter") == 0:
            enablers = [c for c in playable if _is_pure_enabler(c, "shatter")]
            if enablers:
                return enablers[0]

        # 3) Сетап Шока: Шок не тикает и копится — любой последующий удар дренит
        #    +3 урона/заряд. Вешаем, пока на цели нет заряда.
        if target.get_status("shock") == 0:
            enablers = [c for c in playable if _is_pure_enabler(c, "shock")]
            if enablers:
                return enablers[0]

        # 4) Темпо Потока: чистый энейблер Потока удешевляет остаток руки —
        #    играем рано, если есть что удешевлять (ещё ≥1 карта в playable).
        if len(playable) > 1:
            flow = [c for c in playable
                    if _has_effect(c, FlowEffect) and not _has_effect(c, DamageEffect)]
            if flow:
                return flow[0]

        return None

    def on_turn_begin(self, combat) -> None:
        """Проактивные способности (до розыгрыша карт)."""

    def on_turn_end(self, combat) -> None:
        """Реактивные способности (после набора стаков/щита за ход)."""


class SummonerPolicy(BotPolicy):
    """Ядро класса — собрать стаю: призывы в приоритет, «Подкрепление» сразу."""

    def _class_pick(self, playable, combat):
        summons = [c for c in playable
                   if any(isinstance(e, SummonEffect) for e in c.effects)]
        return random.choice(summons) if summons else random.choice(playable)

    def on_turn_begin(self, combat) -> None:
        ab = _ability(combat)
        if ab:                      # бесплатный волк — успеет атаковать в этот ход
            ab.activate(combat)


class BerserkerPolicy(BotPolicy):
    """«Отрицание Смерти»: входит в БЕЗУМИЕ как СТАВКУ ДИСПЕРСИИ — дамп руки за 0
    энергии ценой HP (нырок в минус → множитель урона), но конец хода в минусе без
    победы = строгая смерть. Компетентный пилот ныряет ТОЛЬКО когда сошлись оба
    условия: полный буфер HP (пережить нырок) И добиваемый залп (нырок окупится
    киллом). Слепой газ был суицидом-ловушкой; умный газ раскручивает движок |HP|→FP
    (память balance-findings-berserker-glasscannon: 40% забегов доходят до эт.50)."""

    def on_turn_begin(self, combat) -> None:
        ab = _ability(combat)
        player = combat.player
        if not (ab and player.hp >= player.max_hp * _BERSERK_HP_FRACTION):
            return
        enemy_hp = sum(e.hp for e in combat.enemies if e.hp > 0)
        if 0 < enemy_hp <= player.max_hp * _BERSERK_KILLABLE_RATIO:
            ab.activate(combat)              # Безумие: карты за 0 энергии ценой HP


class WarriorPolicy(BotPolicy):
    """Ядро Воина — «защита = атака»: копим щит, затем конвертируем в урон
    («Возмездие» = щит, «Щитовой удар» = 50% щита)."""

    def _class_pick(self, playable, combat):
        shield = combat.player.shield
        retribution = [c for c in playable
                       if any(isinstance(e, ShieldDamageEffect) for e in c.effects)]
        shields = [c for c in playable
                   if any(isinstance(e, ShieldEffect) for e in c.effects)]
        others = [c for c in playable if c not in retribution]
        # «Возмездие» — на накопленном щите (или когда больше нечем играть).
        if retribution and (shield >= _WARRIOR_RETRIBUTION_MIN or not others):
            return retribution[0]
        # Иначе сначала строим щит (топливо для удара), потом всё остальное.
        if shields:
            return random.choice(shields)
        return random.choice(others) if others else random.choice(playable)

    def on_turn_end(self, combat) -> None:
        ab = _ability(combat)
        if ab and combat.player.shield >= _WARRIOR_SHIELD_MIN:
            ab.activate(combat)


class RoguePolicy(BotPolicy):
    """«Вскрытие» — удвоить осмысленный стак кровотечения (ценой -1 энергии)."""

    def on_turn_end(self, combat) -> None:
        ab = _ability(combat)
        if ab and getattr(combat.enemy, "bleed", 0) >= _ROGUE_BLEED_MIN:
            ab.activate(combat)


class DruidPolicy(BotPolicy):
    """«Токсичный взрыв» — когда яд накопился до осмысленного бурста."""

    def on_turn_end(self, combat) -> None:
        ab = _ability(combat)
        if ab and getattr(combat.enemy, "poison", 0) >= _DRUID_POISON_MIN:
            ab.activate(combat)


class MagePolicy(BotPolicy):
    """«Стихийный барьер» — при достаточной сумме стихийных стаков.
    pick_card: сетап комбо энейблером → атаки для детонации → фолбэк."""

    def _class_pick(self, playable, combat):
        enemy = combat.enemy
        has_both = (getattr(enemy, "wet", 0) > 0
                    and getattr(enemy, "ignited", 0) > 0)
        # Энейблер: карта, вешающая И wet, И ignited (сетап ПАР)
        enablers = []
        attacks = []
        for c in playable:
            status_types = {
                e.status_type
                for e in c.effects
                if isinstance(e, StatusEffect)
            }
            if "wet" in status_types and "ignited" in status_types:
                enablers.append(c)
            if any(isinstance(e, DamageEffect) for e in c.effects):
                attacks.append(c)
        # Если комбо ещё не готово — сетап энейблером
        if not has_both and enablers:
            return enablers[0]
        # Комбо готово — атаки для детонации (×2), но НЕ энейблер
        others = [c for c in playable if c not in enablers]
        detonators = [c for c in attacks if c not in enablers]
        if detonators:
            return random.choice(detonators)
        return random.choice(others) if others else random.choice(playable)

    def on_turn_end(self, combat) -> None:
        ab = _ability(combat)
        if not ab:
            return
        total = sum(
            max(0, getattr(creature, key, 0))
            for creature in (combat.player, combat.enemy)
            for key in _ELEMENTAL_STATUSES
        )
        if total >= _MAGE_ELEMENTAL_MIN:
            ab.activate(combat)


# Реестр: имя класса игрока -> политика. Фолбэк — базовая (random, без способности).
CLASS_POLICIES = {
    "Summoner":  SummonerPolicy(),
    "Berserker": BerserkerPolicy(),
    "Warrior":   WarriorPolicy(),
    "Rogue":     RoguePolicy(),
    "Druid":     DruidPolicy(),
    "Mage":      MagePolicy(),
}


def get_policy(class_name: str) -> BotPolicy:
    """Политика для класса игрока (по type(player).__name__)."""
    return CLASS_POLICIES.get(class_name, BotPolicy())
