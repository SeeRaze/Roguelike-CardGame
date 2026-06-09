# tests/test_starter_pool.py
# Узкий стартовый пул (С57, step 1 капстоуна): фильтрация пула карт по анлокам.
# meta=None → весь пул (обр. совместимость, сим не задет); meta → фильтр по unlocks.

import core.progression as prog
from core.progression import LOCKED_CARDS, LOCKED_RELICS, relic_id_for
from core.cards.catalog import (
    GENERIC_FACTORIES, get_pool_for_class, card_id_for,
)
from core.relics import ALL_RELICS


def _meta(*unlocks) -> dict:
    return {"stats": {}, "unlocks": list(unlocks)}


# ── К2: фильтр пула ──────────────────────────────────────────────────────────
def test_meta_none_возвращает_весь_пул():
    # Обратная совместимость: без меты фильтра нет (сим/baseline видят всё).
    full = get_pool_for_class("Warrior")
    assert len(full) == len(GENERIC_FACTORIES) + 6   # generic + 6 классовых Воина


def test_meta_none_не_фильтрует_даже_при_locked(monkeypatch):
    # Даже если карта locked, meta=None отдаёт её (сим обязан остаться full-access).
    monkeypatch.setattr(prog, "LOCKED_CARDS", {"fire_breath"})
    names = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=None)}
    assert "fire_breath" in names


def test_meta_фильтрует_locked_карту(monkeypatch):
    monkeypatch.setattr(prog, "LOCKED_CARDS", {"fire_breath"})
    # Новый игрок (пустые unlocks) — fire_breath отфильтрован, strike остался.
    ids = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=_meta())}
    assert "fire_breath" not in ids
    assert "strike" in ids


def test_анлок_возвращает_карту_в_пул(monkeypatch):
    monkeypatch.setattr(prog, "LOCKED_CARDS", {"fire_breath"})
    ids = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=_meta("fire_breath"))}
    assert "fire_breath" in ids


def test_пустой_locked_пул_не_меняется(monkeypatch):
    # Фильтр инертен при пустом LOCKED_CARDS: meta-фильтр == полному пулу.
    monkeypatch.setattr(prog, "LOCKED_CARDS", set())
    filtered = get_pool_for_class("Mage", meta=_meta())
    assert len(filtered) == len(get_pool_for_class("Mage"))


# ── К3: целостность разметки + состав стартового пула ────────────────────────
def test_все_locked_карты_существуют_в_пуле():
    # Защита от опечаток/дрейфа: каждый LOCKED card_id — реальная generic-карта.
    real = {card_id_for(f) for f in GENERIC_FACTORIES}
    bogus = LOCKED_CARDS - real
    assert not bogus, f"LOCKED_CARDS содержит несуществующие id: {bogus}"


def test_все_locked_артефакты_существуют():
    real = {relic_id_for(r) for r in ALL_RELICS}
    bogus = LOCKED_RELICS - real
    assert not bogus, f"LOCKED_RELICS содержит несуществующие id: {bogus}"


def test_стартовый_generic_пул_ровно_13_карт():
    # Новый игрок (пустые unlocks) видит только стартовые generic (13) + класс.
    ids = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=_meta())}
    generic_ids = ids & {card_id_for(f) for f in GENERIC_FACTORIES}
    assert len(generic_ids) == 13
    assert "strike" in generic_ids
    assert "fire_breath" not in generic_ids   # locked


def test_классовые_сигнатурки_остаются_у_нового_игрока():
    # Тир-1 сигнатурки не заперты (стартдеки не трогаем) → видны при пустых unlocks.
    ids = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=_meta())}
    # 13 стартовых generic + 6 классовых Воина = 19.
    assert len(ids) == 19
