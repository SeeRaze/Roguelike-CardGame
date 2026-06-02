from core.enemies.base import Enemy

class Cultist(Enemy):
    def choose_intent(self):
        if self.turn_count == 0:
            self.intent_type = "defend"
            self.intent_value = self.base_test_shield
        else:
            self.intent_type = "attack"
            # Смягчаем разгон: +1 урон за ход вместо +2
            self.intent_value = self.base_test_damage + self.turn_count
        self.turn_count += 1


