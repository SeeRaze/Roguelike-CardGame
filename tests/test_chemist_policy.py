# tests/test_chemist_policy.py
# Card Fusion этап 4 (С51), сим-натив: ChemistPolicy варит карты в on_turn_begin
# (тратит Реагент на слияния → растит Нестабильность), приоритет Глитчам в выборе.

from core.players import Chemist
from core.enemies.cultist import Cultist
from core.cards import create_strike, create_coffee_spill, create_defend
from managers.balance.policy import get_policy, ChemistPolicy
from managers.CombatManager import CombatManager


def _cm(deck=None):
    d = deck if deck is not None else [
        create_strike(), create_strike(), create_coffee_spill(), create_defend(),
    ]
    return CombatManager(Chemist(), Cultist("K", 80, 80), d)


def test_реестр_отдаёт_политику_химика():
    assert isinstance(get_policy("Chemist"), ChemistPolicy)


def test_бот_варит_карты_тратя_реагент():
    cm = _cm()
    cm.player.reagent = 2
    policy = ChemistPolicy()
    inst_before = cm.player.instability
    policy.on_turn_begin(cm)
    # потратил Реагент на ≥1 фьюжн → Нестабильность выросла, Реагент убыл
    assert cm.player.instability > inst_before
    assert cm.player.reagent < 2
    assert any(getattr(c, "is_fused", False) for c in cm.deck_manager.hand)


def test_бот_не_варит_без_реагента():
    cm = _cm()
    cm.player.reagent = 0
    ChemistPolicy().on_turn_begin(cm)
    assert cm.player.instability == 0
    assert not any(getattr(c, "is_fused", False) for c in cm.deck_manager.hand)


def test_приоритет_глитчам_в_выборе():
    cm = _cm()
    cm.player.reagent = 5
    ChemistPolicy().on_turn_begin(cm)
    playable = list(cm.deck_manager.hand)
    glitches = [c for c in playable if getattr(c, "is_fused", False)]
    if glitches:   # если что-то сварилось — выбор берёт Глитч
        pick = ChemistPolicy()._class_pick(playable, cm)
        assert getattr(pick, "is_fused", False) is True


def test_пара_атак_приоритетна():
    # _pick_fusion_pair предпочитает две карты с DamageEffect.
    from core.fusion import can_fuse
    hand = [create_defend(), create_strike(), create_strike()]
    pair = ChemistPolicy._pick_fusion_pair(hand, can_fuse)
    assert pair is not None
    i, j = pair
    # обе выбранные — атаки (индексы 1 и 2), не Защита (0)
    assert {i, j} == {1, 2}
