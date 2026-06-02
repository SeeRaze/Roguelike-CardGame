from core.enemies.base import Enemy

class SlimeAndGoblins(Enemy):
    def choose_intent(self):
        # Чередуем: ход — атака, ход — дебафф/щит
        if self.turn_count % 2 == 0:
            self.intent_type = "attack"
            self.intent_value = self.base_test_damage
        else:
            self.intent_type = "defend"
            self.intent_value = self.base_test_shield + 2