# managers/balance/policy.py
# Политика бота: КАК выбирать карту и КОГДА жать классовую способность.
# Дефолт-бот играл случайно и не жал способности — из-за этого классы (особенно
# Призыватель) мерились искусственно слабыми. Политика делает бота КОМПЕТЕНТНЫМ:
# он играет к ядру своего класса. Цель — честный замер, а не оптимальный ИИ.
import random

from core.cards.base import ShieldEffect
from core.cards.summon import SummonEffect
from core.cards.warrior import ShieldDamageEffect

# --- Пороги «компетентности» (НЕ игровой баланс, а качество игры бота) ---
# Жать реактивную способность, когда набралось осмысленно много стаков/щита.
_WARRIOR_SHIELD_MIN     = 8   # «Щитовой удар»: удар = 50% щита
_WARRIOR_RETRIBUTION_MIN = 10 # «Возмездие»: придержать, пока щит не накоплен
_ROGUE_BLEED_MIN        = 8   # «Вскрытие»: удвоить кровотечение (ценой -1 энергии)
_DRUID_POISON_MIN       = 10  # «Токсичный взрыв»: снять весь яд разом
_MAGE_ELEMENTAL_MIN     = 4   # «Стихийный барьер»: щит = стихийные стаки * 3
_BERSERK_HP_FRACTION    = 0.6 # «Кровавая ярость»: жать, пока HP безопасно высок

# Стихийные статусы для подсчёта (как в MageAbility).
_ELEMENTAL_STATUSES = ("ignited", "wet", "poison")


def _ability(combat):
    """Готовая к активации способность игрока или None."""
    ab = getattr(combat.player, "active_ability", None)
    return ab if (ab and ab.is_ready()) else None


class BotPolicy:
    """База: случайный выбор карты, способность не используется.
    Подклассы переопределяют нужное."""

    def pick_card(self, playable, combat):
        return random.choice(playable)

    def on_turn_begin(self, combat) -> None:
        """Проактивные способности (до розыгрыша карт)."""

    def on_turn_end(self, combat) -> None:
        """Реактивные способности (после набора стаков/щита за ход)."""


class SummonerPolicy(BotPolicy):
    """Ядро класса — собрать стаю: призывы в приоритет, «Подкрепление» сразу."""

    def pick_card(self, playable, combat):
        summons = [c for c in playable
                   if any(isinstance(e, SummonEffect) for e in c.effects)]
        return random.choice(summons) if summons else random.choice(playable)

    def on_turn_begin(self, combat) -> None:
        ab = _ability(combat)
        if ab:                      # бесплатный волк — успеет атаковать в этот ход
            ab.activate(combat)


class BerserkerPolicy(BotPolicy):
    """Ранняя Ярость действует больше ходов; жмём, пока HP безопасно высок."""

    def on_turn_begin(self, combat) -> None:
        ab = _ability(combat)
        player = combat.player
        if ab and player.hp >= player.max_hp * _BERSERK_HP_FRACTION:
            ab.activate(combat)


class WarriorPolicy(BotPolicy):
    """Ядро Воина — «защита = атака»: копим щит, затем конвертируем в урон
    («Возмездие» = щит, «Щитовой удар» = 50% щита)."""

    def pick_card(self, playable, combat):
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
    """«Стихийный барьер» — только при достаточной сумме стихийных стаков."""

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
