from core.rarity import Rarity


class Relic:
    """
    Базовый класс для всех пассивных артефактов.

    Хуки вызываются из соответствующих систем:
      on_combat_start      <- CombatManager.__init__
      on_turn_start        <- CombatManager.start_turn_phase (если добавить)
      on_damage_calculated <- EffectCalculator.calculate_damage
      on_tick_ignited      <- Creature.tick_statuses
      on_wet_applied       <- water.py (create_splash / create_rain_cloud)
      on_card_played       <- CombatManager.play_card_by_index (заглушка)
      on_shield_gained     <- Creature.gain_shield (заглушка)
      on_kill              <- CombatManager.end_turn_phase (заглушка)
    """

    def __init__(self, name: str, description: str,
                 rarity: Rarity = Rarity.COMMON):
        self.name        = name
        self.description = description
        self.rarity      = rarity

    # --- Активные хуки (реализованы в реликвиях) ---
    def on_combat_start(self, combat_manager):       pass
    def on_turn_start(self, combat_manager):         pass
    def on_damage_calculated(self, base_dmg):        return base_dmg
    def on_tick_ignited(self, creature):             return 0
    def on_wet_applied(self, combat_manager):        pass

    # --- Хуки-заглушки для будущих реликвий ---
    def on_card_played(self, card, combat_manager):  pass
    def on_shield_gained(self, amount, creature):    pass
    def on_kill(self, enemy, combat_manager):        pass