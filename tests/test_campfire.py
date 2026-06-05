# tests/test_campfire.py
# Юнит-тесты core-хелперов Костра (Creature.lose_hp / rest_heal_amount).
# Сам UI костра (ui/Campfire.py) — pygame-слой, логику держим в core и тестируем тут.
from core.Creature import Creature


# ═══════════════════════════════════════════════════════════════════
# lose_hp -- прямой урон СКВОЗЬ ЩИТ (Ритуал крови, Проклятый сундук)
# ═══════════════════════════════════════════════════════════════════
def test_lose_hp_бьёт_сквозь_щит_не_трогая_броню():
    c = Creature("Цель", 50, 50)
    c.shield = 20
    lost = c.lose_hp(10)
    assert lost == 10
    assert c.hp == 40        # урон ушёл прямо в HP
    assert c.shield == 20    # щит не тронут


def test_lose_hp_клампится_в_ноль_не_уходит_в_минус():
    c = Creature("Цель", 5, 50)
    lost = c.lose_hp(10)
    assert lost == 5         # списали лишь сколько было
    assert c.hp == 0


def test_lose_hp_ноль_и_отрицательное_безопасны():
    c = Creature("Цель", 30, 50)
    assert c.lose_hp(0) == 0
    assert c.lose_hp(-7) == 0
    assert c.hp == 30        # HP не изменилось


# ═══════════════════════════════════════════════════════════════════
# rest_heal_amount -- «Отдых»: 30% от НЕДОСТАЮЩЕГО HP
# ═══════════════════════════════════════════════════════════════════
def test_rest_heal_30_процентов_недостающего():
    # недостаёт 60 → 30% = 18
    assert Creature.rest_heal_amount(40, 100) == 18


def test_rest_heal_при_полном_хп_ноль():
    assert Creature.rest_heal_amount(100, 100) == 0


def test_rest_heal_округление_вниз():
    # недостаёт 5 → 1.5 → int() усечёт до 1
    assert Creature.rest_heal_amount(95, 100) == 1
