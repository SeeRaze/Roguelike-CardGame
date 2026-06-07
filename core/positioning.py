# core/positioning.py
# ПОЗИЦИОНКА 3×3 — кейстоун (§1 ЯДРО). ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ о позиции существ.
#
# Зачем: позиция = СУБСТРАТ, на котором висит половина Парадокс-режима и грядущий
# class-redesign. Здесь — только МЕХАНИЗМ (где существо стоит и кто по нему может
# попасть), class-agnostic. Класс-специфику (стяжка/симпатия/призыв) строим
# КИРПИЧАМИ поверх, не вшивая в этот модуль.
#
# Это ЧИСТЫЙ модуль: только данные + пьюр-хелперы запроса. Без pygame, без боевой
# логики, без побочек (тестируется без SDL). Сетка — это ИНДЕКС над существующими
# списками (player+allies / enemies), а НЕ новый источник правды: существа живут в
# своих списках, позиция — лишь атрибут `rank` на существе (дефолт None → инертно).
# Так нет параллельной структуры, которая может рассинхрониться (урок бага cm.enemy).
#
# ── Срез v1 (развилки §2 спеки закрыты с юзером) ─────────────────────────────────
# • Ось РАНГА фронт/тыл на СТОРОНЕ ИГРОКА (партия = [player] + allies). Враги пока
#   «толпа» без сетки.
# • ПЕРЕХВАТ строго ПОЛНЫЙ: пока жив ФРОНТ — одиночный урон в ТЫЛ не проходит
#   (intercept_targets). AoE бьёт всех (мимо этого хелпера). Без рангов (позиционка
#   off) intercept_targets возвращает всех живых → поведение байт-в-байт сегодня.
# • РАСКЛАДКА = 3 слота. Дефолт 1 фронт + 2 тыл (герой танкует, союзники сзади).
#   ЗЕРКАЛО (класс типа призывателя): 2 фронт + 1 тыл (саммоны танкуют, герой в тылу).
#   Один булев флаг mirrored переворачивает и сплит (1/2 ↔ 2/1), и кто-где (§3).


class Rank:
    """Ранг существа в партии. Бинарная ось v1 (будущее: + ось линий → полная 3×3).

    Значения — строки (а не Enum): просто, читабельно, сериализуемо для сейва.
    `rank == None` означает «позиции нет» (позиционка выключена) → всё инертно."""

    FRONT = "front"   # авангард: перехватывает одиночный урон за тыл
    BACK  = "back"    # арьергард: защищён, пока жив фронт

    ALL = (FRONT, BACK)


# Раскладки партии как ДАННЫЕ (ёмкости утверждены юзером). Всего 3 слота.
# Дефолт: герой один во фронте, союзники сзади. Зеркало: инверсия сплита.
DEFAULT_LAYOUT  = {Rank.FRONT: 1, Rank.BACK: 2}
MIRRORED_LAYOUT = {Rank.FRONT: 2, Rank.BACK: 1}


def party_layout(mirrored: bool = False) -> dict:
    """Ёмкости слотов партии по флагу зеркала. Дефолт 1/2, зеркало 2/1."""
    return dict(MIRRORED_LAYOUT if mirrored else DEFAULT_LAYOUT)


def slot_capacity(rank: str, mirrored: bool = False) -> int:
    """Сколько существ помещается в данный ранг при данной раскладке."""
    return party_layout(mirrored).get(rank, 0)


# ── Пьюр-хелперы запроса (работают над ЛЮБОЙ итерируемой партией существ) ─────────

def living(creatures) -> list:
    """Только живые (hp > 0), порядок исходный."""
    return [c for c in creatures if c.hp > 0]


def has_positions(creatures) -> bool:
    """Есть ли у кого-то из существ заданный ранг (позиционка включена)?
    Если ни у кого нет ранга → позиционка off → таргетинг ведёт себя как сегодня."""
    return any(getattr(c, "rank", None) is not None for c in creatures)


def front_rank(creatures) -> list:
    """Живые существа во ФРОНТЕ."""
    return [c for c in creatures if c.hp > 0 and getattr(c, "rank", None) == Rank.FRONT]


def back_rank(creatures) -> list:
    """Живые существа в ТЫЛУ."""
    return [c for c in creatures if c.hp > 0 and getattr(c, "rank", None) == Rank.BACK]


