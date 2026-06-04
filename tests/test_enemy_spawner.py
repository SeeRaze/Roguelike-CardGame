# tests/test_enemy_spawner.py
# Проверяем процедурную сборку врага: экспоненциальная формула E₀·g^f,
# множители элиты/босса, монотонность роста.
# Ожидаемые статы считаются из констант формулы (устойчиво к тюнингу баланса).
from managers.EnemySpawner import (
    build_enemy, build_enemy_group,
    HP_BASE, HP_GROWTH,
    DMG_BASE, DMG_GROWTH,
    SHLD_BASE, SHLD_GROWTH,
)
from managers.MapGenerator import FLOORS_PER_ACT


def _expected_stats(floor: int):
    """Базовые статы врага по экспоненциальной формуле (без множителей)."""
    hp   = int(HP_BASE * HP_GROWTH ** floor)
    dmg  = int(DMG_BASE * DMG_GROWTH ** floor)
    shld = int(SHLD_BASE * SHLD_GROWTH ** floor)
    return hp, dmg, shld


def test_обычный_враг_первого_этажа():
    hp, dmg, shld = _expected_stats(1)
    e = build_enemy(1, is_elite=False)
    assert e.hp == hp
    assert e.base_test_damage == dmg
    assert e.base_test_shield == shld
    assert e.is_elite is False
    assert e.shield == 0        # обычный враг не начинает со щитом


def test_элита_усиливает_статы():
    # Множители элиты: hp×1.5, dmg×1.4, shld×1.5 (с округлением вниз).
    hp, dmg, shld = _expected_stats(1)
    e = build_enemy(1, is_elite=True)
    assert e.hp == int(hp * 1.5)
    assert e.base_test_damage == int(dmg * 1.4)
    assert e.base_test_shield == int(shld * 1.5)
    assert e.is_elite is True
    assert e.shield == int(shld * 1.5)   # элита начинает со щитом


def test_босс_сильнее_и_подписан():
    # Последний этаж акта -> босс: имя с «БОСС:», множители ×2.2/×1.3/×1.8.
    boss_floor = FLOORS_PER_ACT
    base_hp, base_dmg, base_shld = _expected_stats(boss_floor)
    boss = build_enemy(boss_floor, is_elite=False)
    assert boss.name.startswith("БОСС:")
    assert boss.is_elite is False
    assert boss.hp == int(base_hp * 2.2)
    assert boss.base_test_damage == int(base_dmg * 1.3)
    assert boss.base_test_shield == int(base_shld * 1.8)
    assert boss.shield == boss.base_test_shield * 2
    # Босс крепче обычного врага соседнего этажа (19 — не босс).
    neighbour = build_enemy(boss_floor - 1, is_elite=False)
    assert boss.hp > neighbour.hp


def test_экспонента_монотонно_растёт():
    """Статы врага монотонно растут с этажом (гладкая экспонента, без скачков)."""
    e1 = build_enemy(1)
    e10 = build_enemy(10)
    e50 = build_enemy(50)
    e100 = build_enemy(100)
    assert e1.hp < e10.hp < e50.hp < e100.hp
    assert e1.base_test_damage < e10.base_test_damage < e50.base_test_damage < e100.base_test_damage
    assert e1.base_test_shield <= e100.base_test_shield


def test_босс_на_каждом_акте():
    """Босс на этажах 20, 40, 60, 80, 100."""
    for floor in [20, 40, 60, 80, 100]:
        e = build_enemy(floor, is_elite=False)
        assert e.name.startswith("БОСС:"), f"Этаж {floor} должен быть боссом"


def test_не_босс_на_обычных_этажах():
    """Обычные этажи (не кратные 20) — не босс."""
    for floor in [1, 5, 19, 21, 39, 41, 99]:
        e = build_enemy(floor, is_elite=False)
        assert not e.name.startswith("БОСС:"), f"Этаж {floor} не должен быть боссом"


def test_группа_врагов_размер_и_множители():
    """Группы: 1 враг до этажа 7, 2 врага с 7, 3 врага с 26. Босс — всегда 1."""
    # Ранний этаж: один враг.
    g1 = build_enemy_group(1)
    assert len(g1) == 1
    # Этаж 7+: два врага.
    g2 = build_enemy_group(10)
    assert len(g2) == 2
    assert all("1/2" in e.name or "2/2" in e.name for e in g2)
    # Этаж 26+: три врага.
    g3 = build_enemy_group(30)
    assert len(g3) == 3
    # Босс — всегда один.
    g_boss = build_enemy_group(20)
    assert len(g_boss) == 1
    assert g_boss[0].name.startswith("БОСС:")


def test_группа_множители_уменьшают_статы():
    """Множители группы снижают HP/урон каждого врага, но не в 1/group_size."""
    solo = build_enemy(30, is_elite=False)
    group = build_enemy_group(30)
    assert len(group) == 3
    # Каждый враг в группе слабее соло-версии того же этажа.
    for e in group:
        assert e.hp < solo.hp
        assert e.base_test_damage < solo.base_test_damage
    # Но суммарное HP группы > соло (трое ослабленных опаснее одного).
    total_hp = sum(e.hp for e in group)
    assert total_hp > solo.hp
