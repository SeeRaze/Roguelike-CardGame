import random
from core.Creature import Creature

class Enemy(Creature):
    """Базовый каркас для всех монстров."""
    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        self.base_test_damage = 0
        self.base_test_shield = 0
        self.intent_type = "none"
        self.intent_value = 0
        self.turn_count = 0

    def choose_intent(self):
        """Каждый уникальный моб перепишет этот метод под свой ИИ."""
        pass

    def execute_intent(self, player, combat_manager=None):
        """Общая логика выполнения намерения в конце хода."""
        self.turn_count += 1
        if combat_manager:
            combat_manager.add_log_message(f"Ход существа [{self.name}]:")
        from core.EffectCalculator import EffectCalculator

        if self.intent_type == "attack":
            final_dmg = EffectCalculator.calculate_damage(self, player, self.intent_value, combat_manager.gm if combat_manager else None, combat_manager)
            player.take_damage(final_dmg, attacker=self)  # <-- передаём себя
            if combat_manager:
                combat_manager.add_log_message(f" -> Бьет вас на {final_dmg} урона.")
        elif self.intent_type == "defend":
            self.gain_shield(self.intent_value)
            if combat_manager:
                combat_manager.add_log_message(f" -> Закрывается щитом на +{self.intent_value}.")
        elif self.intent_type == "debuff":
            player.weak += self.intent_value
            if combat_manager:
                combat_manager.add_log_message(f" -> Накладывает на вас Слабость ({self.intent_value} х.)")