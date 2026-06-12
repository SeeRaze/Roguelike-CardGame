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


# ─── Диспетчер задач: Эхо 1 → следующая карта ×2 (E5: унифицировано на эхо) ──
def test_task_manager_doubles_next_card():
    cm = _cm()
    e = cm.enemies[0]
    e.hp = 100
    cm.player.energy = 3
    cm.deck_manager.hand = [create_task_manager(), create_strike()]
    cm.play_card_by_index(0)        # Диспетчер → Эхо 1
    assert cm.player.echo == 1
    cm.play_card_by_index(0)        # Удар (теперь index 0) → ×2 = 12 урона
    assert e.hp == 88
    assert cm.player.echo == 0      # заряд потрачен


def test_dispatcher_does_not_double_itself():
    cm = _cm()
    cm.player.energy = 3
    cm.deck_manager.hand = [create_task_manager()]
    cm.play_card_by_index(0)
    # Диспетчер сам себя не дублирует: заряды снимаются ДО apply (E5),
    # его собственное Эхо ложится уже ПОСЛЕ — остаётся для СЛЕДУЮЩЕЙ карты.
    assert cm.player.echo == 1


def test_echo_giver_does_not_retrigger_itself():
    """Регресс-гард E5 (фикс порядка зарядов): карта, дающая Эхо N, при розыгрыше
    БЕЗ эха на игроке кладёт ровно N зарядов — не ретриггерит сама себя.
    До фикса Ретрай(Эхо 2) самоповторялся и давал 4."""
    from core.cards.echo import create_echo_resonance
    cm = _cm()
    cm.player.energy = 3
    cm.player.echo = 0
    cm.deck_manager.hand = [create_echo_resonance()]
    cm.play_card_by_index(0)
    assert cm.player.echo == 2      # ровно по описанию, не 4


# ─── Отменить: вернуть последнюю сыгранную из сброса ─────────────────────────
def test_undo_returns_last_card_to_hand():
    cm = _cm()
    last = create_strike()
    cm.deck_manager.discard_pile = [last]
    cm.deck_manager.hand = []
    create_undo().apply(cm.player, cm.enemies[0], cm)
    assert last in cm.deck_manager.hand
    assert last not in cm.deck_manager.discard_pile


def test_undo_skips_other_undo_in_discard():
    # Анти-петля: две «Отменить» не должны воскрешать друг друга (cost 0 → иначе
    # вечный ход). Undo пропускает Undo-карты в сбросе и берёт обычную под ними.
    cm = _cm()
    strike, undo_in_pile = create_strike(), create_undo()
    cm.deck_manager.discard_pile = [strike, undo_in_pile]  # верх = Undo
    cm.deck_manager.hand = []
    create_undo().apply(cm.player, cm.enemies[0], cm)
    assert strike in cm.deck_manager.hand              # вернулся Удар, не Undo
    assert undo_in_pile in cm.deck_manager.discard_pile  # Undo остался в сбросе


def test_undo_noop_when_only_undo_in_discard():
    # Если в сбросе ТОЛЬКО Отмены — возвращать нечего, рука не растёт (петля рвётся).
    cm = _cm()
    cm.deck_manager.discard_pile = [create_undo(), create_undo()]
    cm.deck_manager.hand = []
    create_undo().apply(cm.player, cm.enemies[0], cm)
    assert cm.deck_manager.hand == []


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
