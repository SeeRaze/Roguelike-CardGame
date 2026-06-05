# managers/EnemySpawner.py
# Процедурная сборка врага: реестр типов, формулы статов (чистая экспонента E₀·g^f),
# генерация имени. Чистый модуль без состояния игры — возвращает готовый объект врага.
import random
from managers.MapGenerator import FLOORS_PER_ACT
from core.enemies import Cultist, SlimeAndGoblins, BossTitan, Enemy, BOSS_BY_FLOOR

# ─── Кривая сложности: чистая экспонента E₀·g^f ──────────────────────────
# stat = BASE * GROWTH ** floor
# Плавный рост без ступеней актов (tier² удалён). g≈1.03 → удвоение ~каждые 23 этажа.
# Тюнинг через константы (замер — managers/balance/).
HP_BASE, HP_GROWTH = 45, 1.028
DMG_BASE, DMG_GROWTH = 5.5, 1.026
SHLD_BASE, SHLD_GROWTH = 3.5, 1.008

# Пороги ввода групп (этаж, с которого появляется N-й враг). Мультивраги
# вводятся позже, чем раньше (этаж 5), чтобы не было ранней «стены».
GROUP_2_FROM = 7    # с этого этажа возможны 2 врага
GROUP_3_FROM = 26   # с этого этажа возможны 3 врага

# Множители статов на одного врага в группе (плавный рост суммарной угрозы).
GROUP_HP_MULT  = {2: 0.55, 3: 0.40}
GROUP_DMG_MULT = {2: 0.60, 3: 0.50}

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

    Статы — чистая экспонента E₀·g^f (BASE * GROWTH ** floor), без ступеней актов.
    Множители элиты/босса применяются поверх. Возвращает готовый объект Enemy
    (без привязки к бою — CombatManager создаёт вызывающий).
    """
    floor = current_floor

    enemy_hp   = int(HP_BASE * HP_GROWTH ** floor)
    enemy_dmg  = int(DMG_BASE * DMG_GROWTH ** floor)
    enemy_shld = int(SHLD_BASE * SHLD_GROWTH ** floor)
    is_boss    = (floor % FLOORS_PER_ACT == 0)

    if is_elite:
        enemy_hp   = int(enemy_hp   * 1.5)
        enemy_dmg  = int(enemy_dmg  * 1.4)
        enemy_shld = int(enemy_shld * 1.5)

    if is_boss:
        enemy_hp   = int(enemy_hp   * 2.2)
        enemy_dmg  = int(enemy_dmg  * 1.3)
        enemy_shld = int(enemy_shld * 1.8)
        enemy_class = BOSS_BY_FLOOR.get(floor, BossTitan)
        # Имя: у каждого босса свой random_title(), у BossTitan — старый список.
        if hasattr(enemy_class, 'random_title'):
            e_name = f"БОСС: {enemy_class.random_title()} [Этаж {floor}]"
        else:
            e_name = f"БОСС: {random.choice(_BOSS_TITLES)} [Этаж {floor}]"
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
    enemy.spawn_floor      = floor   # Для Void Elemental (щит растёт с этажом)

    if is_boss:
        enemy.shield = enemy_shld * 2
    elif is_elite:
        enemy.shield = enemy_shld

    return enemy


def build_enemy_group(current_floor: int, is_elite: bool = False):
    """Собрать группу врагов для этажа.
    Возвращает список из 1–3 врагов. Босс всегда один.
    Пороги ввода групп — GROUP_2_FROM / GROUP_3_FROM (мультивраги вводятся
    плавно, чтобы не было ранней «стены»). HP/урон каждого уменьшены
    пропорционально размеру группы (GROUP_HP_MULT / GROUP_DMG_MULT)."""
    local_step = (current_floor - 1) % FLOORS_PER_ACT + 1
    is_boss    = (local_step == FLOORS_PER_ACT)

    # Босс всегда один (полный HP)
    if is_boss:
        return [build_enemy(current_floor, is_elite)]

    # Размер группы по этажу
    if current_floor < GROUP_2_FROM:
        group_size = 1
    elif current_floor < GROUP_3_FROM:
        group_size = 2
    else:
        group_size = 3

    # Элита тоже может быть группой (но реже: размер на 1 меньше)
    if is_elite and group_size > 1:
        group_size -= 1

    enemies = []
    for i in range(group_size):
        enemy = build_enemy(current_floor, is_elite)
        if group_size > 1:
            # Уменьшаем HP/урон пропорционально размеру группы
            enemy.hp     = max(1, int(enemy.hp * GROUP_HP_MULT[group_size]))
            enemy.max_hp = enemy.hp
            enemy.base_test_damage = max(
                3, int(enemy.base_test_damage * GROUP_DMG_MULT[group_size])
            )
            enemy.name = f"{enemy.name} ({i + 1}/{group_size})"
        enemies.append(enemy)

    return enemies
