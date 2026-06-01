class Creature:
    """
    Базовый класс для всех живых существ.
    Теперь он умеет обрабатывать статусы Уязвимости и Слабости.
    """
    def __init__(self, name, hp, max_hp):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.shield = 0    # Статус "Щита"
        self.wet = 0       # Статус "Мокрый" (кол-во ходов)
        self.ignited = 0   # Статус "Зажженный" (кол-во ходов)

        
        # Новые карманы для статусов (число показывает, сколько ходов статус будет действовать)
        self.vulnerable = 0  # Уязвимость (получает на 50% больше урона)
        self.weak = 0        # Слабость (наносит на 25% меньше урона)

    def gain_shield(self, amount):
        self.shield += amount
        print(f"[{self.name}] получает +{amount} к щиту. Текущий щит: {self.shield}")

    def take_damage(self, amount):
        if self.vulnerable > 0:
            amount = int(amount * 1.5)
            print(f" [Эффект] {self.name} УЯЗВИМ! Урон увеличен до {amount}")

        print(f"[{self.name}] атакован на {amount} урона. (Щит: {self.shield}, HP: {self.hp})")
        
        # Честный и простой алгоритм поглощения урона щитом:
        if self.shield >= amount:
            # А) Щита много, он полностью впитывает удар
            self.shield -= amount
        else:
            # Б) Щита не хватает. Урон пробивает его остатки и бьет по здоровью
            damage_left = amount - self.shield
            self.shield = 0 # Щит полностью уничтожен
            self.hp -= damage_left # Остаток летит в лицо
            
        self.hp = max(self.hp, 0)
        print(f"[{self.name}] Итог -> Осталось щита: {self.shield}, Осталось HP: {self.hp}")

    def tick_statuses(self):
        """Метод «ти́канья» статусов в конце хода. Уменьшает их длительность на 1."""
        if self.vulnerable > 0:
            self.vulnerable -= 1
            if self.vulnerable == 0:
                print(f" [Статус] Уязвимость на существе {self.name} прошла.")
                
        if self.weak > 0:
            self.weak -= 1
            if self.weak == 0:
                print(f" [Статус] Слабость на существе {self.name} прошла.")
        # Эффект горения: если существо горит, оно получает урон в конце хода
        if self.ignited > 0:
            print(f" [Горение] {self.name} получает 3 урона от огня!")
            self.hp = max(self.hp - 3, 0)
            self.ignited -= 1
            if self.ignited == 0:
                print(f" [Статус] Огонь на {self.name} потух.")
                
        if self.wet > 0:
            self.wet -= 1
            if self.wet == 0:
                print(f" [Статус] {self.name} высох.")