def intercept_targets(party) -> list:
    """СЕРДЦЕ полного перехвата: допустимые цели ОДИНОЧНОЙ атаки врага по партии.

    Правило: пока жив ФРОНТ — целью может быть только фронт; когда фронт пал —
    становится доступен ТЫЛ. Если рангов нет вовсе (позиционка off) — возвращаем
    всех живых, что байт-в-байт повторяет старый пул {игрок + живые союзники}.

    AoE сюда НЕ ходит (бьёт всех мимо перехвата). Хелпер ПЬЮР: только читает hp/rank,
    ничего не мутирует — вызывающий код сам делает random.choice по результату."""
    alive = living(party)
    front = [c for c in alive if getattr(c, "rank", None) == Rank.FRONT]
    if front:
        return front
    back = [c for c in alive if getattr(c, "rank", None) == Rank.BACK]
    if back:
        return back
    return alive


# ── Расстановка партии (§3) ──────────────────────────────────────────────────────

def assign_party_ranks(player, allies=None, mirrored: bool = False) -> list:
    """Расставить партию по рангам. Дефолт: герой во ФРОНТЕ, союзники в ТЫЛУ.
    ЗЕРКАЛО (mirrored=True, класс типа призывателя): инверсия — союзники во ФРОНТЕ
    (танкуют), герой в ТЫЛУ.

    (Пере)назначает .rank У ВСЕХ членов партии при каждом вызове — поэтому вызов на
    старте каждого боя сам ПО СЕБЕ сбрасывает протухшие ранги: персистентная стая
    переставляется заново, без утечки расстановки прошлого боя.

    Расстановка БИНАРНАЯ (герой vs союзники). Жёсткие ёмкости слотов (party_layout
    2/1) — забота UI/§5: разнос N союзников по слотам и показ капа делаем там.
    Возвращает партию [player] + allies (порядок: герой первым)."""
    allies = allies or []
    hero_rank, ally_rank = (
        (Rank.BACK, Rank.FRONT) if mirrored else (Rank.FRONT, Rank.BACK)
    )
    player.rank = hero_rank
    for ally in allies:
        ally.rank = ally_rank
    return [player] + list(allies)


# ════════════════════════════════════════════════════════════════════════════════
# v2 — ПОЛНАЯ 2D-СЕТКА: ось ЛИНИЙ ортогонально РАНГУ (С48)
# ════════════════════════════════════════════════════════════════════════════════
# Срез v1 дал ось РАНГА (фронт/тыл) на стороне игрока. v2 добавляет ось ЛИНИЙ
# (лево/центр/право) ОРТОГОНАЛЬНО → настоящая 2D-решётка (line × rank) для ОБЕИХ
# сторон. Цель — субстрат «по всем осям»: EffectCalculator получает понятия «соседняя
# ячейка» (neighbors) и «вертикальный ряд» (column) под будущие AoE/сплеш/детонации
# соседей. Смысл клеток (механики) вешаем КОНТЕНТОМ позже; здесь — только координаты
# и пьюр-ридеры. Всё аддитивно и ИНЕРТНО: `line == None` (дефолт) → хелперы пусты,
# v1-перехват и расстановка не задеты, baseline зелёный.


class Line:
    """Ось ЛИНИЙ (горизонталь) 2D-сетки: лево/центр/право. Ортогональна `Rank`.

    Значения — строки (как у Rank): просто, читабельно, сериализуемо для сейва.
    `line == None` означает «линии нет» (позиционка off / только-ранг) → инертно."""

    LEFT   = "left"     # левая колонка
    CENTER = "center"   # центральная колонка
    RIGHT  = "right"    # правая колонка

    ALL = (LEFT, CENTER, RIGHT)


# Индексы осей для МЕТРИКИ СОСЕДСТВА (манхэттен по сетке).
_LINE_INDEX = {Line.LEFT: 0, Line.CENTER: 1, Line.RIGHT: 2}
_RANK_INDEX = {Rank.FRONT: 0, Rank.BACK: 1}


# Т-ОБРАЗНЫЕ 2D-раскладки как ДАННЫЕ (refinement v1: те же 3 слота + ось линий).
# Дефолт: герой (ЦЕНТР, ФРОНТ) танкует, 2 союзника по краям тыла (ЛЕВО/ПРАВО, ТЫЛ).
# Зеркало (класс типа призывателя): 2 саммона по краям фронта (ЛЕВО/ПРАВО, ФРОНТ)
# танкуют, герой в центре тыла (ЦЕНТР, ТЫЛ). v1 «1 фронт / 2 тыл» = частный случай.
DEFAULT_GRID = {
    Rank.FRONT: [Line.CENTER],
    Rank.BACK:  [Line.LEFT, Line.RIGHT],
}
MIRRORED_GRID = {
    Rank.FRONT: [Line.LEFT, Line.RIGHT],
    Rank.BACK:  [Line.CENTER],
}


