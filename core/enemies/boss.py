from core.enemies.base import Enemy


class BossTitan(Enemy):
    """Настоящий Босс Яруса со сложным и опасным паттерном поведения."""

    def choose_intent(self):
        # Паттерн из 3 ходов по кругу.
        # turn_count инкрементируется в execute_intent базового класса.
        step = self.turn_count % 3

        if step == 0:
            self.intent_type  = "defend"
            self.intent_value = self.base_test_shield * 2
        elif step == 1:
            self.intent_type  = "debuff"
            self.intent_value = 2
        else:
            self.intent_type  = "attack"
            self.intent_value = self.base_test_damage * 2