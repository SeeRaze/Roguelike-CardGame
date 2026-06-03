# managers/EnemySpawner.py
# Процедурная сборка врага: реестр типов, формулы статов по этажу/ярусу, генерация имени.
# Чистый модуль без состояния игры — возвращает готовый объект врага.
import random
from managers.MapGenerator import FLOORS_PER_ACT
from core.enemies import Cultist, SlimeAndGoblins, BossTitan, Enemy

# Реестр типов рядовых врагов: имя -> класс.
# Добавление нового врага: класс в core/enemies/ + строка сюда.
ENEMY_REGISTRY = {
    "Культист": Cultist,
    "Страж":    Cultist,
    "Слизень":  SlimeAndGoblins,
    "Гоблин":   SlimeAndGoblins,
    "Орк":      SlimeAndGoblins,
}

_BOSS_TITLES   = ["Древний Страж Башни", "Верховный Культист Неона", "Гидра Стихий"]
_ELITE_PREFIX  = ["Элитный", "Закалённый", "Древний", "Проклятый Страж"]
_COMMON_PREFIX = ["Дикий", "Проклятый", "Чумной", "Стальной", "Адский"]


def build_enemy(current_floor: int, is_elite: bool = False):
    """Собрать врага для текущего этажа.

    Считает статы по формулам этажа/яруса, применяет множители элиты/босса,
    проставляет имя, класс, base_test_damage/shield, is_elite и стартовый щит.
    Возвращает готовый объект Enemy (без привязки к бою — CombatManager создаёт вызывающий).
    """
    floor      = current_floor
    local_step = (floor - 1) % FLOORS_PER_ACT + 1
    tier       = (floor - 1) // FLOORS_PER_ACT + 1

    enemy_hp   = 35 + (floor * 5) + (tier * 15)
    enemy_dmg  = 5  + (tier * 2)  + (floor // 3)
    enemy_shld = 3  + (tier * 1)
    is_boss    = (local_step == FLOORS_PER_ACT)

    if is_elite:
        enemy_hp   = int(enemy_hp   * 1.5)
        enemy_dmg  = int(enemy_dmg  * 1.4)
        enemy_shld = int(enemy_shld * 1.5)

    if is_boss:
        enemy_hp   = int(enemy_hp   * 2.2)
        enemy_dmg  = int(enemy_dmg  * 1.3)
        enemy_shld = int(enemy_shld * 1.8)
        e_name      = f"БОСС: {random.choice(_BOSS_TITLES)} [Ярус {tier + 1}]"
        enemy_class = BossTitan
    elif is_elite:
        e_type      = random.choice(list(ENEMY_REGISTRY.keys()))
        e_name      = f"{random.choice(_ELITE_PREFIX)} {e_type} [Элита, Этаж {floor}]"
        enemy_class = ENEMY_REGISTRY.get(e_type, Enemy)
    else:
        e_type      = random.choice(list(ENEMY_REGISTRY.keys()))
        e_name      = f"{random.choice(_COMMON_PREFIX)} {e_type} [Этаж {floor}]"
        enemy_class = ENEMY_REGISTRY.get(e_type, Enemy)

    enemy = enemy_class(name=e_name, hp=enemy_hp, max_hp=enemy_hp)
    enemy.base_test_damage = enemy_dmg
    enemy.base_test_shield = enemy_shld
    enemy.is_elite         = is_elite

    if is_boss:
        enemy.shield = enemy_shld * 2
    elif is_elite:
        enemy.shield = enemy_shld

    return enemy
