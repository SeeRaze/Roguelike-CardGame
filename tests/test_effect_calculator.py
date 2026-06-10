# tests/test_effect_calculator.py
# Проверяем расчёт урона: EffectCalculator.calculate_damage(...).
# Это «сердце» боя — если тут ошибка, ломается весь баланс.
from core.EffectCalculator import EffectCalculator
from core.ComboRegistry import COMBOS, all_combos
from core.Creature import Creature
from core.players import Berserker
from core.relics import ПроклятаяКорона

calc = EffectCalculator.calculate_damage


def test_базовый_урон_без_модификаторов():
    # Нет ни ярости, ни слабости, ни уязвимости -> урон остаётся как есть.
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    assert calc(atk, tgt, 10) == 10


def test_ярость_добавляет_урон():
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    atk.strength = 3            # +3 к урону
    assert calc(atk, tgt, 10) == 13


def test_слабость_снижает_урон_на_25_процентов():
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    atk.weak = 1
    # int(10 * 0.75) == 7
    assert calc(atk, tgt, 10) == 7


def test_уязвимость_цели_увеличивает_урон_в_полтора_раза():
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    tgt.vulnerable = 1
    # int(10 * 1.5) == 15
    assert calc(atk, tgt, 10) == 15


def test_порядок_ярость_потом_слабость():
    # Сначала прибавляется ярость, потом применяется слабость.
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    atk.strength = 4
    atk.weak = 1
    # (10 + 4) -> int(14 * 0.75) == 10
    assert calc(atk, tgt, 10) == 10


def test_комбо_пар_утраивает_урон():
    # «Пар»: цель одновременно Мокрая и Горящая -> урон ×3.0.
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    tgt.wet = 2
    tgt.ignited = 2
    assert calc(atk, tgt, 10) == 30


def test_dry_run_не_расходует_стаки_комбо():
    # dry_run=True — это «прикидка для превью на карте», состояние меняться не должно.
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    tgt.wet = 2
    tgt.ignited = 2
    calc(atk, tgt, 10, dry_run=True)
    assert tgt.wet == 2 and tgt.ignited == 2     # стаки на месте


def test_обычный_расчёт_расходует_стаки_комбо(make_combat):
    # Без dry_run комбо «срабатывает»: по одному стаку Мокрого и Горящего уходит,
    # и поднимается флаг для пассива Мага.
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    tgt.wet = 2
    tgt.ignited = 2
    cm = make_combat(player=atk, enemy=tgt)
    calc(atk, tgt, 10, combat_manager=cm)
    assert tgt.wet == 1 and tgt.ignited == 1
    assert cm._combo_triggered is True


def test_берсерк_урон_только_от_минуса_hp(make_combat):
    # Передел Берсерка (этап 1): плоский пассив «Ярость крови» УБРАН. В ПЛЮСЕ Берсерк
    # бьёт как обычный боец (без бонуса); урон даёт ТОЛЬКО HP-долг множитель в МИНУСЕ.
    berserker = Berserker()
    tgt = Creature("Цель", 50, 50)
    cm = make_combat(player=berserker, enemy=tgt)   # игрок == атакующий
    berserker.hp = berserker.max_hp // 2            # положительный, но низкий
    assert calc(berserker, tgt, 10, combat_manager=cm) == 10   # БЕЗ бонуса
    berserker.hp = -5                               # долг HP 5 → ×1.5
    assert calc(berserker, tgt, 10, combat_manager=cm) == 15


def test_реликвия_проклятая_корона_удваивает_урон_игрока(make_combat):
    atk = Creature("Игрок", 50, 50)
    tgt = Creature("Цель", 50, 50)
    cm = make_combat(player=atk, enemy=tgt)
    cm.gm.relics = [ПроклятаяКорона()]
    # Корона удваивает урон атаки игрока: 10 -> 20.
    assert calc(atk, tgt, 10, game_manager=cm.gm, combat_manager=cm) == 20


def test_проклятая_корона_не_трогает_урон_врага(make_combat):
    enemy = Creature("Враг", 50, 50)
    player = Creature("Игрок", 50, 50)
    cm = make_combat(player=player, enemy=enemy)
    cm.gm.relics = [ПроклятаяКорона()]
    # Атакует враг (не игрок) -> корона не срабатывает.
    assert calc(enemy, player, 10, game_manager=cm.gm, combat_manager=cm) == 10


# ═══════════════════════════════════════════════════════════
# ComboRegistry — data-driven реестр комбо
# ═══════════════════════════════════════════════════════════

def test_реестр_содержит_правильную_запись_пар():
    steam = COMBOS.get("steam")
    assert steam is not None
    assert steam["name"] == "ПАР"
    assert steam["requires"] == ("wet", "ignited")
    assert steam["multiplier"] == 3.0
    assert steam["consume"] == 1
    assert "ПАР" in steam["log"]


def test_all_combos_возвращает_тот_же_словарь():
    assert all_combos() is COMBOS


def test_комбо_вариантный_не_срабатывает_без_стихий(make_combat):
    """Ни одного requires-статуса нет → урон без множителя."""
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    cm = make_combat(player=atk, enemy=tgt)
    assert calc(atk, tgt, 10, combat_manager=cm) == 10
    assert not cm._combo_triggered


def test_комбо_требует_все_статусы_одновременно(make_combat):
    """Только wet без ignited → множитель не срабатывает."""
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    tgt.wet = 3
    cm = make_combat(player=atk, enemy=tgt)
    assert calc(atk, tgt, 10, combat_manager=cm) == 10
    assert not cm._combo_triggered


def test_комбо_флаг_выставляется_при_срабатывании(make_combat):
    """Проверяем, что _combo_triggered = True (а не _steam_combo_triggered)."""
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    tgt.wet = 2
    tgt.ignited = 2
    cm = make_combat(player=atk, enemy=tgt)
    calc(atk, tgt, 10, combat_manager=cm)
    assert cm._combo_triggered is True


def test_комбо_стаки_снимаются_через_consume(make_combat):
    """ComboRegistry.consume=1: по 1 стаку каждого requires уходит."""
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    tgt.wet = 5
    tgt.ignited = 3
    cm = make_combat(player=atk, enemy=tgt)
    calc(atk, tgt, 10, combat_manager=cm)
    assert tgt.wet == 4
    assert tgt.ignited == 2


def test_комбо_не_уходит_ниже_нуля_стаков(make_combat):
    """Если стаков ровно на consume=1, они обнуляются, не уходят в минус."""
    atk = Creature("Атакующий", 50, 50)
    tgt = Creature("Цель", 50, 50)
    tgt.wet = 1
    tgt.ignited = 1
    cm = make_combat(player=atk, enemy=tgt)
    calc(atk, tgt, 10, combat_manager=cm)
    assert tgt.wet == 0
    assert tgt.ignited == 0
