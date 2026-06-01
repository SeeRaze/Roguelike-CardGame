# Из файла Creature импортируем родительский класс Creature
from core.Creature import Creature

# В скобках указываем Creature. Это значит: Player наследует ВСЁ у класса Creature
class Player(Creature):
    def __init__(self, hp=80, max_hp=80, energy=3, max_energy=3):
        # super() — это команда «обратись к родителю». 
        # Мы вызываем инит родителя, чтобы он записал имя, hp и max_hp в паспорт
        super().__init__(name="Игрок", hp=hp, max_hp=max_hp)
        
        # А это личные уникальные карманы игрока, которых нет у обычных монстров
        self.energy = energy
        self.max_energy = max_energy

    def use_energy(self, amount):
        """Уникальное умение игрока — тратить энергию на карты"""
        self.energy -= amount
