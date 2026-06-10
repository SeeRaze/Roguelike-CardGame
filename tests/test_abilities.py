# tests/test_abilities.py
# Проверяем активные способности классов: эффект срабатывает, ставится «использована»,
# повторно за бой не активируется.
from core.players import Berserker
from core.players.abilities import (
    WarriorAbility, RogueAbility, MageAbility, BerserkerAbility,
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


def test_воин_щитовой_удар_бьёт_живого_в_группе(make_combat, make_creature):
    # Групповой бой: enemies[0] труп → удар уходит по живому, а не в пустоту (AUDIT 1.5).
    cm = make_combat()
    dead = cm.enemy
    dead.hp = 0
    alive = make_creature("Тыл", 30, 30)
    cm.enemies = [dead, alive]
    cm.player.shield = 10
    ab = WarriorAbility()
    assert ab.activate(cm) is True
    assert dead.hp == 0             # труп не трогаем
    assert alive.hp == 25           # урон 50% от 10 щита = 5 по живому


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


def test_берсерк_безумие(make_combat):
    # Передел (этап 1): активка теперь «Безумие» — карты за 0 энергии ценой HP.
    player = Berserker()
    cm = make_combat(player=player)
    ab = BerserkerAbility()
    assert ab.activate(cm) is True
    assert player.madness_active is True
    assert ab.activate(cm) is False        # уже в безумии в этот ход — повтор не активирует
