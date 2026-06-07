# tests/test_abilities.py
# Проверяем активные способности классов: эффект срабатывает, ставится «использована»,
# повторно за бой не активируется.
from core.players import Berserker
from core.players.abilities import (
    WarriorAbility, RogueAbility, MageAbility, DruidAbility, BerserkerAbility,
)


def test_воин_щитовой_удар(make_combat):
    cm = make_combat()
    cm.player.shield = 10
    ab = WarriorAbility()
    assert ab.activate(cm) is True
    assert cm.enemy.hp == 45        # урон = 50% от 10 щита = 5
    assert ab._used is True
    # Повторно за бой — не срабатывает.
    assert ab.activate(cm) is False
    assert cm.enemy.hp == 45


def test_разбойник_вскрытие_удваивает_кровотечение(make_combat):
    cm = make_combat()
    cm.enemy.bleed = 3
    ab = RogueAbility()
    ab.activate(cm)
    assert cm.enemy.bleed == 6
    assert ab._used is True
    assert ab._penalty_pending is True   # штраф энергии на следующий ход


def test_маг_стихийный_барьер_даёт_щит(make_combat):
    cm = make_combat()
    cm.enemy.wet = 2
    cm.enemy.ignited = 1            # сумма стихийных стаков = 3
    ab = MageAbility()
    ab.activate(cm)
    assert cm.player.shield == 9   # 3 стака × 3
    assert cm._elemental_blocked is True
    assert ab._used is True


def test_друид_токсичный_взрыв(make_combat):
    cm = make_combat()
    cm.enemy.poison = 8             # 8 яда → бурст 8 урона + реген = 8//4 = 2
    ab = DruidAbility()
    ab.activate(cm)
    assert cm.enemy.poison == 0     # весь яд снят...
    assert cm.enemy.hp == 42        # ...и нанесён разом (8 урона)
    assert cm.player.regen == 2     # реген = 1/4 снятого яда (потолок 8)
    assert ab._used is True


def test_берсерк_безумие(make_combat):
    # Передел (этап 1): активка теперь «Безумие» — карты за 0 энергии ценой HP.
    player = Berserker()
    cm = make_combat(player=player)
    ab = BerserkerAbility()
    assert ab.activate(cm) is True
    assert player.madness_active is True
    assert ab.activate(cm) is False        # уже в безумии в этот ход — повтор не активирует
