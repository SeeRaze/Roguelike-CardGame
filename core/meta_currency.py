# core/meta_currency.py
# МЕТА-ВАЛЮТА «Опыт + Грейд» (С70) — фундамент петли прогрессии:
# «умер → накопил Опыт → крутишь казино / прошёл условие → открыл контент».
#
# Два счётчика по дизайну [[progression-design-s70]]:
#   • meta['xp']        — ТРАТИМАЯ валюта (крутка казино = N Опыта).
#   • meta['grade_xp']  — НАКОПИТЕЛЬНЫЙ счётчик, не тратится. Гонит ступени Грейда.
# grant_xp растит ОБА. spend_xp уменьшает только xp, grade_xp не трогает —
# Грейд фиксирует «жизненный опыт», его нельзя профукать в казино.
#
# 5 ступеней Грейда (имена-вехи карьеры IT, не должности — нет клэша с классами
# Стажёр/TechLead-Демиург):
#   L0 Onboarding   — 0      (старт, доступ в казино)
#   L1 Первый PR    — 150    (+ keepsake, +1 крутка)
#   L2 On-call      — 600    (+ перманент-бан казино)
#   L3 Архитектор   — 1800   (хардкор-режим + per-run бан тега в костре)
#   L4 CTO          — 4000   (нарративный маяк Демиурга)
# Пороги срезаны под альфу — калибровка после первого плейтеста.
#
# КОНТРАКТ «sim/baseline СЛЕП»: все функции принимают meta=None дефолтом, при None
# превращаются в no-op (grant возвращает meta=None как есть; spend → False; current
# → 0). Симулятор и baseline новые точки наполнения НЕ дёргают (точки висят за
# UI-фасадом в GameManager/SaveManager), но даже если случайно вызовут — гард не
# дрейфует. Чисто примитивы + dict, никаких pygame/игровых объектов → тривиально
# тестируется без боя.

# Пороги Грейда (накопительный grade_xp). Индексы 0..4 = L0..L4.
GRADE_THRESHOLDS = (0, 150, 600, 1800, 4000)

# Цена одной крутки казино — общая константа для UI и тестов.
CASINO_SPIN_COST = 100


def grant_xp(meta, amount: int) -> None:
    """Начислить Опыт: растит ОБА счётчика (xp тратимый + grade_xp накопительный).

    meta=None → no-op (sim/baseline-контракт). Отрицательный amount игнорируется
    (защита от багов вызывающего; уменьшение xp только через spend_xp)."""
    if meta is None or amount <= 0:
        return
    meta["xp"]       = int(meta.get("xp", 0)) + int(amount)
    meta["grade_xp"] = int(meta.get("grade_xp", 0)) + int(amount)


def spend_xp(meta, amount: int) -> bool:
    """Потратить Опыт. Возвращает True если хватило (и списано), False иначе.

    Уменьшает ТОЛЬКО meta['xp']; grade_xp не трогает — ступени Грейда фиксируют
    «жизненный опыт», его нельзя профукать в казино. meta=None или amount<=0
    или нехватка → False, мета не изменена."""
    if meta is None or amount <= 0:
        return False
    have = int(meta.get("xp", 0))
    if have < amount:
        return False
    meta["xp"] = have - int(amount)
    return True


def current_grade(meta) -> int:
    """Текущая ступень Грейда (0..4) по накопительному grade_xp.

    meta=None → 0. Возвращает максимальный индекс i, при котором
    grade_xp ≥ GRADE_THRESHOLDS[i]."""
    if meta is None:
        return 0
    gx = int(meta.get("grade_xp", 0))
    grade = 0
    for i, threshold in enumerate(GRADE_THRESHOLDS):
        if gx >= threshold:
            grade = i
    return grade


def next_threshold(meta):
    """Порог СЛЕДУЮЩЕЙ ступени Грейда. Возвращает int или None если уже L4.

    meta=None → GRADE_THRESHOLDS[1] (порог L1, удобный дефолт для UI первой строки)."""
    if meta is None:
        return GRADE_THRESHOLDS[1]
    g = current_grade(meta)
    if g + 1 >= len(GRADE_THRESHOLDS):
        return None
    return GRADE_THRESHOLDS[g + 1]


def xp_to_next(meta):
    """Сколько ещё накопить grade_xp до следующей ступени. None если уже L4.

    Удобно для UI-прогрессбара лестницы Грейда."""
    nxt = next_threshold(meta)
    if nxt is None:
        return None
    gx = 0 if meta is None else int(meta.get("grade_xp", 0))
    return max(0, nxt - gx)
