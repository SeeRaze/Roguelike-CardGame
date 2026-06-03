# tests/test_enemy_spawner.py
# Проверяем процедурную сборку врага: формулы статов, множители элиты/босса.
from managers.EnemySpawner import build_enemy
from managers.MapGenerator import FLOORS_PER_ACT


def test_обычный_враг_первого_этажа():
    # floor=1, tier=1: hp=35+5+15=55, dmg=5+2+0=7, shld=3+1=4.
    e = build_enemy(1, is_elite=False)
    assert e.hp == 55
    assert e.base_test_damage == 7
    assert e.base_test_shield == 4
    assert e.is_elite is False
    assert e.shield == 0        # обычный враг не начинает со щитом


def test_элита_усиливает_статы():
    # Множители элиты: hp×1.5, dmg×1.4, shld×1.5 (с округлением вниз).
    e = build_enemy(1, is_elite=True)
    assert e.hp == 82           # int(55 * 1.5)
    assert e.base_test_damage == 9   # int(7 * 1.4)
    assert e.base_test_shield == 6   # int(4 * 1.5)
    assert e.is_elite is True
    assert e.shield == 6        # элита начинает со щитом


def test_босс_сильнее_и_подписан():
    # Последний этаж акта -> босс: имя с «БОСС:», стартовый щит = база×2.
    boss = build_enemy(FLOORS_PER_ACT, is_elite=False)
    assert boss.name.startswith("БОСС:")
    assert boss.is_elite is False
    # Босс заметно крепче обычного врага того же этажа по HP.
    assert boss.hp > build_enemy(1).hp
    assert boss.shield == boss.base_test_shield * 2
