# tests/test_corpse.py
# Трупы на сетке (субстрат Некроманта): тег [Corpse] + pure-ридеры/предикаты.
# Чистая логика, без боя.
from core.corpse import (
    CORPSE_TAG, mark_corpse, is_corpse, corpses_in, cell_has_corpse,
)
from core.Creature import Creature


def test_метка_и_предикат():
    c = Creature("X", 0, 30)
    assert is_corpse(c) is False              # живое/непомеченное — не труп
    mark_corpse(c)
    assert is_corpse(c) is True
    assert CORPSE_TAG in c.tags


def test_метка_идемпотентна():
    c = Creature("X", 0, 30)
    mark_corpse(c)
    mark_corpse(c)
    assert c.tags == {CORPSE_TAG}             # без дублей


def test_метка_не_трогает_координату():
    from core.positioning import Rank, Line
    c = Creature("X", 0, 30)
    c.rank, c.line = Rank.FRONT, Line.CENTER
    mark_corpse(c)
    assert c.rank == Rank.FRONT and c.line == Line.CENTER  # труп остаётся в клетке


def test_corpses_in_фильтрует():
    a, b, d = Creature("A", 0, 10), Creature("B", 5, 10), Creature("D", 0, 10)
    mark_corpse(a)
    mark_corpse(d)
    assert corpses_in([a, b, d]) == [a, d]    # только помеченные


def test_cell_has_corpse_предикат():
    from core.positioning import Rank, Line
    c = Creature("X", 0, 10)
    c.rank, c.line = Rank.FRONT, Line.LEFT
    mark_corpse(c)
    assert cell_has_corpse([c], Rank.FRONT, Line.LEFT) is True
    assert cell_has_corpse([c], Rank.BACK, Line.LEFT) is False   # другая клетка
    live = Creature("L", 5, 10)
    live.rank, live.line = Rank.FRONT, Line.LEFT
    assert cell_has_corpse([live], Rank.FRONT, Line.LEFT) is False  # живой ≠ труп
