from core.EffectCalculator import EffectCalculator

class DamageEffect:
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final_dmg = EffectCalculator.calculate_damage(player, enemy, base, gm_ref, combat_manager)
        enemy.take_damage(final_dmg, attacker=player)
        if combat_manager:
            combat_manager.add_log_message(f" -> {enemy.name} получает {final_dmg} урона.")

class ShieldEffect:
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
    def execute(self, player, enemy, combat_manager, is_upgraded):
        shield_amount = self.upgrade_val if is_upgraded else self.base_val
        player.gain_shield(shield_amount)
        if combat_manager:
            combat_manager.add_log_message(f" -> Вы получаете +{shield_amount} щита.")

class StatusEffect:
    def __init__(self, status_type, base_turns, upgrade_turns):
        self.status_type = status_type
        self.base_turns = base_turns
        self.upgrade_turns = upgrade_turns
    def execute(self, player, enemy, combat_manager, is_upgraded):
        turns = self.upgrade_turns if is_upgraded else self.base_turns
        if self.status_type == "weak":
            enemy.weak += turns
        elif self.status_type == "vulnerable":
            enemy.vulnerable += turns
        elif self.status_type == "wet":
            enemy.wet += turns
            # Хук реликвий: при наложении "мокрый" на врага
            if combat_manager and hasattr(combat_manager, 'gm') and combat_manager.gm:
                for relic in combat_manager.gm.relics:
                    relic.on_wet_applied(combat_manager)
        elif self.status_type == "ignited":
            enemy.ignited += turns
        if combat_manager:
            combat_manager.add_log_message(f" -> На {enemy.name} наложен статус {self.status_type} ({turns} х.)")

class PoisonEffect:
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
    def execute(self, player, enemy, combat_manager, is_upgraded):
        val = self.upgrade_val if is_upgraded else self.base_val
        enemy.poison += val
        if combat_manager:
            combat_manager.add_log_message(f" -> {enemy.name} отравлен на +{val} ед. яда!")

class Card:
    def __init__(self, name, cost, card_type, description, effects):
        self.name = name
        self.cost = cost
        self.card_type = card_type
        self.description = description
        self.effects = effects
        self.upgraded = False
    def upgrade(self):
        if not self.upgraded:
            self.upgraded = True
            self.name += "+"
    def apply(self, player, enemy, combat_manager=None):
        for effect in self.effects:
            effect.execute(player, enemy, combat_manager, self.upgraded)