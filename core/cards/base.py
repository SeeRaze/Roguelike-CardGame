# core/cards/base.py
from core.EffectCalculator import EffectCalculator
from core.StatusRegistry import STATUSES
from core.rarity import Rarity


class DamageEffect:
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final_dmg = EffectCalculator.calculate_damage(
            player, enemy, base, gm_ref, combat_manager
        )
        enemy.take_damage(final_dmg, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> {enemy.name} получает {final_dmg} урона."
            )


class VampireDamageEffect:
    """Урон + восстановление 50% от фактически нанесённого урона.
    Синергирует с Яростью: сила удара растёт -> хил растёт пропорционально."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        gm_ref = combat_manager.gm if combat_manager is not None else None

        # Считаем финальный урон с учётом Ярости, Слабости, Уязвимости и реликвий
        final_dmg = EffectCalculator.calculate_damage(
            player, enemy, base, gm_ref, combat_manager
        )
        enemy.take_damage(final_dmg, attacker=player, combat_manager=combat_manager)

        # Хил = 50% от фактического урона (округление вниз, минимум 1)
        heal_amount = max(1, final_dmg // 2)
        healed = player.heal(heal_amount)

        if combat_manager:
            combat_manager.add_log_message(
                f" -> {enemy.name} получает {final_dmg} урона."
            )
            combat_manager.add_log_message(
                f" [ВАМПИР] Вы восстанавливаете {healed} HP."
            )


class ShieldEffect:
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        shield_amount = self.upgrade_val if is_upgraded else self.base_val
        player.gain_shield(shield_amount)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Вы получаете +{shield_amount} щита."
            )


class HealEffect:
    """Восстанавливает HP игрока. Не превышает max_hp."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        healed = player.heal(amount)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Вы восстанавливаете {healed} HP."
            )


class RegenEffect:
    """Накладывает статус регенерации на игрока."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.add_status("regen", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Вы получаете Регенерацию ({amount})."
            )


class StatusEffect:
    def __init__(self, status_type, base_turns, upgrade_turns):
        self.status_type = status_type
        self.base_turns = base_turns
        self.upgrade_turns = upgrade_turns

    def execute(self, player, enemy, combat_manager, is_upgraded):
        turns = self.upgrade_turns if is_upgraded else self.base_turns
        if self.status_type in STATUSES:
            enemy.add_status(self.status_type, turns, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> На {enemy.name} наложен статус "
                f"{self.status_type} ({turns} х.)"
            )


class PoisonEffect:
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        val = self.upgrade_val if is_upgraded else self.base_val
        enemy.poison += val
        if combat_manager:
            combat_manager.add_log_message(
                f" -> {enemy.name} отравлен на +{val} ед. яда!"
            )


class Card:
    def __init__(self, name, cost, card_type, description, effects,
                 rarity=Rarity.COMMON, exile=False):
        self.name = name
        self.cost = cost
        self.card_type = card_type
        self.description = description
        self.effects = effects
        self.rarity = rarity
        self.upgraded = False
        self.exile = exile

    def upgrade(self):
        if not self.upgraded:
            self.upgraded = True
            self.name += "+"

    def apply(self, player, enemy, combat_manager=None):
        for effect in self.effects:
            effect.execute(player, enemy, combat_manager, self.upgraded)