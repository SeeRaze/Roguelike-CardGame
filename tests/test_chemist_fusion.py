# tests/test_chemist_fusion.py
# Card Fusion этап 2 (С51), МЕХАНИЗМ слияния руки: CombatManager.fuse_hand_cards
# (гейт fusion_enabled + тормоз Реагентом + транзиентный Глитч в руку) и приток
# Реагента в start_turn_phase. Нестабильность/числа — этап 3.

from core.players import Chemist, Warrior
from core.players.chemist import REAGENT_PER_TURN
from core.enemies.cultist import Cultist
from core.cards import create_strike, create_defend, create_coffee_spill
from core.fusion import FUSION_REAGENT_COST, MAX_FUSED_EFFECTS
from managers.CombatManager import CombatManager


def _cm(player, deck=None):
    e = Cultist("Культист", 30, 30)
    d = deck if deck is not None else [create_strike(), create_strike(), create_defend()]
    return CombatManager(player, e, d)


# ── приток Реагента ────────────────────────────────────────────────────────────────

def test_реагент_капает_в_начало_хода_у_химика():
    cm = _cm(Chemist())
    # start_turn_phase уже вызван в __init__ → 1 приток.
    assert cm.player.reagent == REAGENT_PER_TURN
    cm.start_turn_phase()
    assert cm.player.reagent == REAGENT_PER_TURN * 2


def test_реагент_не_капает_другим_классам():
    cm = _cm(Warrior())
    assert cm.player.reagent == 0
    cm.start_turn_phase()
    assert cm.player.reagent == 0


# ── механизм слияния ───────────────────────────────────────────────────────────────

def test_слияние_создаёт_глитч_в_руке():
    cm = _cm(Chemist(), deck=[create_strike(), create_coffee_spill(), create_defend()])
    cm.player.reagent = 5
    hand_before = len(cm.deck_manager.hand)
    a, b = 0, 1
    name_a = cm.deck_manager.hand[a].name
    name_b = cm.deck_manager.hand[b].name
    ok = cm.fuse_hand_cards(a, b)
    assert ok is True
    # рука уменьшилась на 1 (две карты → одна Глитч)
    assert len(cm.deck_manager.hand) == hand_before - 1
    glitch = next(c for c in cm.deck_manager.hand if getattr(c, "is_fused", False))
    assert glitch.fused_from == (name_a, name_b)
    # оригиналы ушли в discard (вернутся в пул следующего боя)
    assert name_a in [c.name for c in cm.deck_manager.discard_pile]


def test_слияние_тратит_реагент():
    cm = _cm(Chemist(), deck=[create_strike(), create_coffee_spill(), create_defend()])
    cm.player.reagent = 3
    cm.fuse_hand_cards(0, 1)
    assert cm.player.reagent == 3 - FUSION_REAGENT_COST


def test_слияние_отказ_без_реагента():
    cm = _cm(Chemist(), deck=[create_strike(), create_coffee_spill(), create_defend()])
    cm.player.reagent = 0
    hand_before = len(cm.deck_manager.hand)
    assert cm.fuse_hand_cards(0, 1) is False
    assert len(cm.deck_manager.hand) == hand_before   # рука не тронута


def test_слияние_отказ_у_не_химика():
    # Гейт доступа: у Воина fusion_enabled=False → механизм инертен даже с Реагентом.
    cm = _cm(Warrior(), deck=[create_strike(), create_coffee_spill(), create_defend()])
    cm.player.reagent = 5
    assert cm.fuse_hand_cards(0, 1) is False


def test_слияние_отказ_совпадающие_индексы():
    cm = _cm(Chemist())
    cm.player.reagent = 5
    assert cm.fuse_hand_cards(1, 1) is False


def test_слияние_отказ_невалидный_индекс():
    cm = _cm(Chemist())
    cm.player.reagent = 5
    assert cm.fuse_hand_cards(0, 99) is False


def test_слияние_отказ_превышение_капа_эффектов():
    # Две карты, у каждой эффектов столько, что сумма > MAX_FUSED_EFFECTS.
    cm = _cm(Chemist(), deck=[create_strike(), create_strike(), create_defend()])
    cm.player.reagent = 5
    a, b = cm.deck_manager.hand[0], cm.deck_manager.hand[1]
    # искусственно раздуваем списки эффектов выше капа
    a.effects = a.effects * (MAX_FUSED_EFFECTS)
    b.effects = b.effects * (MAX_FUSED_EFFECTS)
    reagent_before = cm.player.reagent
    assert cm.fuse_hand_cards(0, 1) is False
    assert cm.player.reagent == reagent_before   # Реагент не списан при отказе


def test_глитч_можно_разыграть():
    cm = _cm(Chemist(), deck=[create_strike(), create_strike(), create_defend()])
    cm.player.reagent = 5
    cm.fuse_hand_cards(0, 1)
    glitch_idx = next(
        i for i, c in enumerate(cm.deck_manager.hand) if getattr(c, "is_fused", False)
    )
    enemy_hp_before = cm.enemies[0].hp
    ok = cm.play_card_by_index(glitch_idx)
    assert ok is True
    # Глитч из двух Ударов нанёс урон
    assert cm.enemies[0].hp < enemy_hp_before
