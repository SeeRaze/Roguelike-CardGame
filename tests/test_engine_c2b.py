# tests/test_engine_c2b.py
# ENGINE C2b — множители: Диспетчер (×2), Отменить (undo), Копировать/Вставить (Буфер).
from core.players.warrior import Warrior
from core.enemies import Cultist
from core.cards.basic import create_strike
from core.cards.shortcuts import (
    create_task_manager, create_undo, create_copy, create_paste,
)
from managers.CombatManager import CombatManager


def _cm():
    return CombatManager(Warrior(), Cultist("K", 100, 100), [create_strike()])


# ─── Диспетчер задач: следующая карта ×2 ─────────────────────────────────────
def test_task_manager_doubles_next_card():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 100
    cm.player.energy = 3
    cm.deck_manager.hand = [create_task_manager(), create_strike()]
    cm.play_card_by_index(0)        # Диспетчер → флаг
    assert cm._dispatcher_pending is True
    cm.play_card_by_index(0)        # Удар (теперь index 0) → ×2 = 12 урона
    assert e.hp == 88
    assert cm._dispatcher_pending is False   # флаг потрачен


def test_dispatcher_does_not_double_itself():
    cm = _cm()
    cm.player.energy = 3
    cm.deck_manager.hand = [create_task_manager()]
    cm.play_card_by_index(0)
    # Диспетчер сам себя не дублирует — флаг остался для СЛЕДУЮЩЕЙ карты.
    assert cm._dispatcher_pending is True


# ─── Отменить: вернуть последнюю сыгранную из сброса ─────────────────────────
def test_undo_returns_last_card_to_hand():
    cm = _cm()
    last = create_strike()
    cm.deck_manager.discard_pile = [last]
    cm.deck_manager.hand = []
    create_undo().apply(cm.player, cm.enemies[0], cm)
    assert last in cm.deck_manager.hand
    assert last not in cm.deck_manager.discard_pile


# ─── Копировать/Вставить: Буфер обмена ───────────────────────────────────────
def test_copy_then_paste_refires_effect():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 50
    cm.deck_manager.discard_pile = [create_strike()]   # последняя сыгранная
    create_copy().apply(cm.player, e, cm)
    assert cm._clipboard is not None
    create_paste().apply(cm.player, e, cm)             # перефайр Удара (6)
    assert e.hp == 44
    assert cm._clipboard is not None                   # Буфер НЕ очищается


def test_paste_empty_buffer_noop():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 50
    create_paste().apply(cm.player, e, cm)
    assert e.hp == 50                                  # пустой Буфер — без эффекта
