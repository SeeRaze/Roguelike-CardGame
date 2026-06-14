# tests/test_starter_pool.py
# Узкий стартовый пул (С57, step 1 капстоуна): фильтрация пула карт по анлокам.
# meta=None → весь пул (обр. совместимость, сим не задет); meta → фильтр по unlocks.

import core.progression as prog
from core.progression import LOCKED_CARDS, LOCKED_RELICS, relic_id_for
from core.cards.catalog import (
    GENERIC_FACTORIES, CLASS_FACTORIES, get_pool_for_class, card_id_for,
)
from core.relics import ALL_RELICS


def _meta(*unlocks) -> dict:
    return {"stats": {}, "unlocks": list(unlocks)}


# ── К2: фильтр пула ──────────────────────────────────────────────────────────
def test_meta_none_возвращает_весь_пул():
    # Обратная совместимость: без меты фильтра нет (сим/baseline видят всё).
    full = get_pool_for_class("Warrior")
    assert len(full) == len(GENERIC_FACTORIES) + 3   # generic + 3 классовых Воина (С57: ось Дисц)


def test_meta_none_не_фильтрует_даже_при_locked(monkeypatch):
    # Даже если карта locked, meta=None отдаёт её (сим обязан остаться full-access).
    monkeypatch.setattr(prog, "LOCKED_CARDS", {"tech_debt"})
    names = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=None)}
    assert "tech_debt" in names


def test_meta_фильтрует_locked_карту(monkeypatch):
    monkeypatch.setattr(prog, "LOCKED_CARDS", {"tech_debt"})
    # Новый игрок (пустые unlocks) — tech_debt отфильтрован, commit остался.
    ids = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=_meta())}
    assert "tech_debt" not in ids
    assert "commit" in ids


def test_анлок_возвращает_карту_в_пул(monkeypatch):
    monkeypatch.setattr(prog, "LOCKED_CARDS", {"tech_debt"})
    ids = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=_meta("tech_debt"))}
    assert "tech_debt" in ids


def test_пустой_locked_пул_не_меняется(monkeypatch):
    # Фильтр инертен при пустом LOCKED_CARDS: meta-фильтр == полному пулу.
    monkeypatch.setattr(prog, "LOCKED_CARDS", set())
    filtered = get_pool_for_class("Mage", meta=_meta())
    assert len(filtered) == len(get_pool_for_class("Mage"))


# ── К3: целостность разметки + состав стартового пула ────────────────────────
def test_все_locked_карты_существуют_в_пуле():
    # Защита от опечаток/дрейфа: каждый LOCKED card_id — реальная карта пула
    # (generic ИЛИ классовая — фильтр анлоков get_pool_for_class гейтит и те, и те;
    # Этап 3: классовые Rare-капстоуны Стажёра тоже запираются через LOCKED_CARDS).
    real = {card_id_for(f) for f in GENERIC_FACTORIES}
    for facs in CLASS_FACTORIES.values():
        real |= {card_id_for(f) for f in facs}
    bogus = LOCKED_CARDS - real
    assert not bogus, f"LOCKED_CARDS содержит несуществующие id: {bogus}"


def test_все_locked_артефакты_существуют():
    real = {relic_id_for(r) for r in ALL_RELICS}
    bogus = LOCKED_RELICS - real
    assert not bogus, f"LOCKED_RELICS содержит несуществующие id: {bogus}"


def test_стартовый_generic_пул_ровно_12_карт():
    # Новый игрок (пустые unlocks) видит только стартовые generic (12) + класс.
    # С60 (задача 4): флат (4) ушёл, пол цикла разработки — 3 COMMON открыты,
    # Песочница (4-я) заперта → 12−4+3 = 11; +1 Кофеин-овердос (контент-волна
    # Стажёр, Этап 1: generic СТАРТОВАЯ) = 12.
    ids = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=_meta())}
    generic_ids = ids & {card_id_for(f) for f in GENERIC_FACTORIES}
    assert len(generic_ids) == 12
    assert "commit" in generic_ids
    assert "caffeine_overdose" in generic_ids   # Этап 1: новая generic СТАРТОВАЯ
    assert "sandbox" not in generic_ids     # locked (UNCOMMON-награда)
    assert "tech_debt" not in generic_ids   # locked


def test_классовые_сигнатурки_остаются_у_нового_игрока():
    # Тир-1 сигнатурки не заперты (стартдеки не трогаем) → видны при пустых unlocks.
    ids = {card_id_for(f) for f in get_pool_for_class("Warrior", meta=_meta())}
    # 12 стартовых generic (+Кофеин-овердос, Этап 1) + 3 классовых Воина
    # (С57: ось Дисц, старая ось вычищена) = 15.
    assert len(ids) == 15
