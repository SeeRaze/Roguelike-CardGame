# tests/test_positioning_grid.py
# Позиционка v2 — §7 ЯДРО 2D: ось ЛИНИЙ ортогонально РАНГУ + Т-раскладки + пьюр-ридеры
# (cell/neighbors/column/same_rank). Без pygame. Всё аддитивно/инертно при line=None.
from core.Creature import Creature
from core.positioning import (
    Rank,
    Line,
    DEFAULT_GRID,
    MIRRORED_GRID,
    party_grid,
    grid_slots,
    cell,
    neighbors,
    column,
    same_rank,
    assign_enemy_ranks,
    assign_party_ranks,
    intercept_targets,
)


def _c(name, hp=10, line=None, rank=None):
    cr = Creature(name=name, hp=hp, max_hp=10)
    cr.line = line
    cr.rank = rank
    return cr


# ═══════════════════════════════════════════════════════════
# Ось ЛИНИЙ + атрибут line на Creature
# ═══════════════════════════════════════════════════════════

def test_line_константы():
    assert Line.LEFT == "left" and Line.CENTER == "center" and Line.RIGHT == "right"
    assert Line.ALL == (Line.LEFT, Line.CENTER, Line.RIGHT)


def test_creature_по_дефолту_без_линии():
    cr = Creature(name="герой", hp=10, max_hp=10)
    assert cr.line is None   # позиции нет → 2D-хелперы инертны
    assert cr.rank is None


# ═══════════════════════════════════════════════════════════
# Т-образные 2D-раскладки (данные)
# ═══════════════════════════════════════════════════════════

def test_дефолт_грид_герой_центр_фронт_союзники_края_тыла():
    assert DEFAULT_GRID == {
        Rank.FRONT: [Line.CENTER],
        Rank.BACK:  [Line.LEFT, Line.RIGHT],
    }


def test_зеркало_грид_саммоны_края_фронта_герой_центр_тыла():
    assert MIRRORED_GRID == {
        Rank.FRONT: [Line.LEFT, Line.RIGHT],
        Rank.BACK:  [Line.CENTER],
    }


def test_party_grid_переключается_зеркалом():
    assert party_grid(mirrored=False)[Rank.FRONT] == [Line.CENTER]
    assert party_grid(mirrored=True)[Rank.FRONT] == [Line.LEFT, Line.RIGHT]


def test_party_grid_копия_не_мутирует_оригинал():
    g = party_grid(mirrored=False)
    g[Rank.FRONT].append("xxx")
    assert DEFAULT_GRID[Rank.FRONT] == [Line.CENTER]   # оригинал цел


def test_grid_slots_плоский_детерминированный_порядок():
    # 3 слота, фронт раньше тыла; внутри ранга — по объявлению линий.
    assert grid_slots(mirrored=False) == [
        (Line.CENTER, Rank.FRONT),
        (Line.LEFT, Rank.BACK),
        (Line.RIGHT, Rank.BACK),
    ]
    assert grid_slots(mirrored=True) == [
        (Line.LEFT, Rank.FRONT),
        (Line.RIGHT, Rank.FRONT),
        (Line.CENTER, Rank.BACK),
    ]


# ═══════════════════════════════════════════════════════════
# cell() — клетка существа
# ═══════════════════════════════════════════════════════════

def test_cell_полная_позиция():
    cr = _c("c", line=Line.CENTER, rank=Rank.FRONT)
    assert cell(cr) == (Line.CENTER, Rank.FRONT)


def test_cell_none_если_нет_линии_или_ранга():
    assert cell(_c("a", line=Line.LEFT, rank=None)) is None
    assert cell(_c("b", line=None, rank=Rank.FRONT)) is None
    assert cell(_c("c")) is None


# ═══════════════════════════════════════════════════════════
# neighbors() — ортогональное соседство (манхэттен-1)
# ═══════════════════════════════════════════════════════════

def test_neighbors_горизонталь_в_ряду():
    # фронт-ряд: ЛЕВО — ЦЕНТР — ПРАВО. Центр соседствует с лево и право.
    left   = _c("L", line=Line.LEFT,   rank=Rank.FRONT)
    center = _c("C", line=Line.CENTER, rank=Rank.FRONT)
    right  = _c("R", line=Line.RIGHT,  rank=Rank.FRONT)
    party = [left, center, right]
    assert set(neighbors(center, party)) == {left, right}
    assert neighbors(left, party) == [center]   # лево НЕ соседствует с право (Δ=2)


