# managers/EnemySpawner.py
# Процедурная сборка врага: реестр типов, формулы статов по этажу/ярусу, генерация имени.
# Чистый модуль без состояния игры — возвращает готовый объект врага.
import random
from managers.MapGenerator import FLOORS_PER_ACT
from core.enemies import Cultist, SlimeAndGoblins, BossTitan, Enemy

# ─── Кривая сложности (тюнится балансером, см. managers/balance/) ────────────
# Цель: плавный скейл к 100-му этажу, который почти непроходим. Рост статов
# НЕЛИНЕЙНЫЙ — ускоряется к поздним актам через tier² (5 актов по 20 этажей).
#   hp  = HP_BASE  + floor*HP_PER_FLOOR  + tier² * HP_PER_TIER2
#   dmg = DMG_BASE + tier²*DMG_PER_TIER2 + floor//DMG_FLOOR_DIV
#   shld= SHLD_BASE + tier*SHLD_PER_TIER
HP_BASE, HP_PER_FLOOR, HP_PER_TIER2 = 30, 4, 12
DMG_BASE, DMG_PER_TIER2, DMG_FLOOR_DIV = 4, 2, 4
SHLD_BASE, SHLD_PER_TIER = 3, 1

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

    Считает статы по формулам этажа/яруса, применяет множители элиты/босса,
    проставляет имя, класс, base_test_damage/shield, is_elite и стартовый щит.
    Возвращает готовый объект Enemy (без привязки к бою — CombatManager создаёт вызывающий).
    """
    floor      = current_floor
    local_step = (floor - 1) % FLOORS_PER_ACT + 1
    tier       = (floor - 1) // FLOORS_PER_ACT + 1

    enemy_hp   = HP_BASE  + (floor * HP_PER_FLOOR)   + (tier * tier * HP_PER_TIER2)
    enemy_dmg  = DMG_BASE + (tier * tier * DMG_PER_TIER2) + (floor // DMG_FLOOR_DIV)
    enemy_shld = SHLD_BASE + (tier * SHLD_PER_TIER)
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
