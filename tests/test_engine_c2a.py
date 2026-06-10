# tests/test_engine_c2a.py
# ENGINE C2a — топливо + фильтр (манипуляция своими ресурсами).
from core.players.warrior import Warrior
from core.enemies import Cultist
from core.cards.basic import create_strike, create_heavy_blade, create_defend
from core.cards.shortcuts import (
    create_window_swap, create_refresh, create_coffee_break,
    create_hard_delete, create_stack_trace,
)
from managers.CombatManager import CombatManager


def _cm():
    return CombatManager(Warrior(), Cultist("K", 100, 100), [create_strike()])


def _play(cm, card, hand_extra=None):
    """Положить карту в руку (как _card_being_played) и применить эффект."""
    dm = cm.deck_manager
    dm.hand = [card] + (hand_extra or [])
    cm._card_being_played = card
    card.apply(cm.player, cm.enemies[0], cm)


# ─── 🔋 ТОПЛИВО ──────────────────────────────────────────────────────────────
def test_refresh_draws():
    cm = _cm()
    cm.deck_manager.hand = []
    cm.deck_manager.draw_pile = [create_strike(), create_strike(), create_strike()]
    create_refresh().apply(cm.player, cm.enemies[0], cm)
    assert len(cm.deck_manager.hand) == 2


def test_coffee_break_gives_energy():
    cm = _cm()
    cm.player.energy = 3
    create_coffee_break().apply(cm.player, cm.enemies[0], cm)
    assert cm.player.energy == 5


def test_window_swap_discards_others_redraws():
    cm = _cm()
    card = create_window_swap()
    others = [create_strike(), create_strike()]      # 2 прочих в руке
    cm.deck_manager.draw_pile = [create_defend(), create_defend(), create_defend()]
    _play(cm, card, hand_extra=others)
    # 2 прочих сброшены, добрано 2; карта-носитель ещё в руке (изымёт cardplay).
    assert card in cm.deck_manager.hand
    assert len(cm.deck_manager.hand) == 3            # self + 2 добранных
    assert all(c in cm.deck_manager.discard_pile for c in others)


# ─── 🔍 ФИЛЬТР ───────────────────────────────────────────────────────────────
def test_hard_delete_exiles_a_hand_card():
    cm = _cm()
    card = create_hard_delete()
    victim = create_strike()
    _play(cm, card, hand_extra=[victim])
    assert victim in cm.deck_manager.exile_pile
    assert victim not in cm.deck_manager.hand


def test_stack_trace_dumps_costliest_top():
    cm = _cm()
    cheap = create_strike()       # cost 1
    pricey = create_heavy_blade()  # cost 2
    cm.deck_manager.draw_pile = [cheap, pricey]   # верх = последние
    create_stack_trace().apply(cm.player, cm.enemies[0], cm)
    # Самая дорогая из верхних → в сброс.
    assert pricey in cm.deck_manager.discard_pile
    assert pricey not in cm.deck_manager.draw_pile
