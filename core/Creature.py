class Creature:
    """
    Базовый класс для всех живых существ.
    Статусы: vulnerable, weak, wet, ignited, poison.
    Баффы: strength (Ярость), thorns (Шипы).
    """
    def __init__(self, name, hp, max_hp):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.shield = 0

        # Статусы (тикают каждый ход)
        self.wet = 0
        self.ignited = 0
        self.poison = 0
        self.vulnerable = 0
        self.weak = 0

        # Пассивные баффы (не тикают, постоянны пока не сброшены)
        self.strength = 0  # Ярость: +X к урону всех атак
        self.thorns = 0    # Шипы: X урона атакующему при получении удара

    def gain_shield(self, amount):
        self.shield += amount
        print(f"[{self.name}] получает +{amount} к щиту. Текущий щит: {self.shield}")

    def take_damage(self, amount, attacker=None):
        if self.vulnerable > 0:
            amount = int(amount * 1.5)
            print(f" [Эффект] {self.name} УЯЗВИМ! Урон увеличен до {amount}")

        print(f"[{self.name}] атакован на {amount} урона. (Щит: {self.shield}, HP: {self.hp})")

        if self.shield >= amount:
            self.shield -= amount
        else:
            damage_left = amount - self.shield
            self.shield = 0
            self.hp -= damage_left

        self.hp = max(self.hp, 0)
        print(f"[{self.name}] Итог -> Осталось щита: {self.shield}, Осталось HP: {self.hp}")

        # Шипы: отражаем урон атакующему (щит не защищает)
        if self.thorns > 0 and attacker is not None:
            print(f" [ШИПЫ] {self.name} отражает {self.thorns} урона на {attacker.name}!")
            attacker.hp = max(attacker.hp - self.thorns, 0)

    def tick_statuses(self):
        """Тикает статусы в конце хода. Баффы (strength, thorns) не трогаем."""
        if self.vulnerable > 0:
            self.vulnerable -= 1
            if self.vulnerable == 0:
                print(f" [Статус] Уязвимость на существе {self.name} прошла.")

        if self.weak > 0:
            self.weak -= 1
            if self.weak == 0:
                print(f" [Статус] Слабость на существе {self.name} прошла.")

        if self.ignited > 0:
            print(f" [Горение] {self.name} получает 3 урона от огня!")
            self.hp = max(self.hp - 3, 0)
            self.ignited -= 1
            if self.ignited == 0:
                print(f" [Статус] Огонь на {self.name} потух.")

        if self.poison > 0:
            print(f" [ЯД] {self.name} получает {self.poison} урона от токсинов сквозь щиты!")
            self.hp = max(self.hp - self.poison, 0)
            self.poison -= 1
            if self.poison == 0:
                print(f" [Статус] Яд в теле {self.name} полностью рассеялся.")

        if self.wet > 0:
            self.wet -= 1
            if self.wet == 0:
                print(f" [Статус] {self.name} высох.")