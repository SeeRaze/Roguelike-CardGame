import random  # Импортируем рандом, чтобы враг выбирал действия случайно
from core.Creature import Creature  # Импортируем нашего родителя
from core.EffectCalculator import EffectCalculator #Импорт системы эффектов

class Enemy(Creature):
    def __init__(self, name="Культист", hp=50, max_hp=50):
        # Вызываем сборочный цех родителя (записываем имя, hp, max_hp и даем 0 щита)
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        
        # Уникальные карманы Врага для хранения его планов:
        self.intent_type = None    # Тип намерения (например, "attack" или "defend")
        self.intent_value = 0     # Числовое значение (сколько урона нанесет или сколько щита прибавит)

    def choose_intent(self):
        """Враг загадывает план, используя прокачанные этажом статы"""
        # Если GameManager не передал новые статы (мало ли), используем старую базу
        dmg = getattr(self, 'base_test_damage', 6)
        shld = getattr(self, 'base_test_shield', 5)
        
        roll = random.randint(1, 2)
        
        if roll == 1:
            self.intent_type = "attack"
            self.intent_value = dmg  # Бьет по новой формуле сложности!
        else:
            self.intent_type = "defend"
            self.intent_value = shld # Защищается по новой формуле!


    def display_intent(self):
        """Метод (умение) показать игроку, что враг задумал"""
        if self.intent_type == "attack":
            print(f"--- [!] Намерение {self.name}: Собирается АТАКОВАТЬ на {self.intent_value} урона! ---")
        elif self.intent_type == "defend":
            print(f"--- [!] Намерение {self.name}: Собирается НАКИНУТЬ {self.intent_value} щита! ---")

    def execute_intent(self, player, combat_manager=None):
        # Делаем проверку, так как в консольном симуляторе баланса мы не передаем лог
        if combat_manager:
            combat_manager.add_log_message(f"Ход существа [{self.name}]:")
            
        if self.intent_type == "attack":
            final_dmg = EffectCalculator.calculate_damage(attacker=self, target=player, base_damage=self.intent_value)
            player.take_damage(final_dmg)
            if combat_manager:
                combat_manager.add_log_message(f" -> Бьет вас на {final_dmg} урона.")
                
        elif self.intent_type == "defend":
            self.gain_shield(self.intent_value)
            if combat_manager:
                combat_manager.add_log_message(f" -> Накладывает себе +{self.intent_value} щита.")
                
        self.intent_type = None
        self.intent_value = 0
