class Relic:
    """Базовый родительский класс для всех пассивных артефактов."""
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def on_combat_start(self, combat_manager): pass
    def on_turn_start(self, combat_manager): pass
    def on_damage_calculated(self, base_dmg): return base_dmg