def test_neighbors_вертикаль_в_колонке():
    front = _c("F", line=Line.CENTER, rank=Rank.FRONT)
    back  = _c("B", line=Line.CENTER, rank=Rank.BACK)
    assert neighbors(front, [front, back]) == [back]
    assert neighbors(back, [front, back]) == [front]


def test_neighbors_диагональ_не_сосед():
    # (ЛЕВО,ФРОНТ) и (ЦЕНТР,ТЫЛ): Δline=1 + Δrank=1 = 2 → НЕ соседи.
    a = _c("a", line=Line.LEFT,   rank=Rank.FRONT)
    b = _c("b", line=Line.CENTER, rank=Rank.BACK)
    assert neighbors(a, [a, b]) == []


def test_neighbors_исключает_себя_и_мёртвых():
    center = _c("C", line=Line.CENTER, rank=Rank.FRONT)
    left   = _c("L", line=Line.LEFT,   rank=Rank.FRONT, hp=0)   # сосед, но труп
    right  = _c("R", line=Line.RIGHT,  rank=Rank.FRONT)
    party = [center, left, right]
    assert neighbors(center, party) == [right]   # мёртвый лево не считается, себя нет


def test_neighbors_инертно_без_позиции():
    # creature без line → пусто, даже если у соседей позиции есть (baseline зелёный).
    loner = _c("loner")
    other = _c("o", line=Line.CENTER, rank=Rank.FRONT)
    assert neighbors(loner, [loner, other]) == []


# ═══════════════════════════════════════════════════════════
# column() / same_rank() — вертикальный ряд / горизонтальный ряд
# ═══════════════════════════════════════════════════════════

def test_column_вертикальный_ряд_одной_линии():
    cf = _c("cf", line=Line.CENTER, rank=Rank.FRONT)
    cb = _c("cb", line=Line.CENTER, rank=Rank.BACK)
    lf = _c("lf", line=Line.LEFT,   rank=Rank.FRONT)
    party = [cf, cb, lf]
    assert column(Line.CENTER, party) == [cf, cb]
    assert column(Line.LEFT, party) == [lf]


def test_column_отсекает_мёртвых_и_беслинейных():
    alive = _c("a", line=Line.LEFT, rank=Rank.FRONT)
    dead  = _c("d", line=Line.LEFT, rank=Rank.BACK, hp=0)
    noln  = _c("n")
    assert column(Line.LEFT, [alive, dead, noln]) == [alive]


def test_same_rank_горизонтальный_ряд():
    f1 = _c("f1", line=Line.LEFT,  rank=Rank.FRONT)
    f2 = _c("f2", line=Line.RIGHT, rank=Rank.FRONT)
    b1 = _c("b1", line=Line.CENTER, rank=Rank.BACK)
    party = [f1, f2, b1]
    assert same_rank(Rank.FRONT, party) == [f1, f2]
    assert same_rank(Rank.BACK, party) == [b1]


# ═══════════════════════════════════════════════════════════
# §8 — assign_enemy_ranks (враги на сетке: фронт первая половина)
# ═══════════════════════════════════════════════════════════

def test_враги_один_во_фронте():
    e = _c("e1")
    assign_enemy_ranks([e])
    assert e.rank == Rank.FRONT


def test_враги_двое_1фронт_1тыл():
    a, b = _c("a"), _c("b")
    assign_enemy_ranks([a, b])
    assert a.rank == Rank.FRONT and b.rank == Rank.BACK


def test_враги_трое_2фронт_1тыл():
    a, b, c = _c("a"), _c("b"), _c("c")
    assign_enemy_ranks([a, b, c])
    assert [a.rank, b.rank, c.rank] == [Rank.FRONT, Rank.FRONT, Rank.BACK]


def test_враги_четверо_2фронт_2тыл():
    es = [_c(f"e{i}") for i in range(4)]
    assign_enemy_ranks(es)
    assert [e.rank for e in es] == [Rank.FRONT, Rank.FRONT, Rank.BACK, Rank.BACK]


def test_враги_пустой_список_безопасно():
    assert assign_enemy_ranks([]) == []


