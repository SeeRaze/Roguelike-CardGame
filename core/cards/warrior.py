# core/cards/warrior.py
# Классовые карты Воина. Идентичность класса — «защита = атака»: Воин копит щит
# и конвертирует его в урон. ShieldDamageEffect — win-condition танка против
# масштабирующихся врагов средней игры.
from core.cards.base import Card
from core.EffectCalculator import EffectCalculator
from core.rarity import Rarity


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
