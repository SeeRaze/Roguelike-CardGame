# core/casino.py
# КАЗИНО мета-прогрессии (С70, Этап 2) — рандом-крутка залоченного контента
# за Опыт без дублей и с перманент-банами от L2 Грейда.
#
# КОНТРАКТ:
#   • Идемпотентность провалов: при ЛЮБОЙ ошибке (нет xp / пул пуст / нет меты)
#     мета не изменяется ВООБЩЕ. Списание xp идёт ПОСЛЕ всех проверок.
#   • Анти-дубль: успешно выкрученный id уходит в casino_seen → больше не выпадет
#     (и параллельно в meta['unlocks'] → is_card_unlocked/is_relic_unlocked сразу
#     его видят: namespace карт/реликвий не пересекается с classами).
#   • Перманент-бан: дополнительный слот фильтра. Капасити растёт со ступенью
#     Грейда (L0/L1=0, L2=1, L3=2, L4=3 — по дизайну [[progression-design-s70]]).
#   • sim/baseline СЛЕП: симулятор казино не дёргает, но meta=None во всех
#     функциях возвращает безопасный «отказ», не падает.
#
# Чистые примитивы + dict, без pygame и игровых объектов → тестируется без боя.

import random

from core import meta_currency, progression


def available_pool(meta) -> list:
    """Список доступных в крутке предметов: [(kind, id), ...], где
    kind ∈ {'card', 'relic'}. Исключает casino_seen (анти-дубль) и casino_bans.

    meta=None → пустой список (sim-контракт)."""
    if meta is None:
        return []
    seen = set(meta.get("casino_seen", []))
    bans = set(meta.get("casino_bans", []))
    out: list = []
    for cid in progression.casino_pool_cards():
        if cid in seen or cid in bans:
            continue
        out.append(("card", cid))
    for rid in progression.casino_pool_relics():
        if rid in seen or rid in bans:
            continue
        out.append(("relic", rid))
    return out


def try_spin(meta, rng=None) -> dict:
    """Попытка крутки казино: списать бесплатную крутку ИЛИ Опыт и выдать
    рандом-предмет из пула.

    Возвращает dict {'ok': bool, 'kind': str|None, 'id': str|None,
    'reason': str|None, 'free': bool}. free=True если списалась бесплатная крутка
    (бонус L1 Грейда), а не Опыт. Возможные reason: 'no_meta' / 'not_enough_xp' /
    'pool_empty' / None (при ok=True).

    Бесплатные крутки (meta['free_spins']) тратятся ПЕРВЫМИ — иначе игрок мог бы
    «сжечь» Опыт, имея бесплатную. Идемпотентность провала: мета НЕ мутируется ни
    при одной из ошибок — проверки → списание → запись id, в этом порядке. rng по
    умолчанию = модуль random (для тестов передаётся random.Random(seed))."""
    if meta is None:
        return {"ok": False, "kind": None, "id": None, "reason": "no_meta", "free": False}
    free = int(meta.get("free_spins", 0)) > 0
    if not free and int(meta.get("xp", 0)) < meta_currency.CASINO_SPIN_COST:
        return {"ok": False, "kind": None, "id": None,
                "reason": "not_enough_xp", "free": False}
    pool = available_pool(meta)
    if not pool:
        return {"ok": False, "kind": None, "id": None, "reason": "pool_empty", "free": False}

    chooser = rng if rng is not None else random
    # Стабильный порядок: список из множеств приходит в порядке итерации set'а
    # (Python: insertion-агностично, но для одного запуска детерминирован).
    # Для теста-воспроизводимости важно: чтобы random.Random(seed) был детерминирован,
    # отсортируем пул — иначе порядок set влияет на выбор.
    pool_sorted = sorted(pool, key=lambda kv: (kv[0], kv[1]))
    kind, item_id = chooser.choice(pool_sorted)

    # Бесплатная крутка тратится первой; иначе списываем Опыт (spend_xp вернёт True —
    # баланс уже проверен).
    if free:
        meta["free_spins"] = int(meta.get("free_spins", 0)) - 1
    else:
        meta_currency.spend_xp(meta, meta_currency.CASINO_SPIN_COST)
    meta.setdefault("casino_seen", []).append(item_id)
    # Грант в общий список анлоков → is_card_unlocked/is_relic_unlocked сразу True
    # (см. core/progression.py — namespace классов/карт/реликвий не пересекается).
    unlocks = meta.setdefault("unlocks", [])
    if item_id not in unlocks:
        unlocks.append(item_id)
    return {"ok": True, "kind": kind, "id": item_id, "reason": None, "free": free}


# ─── Перманент-баны (L2+ Грейд) ───────────────────────────────────────────────

def bans_capacity(meta) -> int:
    """Сколько перманент-банов разрешено по текущей ступени Грейда.

    L0/L1 = 0 (фича закрыта), L2 = 1, L3 = 2, L4 = 3 (+1 слот за каждую ступень
    выше L1). meta=None → 0."""
    if meta is None:
        return 0
    grade = meta_currency.current_grade(meta)
    return max(0, grade - 1)


def can_ban(meta) -> bool:
    """Можно ли добавить ещё один перманент-бан (капасити Грейда не выбран)?"""
    if meta is None:
        return False
    return len(meta.get("casino_bans", [])) < bans_capacity(meta)


def ban_item(meta, item_id: str) -> bool:
    """Перманент-бан предмета казино. True если бан успешно применён.

    Отказы (вернёт False, мета не мутируется):
      - meta=None;
      - item_id не в пуле казино (только запрещаем предметы, которые МОГЛИ бы
        выпасть — баны на ачивочные/стартовые предметы абсурдны);
      - капасити выбран (нужно достичь следующей ступени Грейда);
      - дубль (уже в casino_bans)."""
    if meta is None:
        return False
    if item_id not in progression.casino_pool_cards() \
            and item_id not in progression.casino_pool_relics():
        return False
    if not can_ban(meta):
        return False
    bans = meta.setdefault("casino_bans", [])
    if item_id in bans:
        return False
    bans.append(item_id)
    return True
