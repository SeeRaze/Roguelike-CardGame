import random
from core.enemies.base import Enemy
from core.enemies.cultist import Cultist
from core.enemies.slime import SlimeAndGoblins
from core.enemies.boss import BossTitan

def spawn_procedural_enemy(floor: int) -> Enemy:
    """Универсальная фабрика. Заменяет старый громоздкий метод из GameManager!"""
    # Выбираем случайный класс монстра из доступных
    enemy_classes = [Cultist, SlimeAndGoblins]
    chosen_class = random.choice(enemy_classes)
    
    # Создаем и возвращаем объект моба, настроенный под текущий этаж
    return chosen_class(floor=floor)