def party_grid(mirrored: bool = False) -> dict:
    """2D-раскладка слотов (rank → список занятых линий) по флагу зеркала."""
    src = MIRRORED_GRID if mirrored else DEFAULT_GRID
    return {rank: list(lines) for rank, lines in src.items()}


def grid_slots(mirrored: bool = False) -> list:
    """Плоский ДЕТЕРМИНИРОВАННЫЙ список занятых клеток (line, rank) раскладки.
    Порядок: по рангам (фронт→тыл), внутри ранга — по объявлению линий. Используется
    UI/расстановкой (§9/§11) для разноса существ по клеткам."""
    grid = party_grid(mirrored)
    return [(line, rank) for rank in Rank.ALL for line in grid.get(rank, [])]


# ── Пьюр-ридеры 2D (читают line/rank существ, ничего не мутируют) ─────────────────

def cell(creature):
    """Клетка существа как (line, rank), либо None если позиция не задана полностью
    (нет line ИЛИ нет rank → существо вне 2D-сетки → инертно для соседства)."""
    line = getattr(creature, "line", None)
    rank = getattr(creature, "rank", None)
    if line is None or rank is None:
        return None
    return (line, rank)


def _adjacent(cell_a, cell_b) -> bool:
    """Ортогональное соседство в сетке: манхэттен-расстояние ровно 1.
    |Δline| + |Δrank| == 1 → соседи (горизонталь в ряду ИЛИ вертикаль в колонке).
    Диагонали соседями НЕ считаются. Неизвестные значения осей → не соседи."""
    line_a, rank_a = cell_a
    line_b, rank_b = cell_b
    if line_a not in _LINE_INDEX or line_b not in _LINE_INDEX:
        return False
    if rank_a not in _RANK_INDEX or rank_b not in _RANK_INDEX:
        return False
    dist = (abs(_LINE_INDEX[line_a] - _LINE_INDEX[line_b])
            + abs(_RANK_INDEX[rank_a] - _RANK_INDEX[rank_b]))
    return dist == 1


def neighbors(creature, party) -> list:
    """Живые существа в ОРТОГОНАЛЬНО соседних клетках — под «соседняя ячейка»
    (AoE/сплеш/детонация соседей). Соседство = манхэттен-1 по сетке. Само существо
    исключено. Без полной позиции у creature → пусто (инертно, baseline зелёный)."""
    me = cell(creature)
    if me is None:
        return []
    out = []
    for other in party:
        if other is creature or other.hp <= 0:
            continue
        oc = cell(other)
        if oc is not None and _adjacent(me, oc):
            out.append(other)
    return out


def column(line, party) -> list:
    """Живые существа в одной ЛИНИИ (вертикальный ряд: фронт+тыл колонки) —
    под «вертикальный ряд» (удар по колонке). Без линий у партии → пусто."""
    return [c for c in party if c.hp > 0 and getattr(c, "line", None) == line]


def same_rank(rank, party) -> list:
    """Живые существа в одном РАНГЕ (горизонтальный ряд). Обобщение front_rank/
    back_rank на произвольный ранг (удар по ряду)."""
    return [c for c in party if c.hp > 0 and getattr(c, "rank", None) == rank]


# ── Расстановка ВРАГОВ (§8) — зеркало партии: враги тоже на сетке ─────────────────

def assign_enemy_ranks(enemies) -> list:
    """Расставить ВРАГОВ по рангам (фронт/тыл) — симметрия v1 (С48, §8).

    Политика: ФРОНТ получает первую ПОЛОВИНУ группы (округление вверх), остальные —
    ТЫЛ. Параметр-фри, масштабируется с размером группы: 1→1Ф · 2→1Ф/1Б · 3→2Ф/1Б ·
    4→2Ф/2Б. Даёт НЕПУСТОЙ фронт → перехват игрок→враг работает (жив фронт врага →
    одиночный урон не доходит до тыла; intercept_targets(enemies) даёт цель).

    Назначает .rank над ВСЕМ списком по индексу (на старте боя все живы). Перехват
    далее сам открывает тыл, когда живой фронт иссяк — re-promote не нужен. line
    (ось 2D) добавит §9; здесь только ось РАНГА."""
    enemies = list(enemies)
    n = len(enemies)
    if n == 0:
        return enemies
    front_count = (n + 1) // 2          # первая половина (округление вверх) — фронт
    for i, enemy in enumerate(enemies):
        enemy.rank = Rank.FRONT if i < front_count else Rank.BACK
    return enemies
