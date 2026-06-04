# tests/test_enemy_spawner.py
# Проверяем процедурную сборку врага: формулы статов, множители элиты/босса.
# Ожидаемые статы считаются из констант формулы (устойчиво к тюнингу баланса).
from managers.EnemySpawner import (
    build_enemy,
    HP_BASE, HP_PER_FLOOR, HP_PER_TIER2,
    DMG_BASE, DMG_PER_TIER2, DMG_FLOOR_DIV,
    SHLD_BASE, SHLD_PER_TIER,
)
from managers.MapGenerator import FLOORS_PER_ACT


def _expected_stats(floor: int):
    """Базовые статы врага по формулам build_enemy (без множителей)."""
    tier = (floor - 1) // FLOORS_PER_ACT + 1
    hp   = HP_BASE  + floor * HP_PER_FLOOR        + tier * tier * HP_PER_TIER2
    dmg  = DMG_BASE + tier * tier * DMG_PER_TIER2 + floor // DMG_FLOOR_DIV
    shld = SHLD_BASE + tier * SHLD_PER_TIER
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
    # Последний этаж акта -> босс: имя с «БОСС:», стартовый щит = база×2.
    boss = build_enemy(FLOORS_PER_ACT, is_elite=False)
    assert boss.name.startswith("БОСС:")
    assert boss.is_elite is False
    # Босс заметно крепче обычного врага того же этажа по HP.
    assert boss.hp > build_enemy(1).hp
    assert boss.shield == boss.base_test_shield * 2