def test_враги_перехват_фронт_прикрывает_тыл():
    # После расстановки intercept_targets даёт только фронт, пока он жив.
    a, b, c = _c("a"), _c("b"), _c("c")
    assign_enemy_ranks([a, b, c])
    assert set(intercept_targets([a, b, c])) == {a, b}   # тыл c прикрыт
    a.hp = 0
    b.hp = 0
    assert intercept_targets([a, b, c]) == [c]           # фронт пал → тыл открыт


# ═══════════════════════════════════════════════════════════
# §9 — заселение ЛИНИЙ: партия по Т-схеме (cell/neighbors/column реальны)
# ═══════════════════════════════════════════════════════════

def test_партия_дефолт_герой_центр_фронт_союзники_края_тыла():
    hero = _c("hero")
    s1, s2 = _c("s1"), _c("s2")
    assign_party_ranks(hero, [s1, s2], mirrored=False)
    assert cell(hero) == (Line.CENTER, Rank.FRONT)
    assert cell(s1) == (Line.LEFT, Rank.BACK)
    assert cell(s2) == (Line.RIGHT, Rank.BACK)


def test_партия_зеркало_саммоны_края_фронта_герой_центр_тыла():
    hero = _c("hero")
    s1, s2 = _c("s1"), _c("s2")
    assign_party_ranks(hero, [s1, s2], mirrored=True)
    assert cell(hero) == (Line.CENTER, Rank.BACK)
    assert cell(s1) == (Line.LEFT, Rank.FRONT)
    assert cell(s2) == (Line.RIGHT, Rank.FRONT)


def test_партия_overflow_линии_циклятся():
    # 3 союзника на 2 слота тыла → линии повторяются (делят клетку), не падаем.
    hero = _c("hero")
    s1, s2, s3 = _c("s1"), _c("s2"), _c("s3")
    assign_party_ranks(hero, [s1, s2, s3], mirrored=False)
    assert s1.line == Line.LEFT and s2.line == Line.RIGHT
    assert s3.line == Line.LEFT          # цикл
    assert all(s.rank == Rank.BACK for s in (s1, s2, s3))


def test_партия_без_союзников_только_герой_центр():
    hero = _c("hero")
    assign_party_ranks(hero, mirrored=False)
    assert cell(hero) == (Line.CENTER, Rank.FRONT)


def test_партия_column_героя_и_соседство():
    # Дефолт: герой (Ц,Ф). Союзник (Л,Т) — НЕ в колонке героя (другая линия) и
    # НЕ сосед (диагональ). Союзник, посаженный в (Ц,Т), был бы соседом по вертикали.
    hero = _c("hero")
    s_left = _c("sL")
    assign_party_ranks(hero, [s_left], mirrored=False)   # s_left → (Л,Т)
    assert column(Line.CENTER, [hero, s_left]) == [hero]
    assert neighbors(hero, [hero, s_left]) == []          # (Ц,Ф)-(Л,Т) диагональ


# ═══════════════════════════════════════════════════════════
# §9 — заселение ЛИНИЙ: враги (cell/neighbors реальны на вражеской стороне)
# ═══════════════════════════════════════════════════════════

def test_враги_линия_один_центр():
    e = _c("e")
    assign_enemy_ranks([e])
    assert cell(e) == (Line.CENTER, Rank.FRONT)


def test_враги_линия_двое_колонка_по_центру():
    # 2 врага → 1Ф/1Б, оба ЦЕНТР (первый в _LINE_FILL_ORDER) → вертикальная колонка.
    a, b = _c("a"), _c("b")
    assign_enemy_ranks([a, b])
    assert cell(a) == (Line.CENTER, Rank.FRONT)
    assert cell(b) == (Line.CENTER, Rank.BACK)
    assert neighbors(a, [a, b]) == [b]    # соседи по вертикали (колонка)


def test_враги_линия_трое_фронт_центр_лево():
    a, b, c = _c("a"), _c("b"), _c("c")
    assign_enemy_ranks([a, b, c])
    assert cell(a) == (Line.CENTER, Rank.FRONT)
    assert cell(b) == (Line.LEFT, Rank.FRONT)
    assert cell(c) == (Line.CENTER, Rank.BACK)
    assert set(neighbors(a, [a, b, c])) == {b, c}   # центр-фронт смежен лево-фронт + центр-тыл


