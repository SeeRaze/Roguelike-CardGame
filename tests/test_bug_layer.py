# tests/test_bug_layer.py
# Слой БАГОВ / технического долга (ярус 1, С59). Проверяем:
#   - несыгрываемость (гейт в play_card_by_index не тратит энергию, карта остаётся);
#   - ACCRUE навешивает Баг в gm.current_deck (персист между боями);
#   - DEBUG вычищает Баг из руки И перманентно из gm.current_deck;
#   - классификатор UI красит Баг ключом 'bug';
#   - сейв-раундтрип: card_id='bug', make_card_by_id воссоздаёт несыгрываемый Баг.
from types import SimpleNamespace

from core.players import Warrior
from core.enemies.cultist import Cultist
from core.cards import create_strike
from core.cards.bug import create_bug, AccrueBugEffect, DebugBugEffect
from core.cards.base import Card, DamageEffect
from managers.CombatManager import CombatManager


def _make_cm(deck):
    """CombatManager, где gm.current_deck — ТОТ ЖЕ список, что колода боя (как в живой
    игре: gm.current_deck передаётся в DeckManager.pool). ACCRUE/DEBUG работают с ним."""
    p = Warrior()
    e = Cultist("Культист", 30, 30)
    gm = SimpleNamespace(current_deck=deck, relics=[])
    return CombatManager(p, e, deck, game_manager=gm)


# ── Несыгрываемость ──────────────────────────────────────────────────────────

def test_баг_несыгрываем_энергия_не_тратится():
    deck = [create_bug(), create_strike()]
    cm = _make_cm(deck)
    cm.player.energy = 3
    idx = next(i for i, c in enumerate(cm.deck_manager.hand)
               if getattr(c, "unplayable", False))
    hand_before = len(cm.deck_manager.hand)
    result = cm.play_card_by_index(idx)
    assert result is False
    assert cm.player.energy == 3                       # энергия не тронута
    assert len(cm.deck_manager.hand) == hand_before    # Баг остался в руке
    assert not cm.deck_manager.discard_pile            # не ушёл в сброс


def test_баг_создаётся_несыгрываемым():
    bug = create_bug()
    assert bug.unplayable is True
    assert bug.effects == []


def test_обычная_карта_по_умолчанию_сыгрываема():
    assert create_strike().unplayable is False


# ── ACCRUE ───────────────────────────────────────────────────────────────────

def test_accrue_навешивает_баг_в_колоду_забега():
    deck = [create_strike()]
    cm = _make_cm(deck)
    eff = AccrueBugEffect(1)
    eff.execute(cm.player, cm.enemies[0], cm, is_upgraded=False)
    bugs = [c for c in deck if getattr(c, "unplayable", False)]
    assert len(bugs) == 1
    assert bugs[0].name == "Баг"


def test_accrue_несколько_багов():
    deck = [create_strike()]
    cm = _make_cm(deck)
    AccrueBugEffect(3).execute(cm.player, cm.enemies[0], cm, is_upgraded=False)
    assert sum(1 for c in deck if getattr(c, "unplayable", False)) == 3


def test_accrue_no_op_без_gm():
    # Синтетический бой без gm/current_deck — не падаем, ничего не навешиваем.
    deck = [create_strike()]
    p = Warrior()
    e = Cultist("Культист", 30, 30)
    cm = CombatManager(p, e, deck, game_manager=None)
    AccrueBugEffect(1).execute(p, e, cm, is_upgraded=False)
    assert not any(getattr(c, "unplayable", False) for c in deck)


# ── DEBUG (counterplay) ──────────────────────────────────────────────────────

def test_debug_вычищает_баг_из_руки_и_колоды():
    deck = [create_bug(), create_strike()]
    cm = _make_cm(deck)
    # Баг в руке (вся колода добралась — рука ≤ pool; форсируем наличие в руке).
    bug = next(c for c in cm.deck_manager.hand if getattr(c, "unplayable", False))
    DebugBugEffect(1).execute(cm.player, cm.enemies[0], cm, is_upgraded=False)
    assert bug not in cm.deck_manager.hand
    assert bug not in deck                              # перманентно из колоды забега


def test_debug_бьёт_только_по_багам():
    deck = [create_bug(), create_strike()]
    cm = _make_cm(deck)
    strike = next(c for c in cm.deck_manager.hand if not getattr(c, "unplayable", False))
    DebugBugEffect(5).execute(cm.player, cm.enemies[0], cm, is_upgraded=False)
    assert strike in cm.deck_manager.hand              # обычную карту не тронул
    assert not any(getattr(c, "unplayable", False) for c in cm.deck_manager.hand)


def test_debug_no_op_без_багов():
    deck = [create_strike()]
    cm = _make_cm(deck)
    hand_before = list(cm.deck_manager.hand)
    DebugBugEffect(1).execute(cm.player, cm.enemies[0], cm, is_upgraded=False)
    assert cm.deck_manager.hand == hand_before


def test_debug_лимит_count():
    deck = [create_bug(), create_bug(), create_bug(), create_strike()]
    cm = _make_cm(deck)
    DebugBugEffect(2).execute(cm.player, cm.enemies[0], cm, is_upgraded=False)
    remaining = sum(1 for c in deck if getattr(c, "unplayable", False))
    assert remaining == 1                              # вычистил ровно 2 из 3


# ── UI классификатор ─────────────────────────────────────────────────────────

def test_классификатор_красит_баг():
    from ui.cards.classifier import classify_card
    assert classify_card(create_bug()) == "bug"


def test_палитра_имеет_ключ_bug():
    from ui.cards.data import card_palette
    bg, border = card_palette("bug")
    assert bg and border


# ── Сейв-раундтрип ───────────────────────────────────────────────────────────

def test_баг_сериализуется_и_воссоздаётся():
    from core.cards.catalog import card_id_of, make_card_by_id
    cid = card_id_of(create_bug())
    assert cid == "bug"
    restored = make_card_by_id("bug")
    assert restored is not None
    assert restored.unplayable is True
    assert restored.name == "Баг"


def test_баг_не_в_пуле_выдачи():
    # Баг НЕ драфтится: его нет в generic-пуле любого класса.
    from core.cards.catalog import get_pool_for_class
    pool = get_pool_for_class("Warrior")
    names = [f().name for f in pool]
    assert "Баг" not in names
