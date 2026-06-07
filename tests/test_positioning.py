# tests/test_positioning.py
# Позиционка 3×3 — §1 ЯДРО: чистый модуль позиций + атрибут rank на Creature.
# Без pygame: Creature тянет только StatusRegistry.
from core.Creature import Creature
from core.positioning import (
    Rank,
    DEFAULT_LAYOUT,
    MIRRORED_LAYOUT,
    party_layout,
    slot_capacity,
    living,
    has_positions,
    front_rank,
    back_rank,
    intercept_targets,
)


def _c(name, hp=10, rank=None):
    cr = Creature(name=name, hp=hp, max_hp=10)
    cr.rank = rank
    return cr


# ═══════════════════════════════════════════════════════════
# Раскладки (ёмкости утверждены юзером)
# ═══════════════════════════════════════════════════════════

def test_дефолтная_раскладка_1_фронт_2_тыл():
    assert DEFAULT_LAYOUT == {Rank.FRONT: 1, Rank.BACK: 2}


def test_зеркальная_раскладка_2_фронт_1_тыл():
    assert MIRRORED_LAYOUT == {Rank.FRONT: 2, Rank.BACK: 1}


def test_party_layout_переключается_флагом_зеркала():
    assert party_layout(mirrored=False) == {Rank.FRONT: 1, Rank.BACK: 2}
    assert party_layout(mirrored=True) == {Rank.FRONT: 2, Rank.BACK: 1}


def test_party_layout_возвращает_копию_не_мутирует_оригинал():
    layout = party_layout(mirrored=False)
    layout[Rank.FRONT] = 99
    assert DEFAULT_LAYOUT[Rank.FRONT] == 1  # оригинал не тронут


def test_slot_capacity_по_рангу_и_зеркалу():
    assert slot_capacity(Rank.FRONT, mirrored=False) == 1
    assert slot_capacity(Rank.BACK, mirrored=False) == 2
    assert slot_capacity(Rank.FRONT, mirrored=True) == 2
    assert slot_capacity(Rank.BACK, mirrored=True) == 1


# ═══════════════════════════════════════════════════════════
# Атрибут rank на Creature
# ═══════════════════════════════════════════════════════════

def test_creature_по_дефолту_без_ранга():
    cr = Creature(name="герой", hp=10, max_hp=10)
    assert cr.rank is None  # позиции нет → позиционка инертна


def test_creature_можно_задать_ранг():
    cr = _c("герой", rank=Rank.FRONT)
    assert cr.rank == Rank.FRONT


# ═══════════════════════════════════════════════════════════
# Пьюр-хелперы запроса
# ═══════════════════════════════════════════════════════════

def test_living_отсекает_мёртвых():
    a, b, d = _c("a"), _c("b"), _c("d", hp=0)
    assert living([a, b, d]) == [a, b]


def test_has_positions_ложь_без_рангов():
    assert has_positions([_c("a"), _c("b")]) is False


def test_has_positions_истина_если_есть_ранг():
    assert has_positions([_c("a"), _c("b", rank=Rank.BACK)]) is True


def test_front_back_rank_фильтруют_по_рангу_и_живости():
    f = _c("f", rank=Rank.FRONT)
    b = _c("b", rank=Rank.BACK)
    dead_f = _c("df", hp=0, rank=Rank.FRONT)
    party = [f, b, dead_f]
    assert front_rank(party) == [f]      # мёртвый фронт не считается
    assert back_rank(party) == [b]


# ═══════════════════════════════════════════════════════════
# intercept_targets — СЕРДЦЕ полного перехвата
# ═══════════════════════════════════════════════════════════

def test_перехват_без_рангов_возвращает_всех_живых():
    # Позиционка off → пул как сегодня {игрок + живые союзники}.
    hero, ally, dead = _c("hero"), _c("ally"), _c("dead", hp=0)
    assert intercept_targets([hero, ally, dead]) == [hero, ally]


def test_перехват_пока_жив_фронт_цель_только_фронт():
    hero = _c("hero", rank=Rank.FRONT)
    s1 = _c("s1", rank=Rank.BACK)
    s2 = _c("s2", rank=Rank.BACK)
    assert intercept_targets([hero, s1, s2]) == [hero]  # тыл недостижим


def test_перехват_фронт_пал_открывается_тыл():
    dead_front = _c("hero", hp=0, rank=Rank.FRONT)
    s1 = _c("s1", rank=Rank.BACK)
    s2 = _c("s2", rank=Rank.BACK)
    assert intercept_targets([dead_front, s1, s2]) == [s1, s2]


def test_перехват_зеркало_двое_во_фронте_танкуют():
    # mirrored: 2 саммона фронт, герой тыл.
    f1 = _c("s1", rank=Rank.FRONT)
    f2 = _c("s2", rank=Rank.FRONT)
    hero = _c("hero", rank=Rank.BACK)
    assert intercept_targets([f1, f2, hero]) == [f1, f2]
    f1.hp = 0  # один фронт пал — второй ещё держит
    assert intercept_targets([f1, f2, hero]) == [f2]
    f2.hp = 0  # фронт пуст — герой открыт
    assert intercept_targets([f1, f2, hero]) == [hero]


def test_перехват_все_мертвы_пустой_список():
    assert intercept_targets([_c("a", hp=0), _c("b", hp=0)]) == []
