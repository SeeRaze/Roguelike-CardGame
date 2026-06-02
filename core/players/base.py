from core.Creature import Creature

class Player(Creature):
    """Базовый каркас игрока. Содержит общую логику для всех будущих классов."""
    def __init__(self, name, max_hp, max_energy, gold, starter_deck_factory):
        # Наследуем базовые параметры существа (ХП, щиты, статусы)
        super().__init__(name=name, hp=max_hp, max_hp=max_hp)
        
        self.max_energy = max_energy
        self.energy = max_energy
        self.gold = gold
        
        # Функция-фабрика, которая соберет уникальную стартовую колоду персонажа
        self.starter_deck_factory = starter_deck_factory

    def reset_energy(self):
        """Восстановление энергии в начале каждого хода"""
        self.energy = self.max_energy

    def get_starter_deck(self):
        """Генерирует чистый массив объектов карт для старта забега"""
        return self.starter_deck_factory()
    def use_energy(self, amount):
        """Тратит указанное количество энергии при разыгрывании карты"""
        self.energy = max(self.energy - amount, 0)
        print(f" [ЭНЕРГИЯ] Потрачено {amount}. Осталось: {self.energy}/{self.max_energy}")

