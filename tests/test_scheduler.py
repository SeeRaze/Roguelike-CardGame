# tests/test_scheduler.py
# Чистый примитив очереди отложенных эффектов (§3): DelayedEffect / DelayedQueue.
# Пьюр-тайминг — без боя: schedule кладёт, tick уменьшает таймеры и отдаёт созревшие.

from core.scheduler import DelayedEffect, DelayedQueue


def _noop(cm):
    """Заглушка-действие: очередь хранит тайминг, исполнение — на вызывателе."""
    return None


# ── DelayedEffect: нормализация taймера ──────────────────────────────────────────

def test_delayed_effect_пол_1():
    """«через 0/отриц. ходов» нормализуется в 1 = «в конце этого хода»."""
    assert DelayedEffect(0, _noop).turns == 1
    assert DelayedEffect(-5, _noop).turns == 1
    assert DelayedEffect(3, _noop).turns == 3


def test_delayed_effect_turns_приводится_к_int():
    assert DelayedEffect(2.9, _noop).turns == 2


# ── DelayedQueue: пустая инертна ─────────────────────────────────────────────────

def test_пустая_очередь_инертна():
    """Без потребителя tick всегда отдаёт [] (baseline зелёный)."""
    q = DelayedQueue()
    assert len(q) == 0
    assert q.tick() == []
    assert q.tick() == []          # повторно — по-прежнему пусто


# ── созревание ───────────────────────────────────────────────────────────────────

def test_созревание_через_один_ход():
    q = DelayedQueue()
    q.schedule(1, _noop, label="через ход")
    assert len(q) == 1
    due = q.tick()
    assert len(due) == 1
    assert due[0].label == "через ход"
    assert len(q) == 0             # созревший убран из очереди


def test_созревание_через_несколько_ходов():
    q = DelayedQueue()
    q.schedule(3, _noop)
    assert q.tick() == []          # 3 -> 2
    assert q.tick() == []          # 2 -> 1
    due = q.tick()                 # 1 -> 0, созрел
    assert len(due) == 1
    assert len(q) == 0


def test_несколько_эффектов_созревают_вместе():
    q = DelayedQueue()
    q.schedule(1, _noop, label="A")
    q.schedule(1, _noop, label="B")
    q.schedule(2, _noop, label="C")
    due = q.tick()
    assert [d.label for d in due] == ["A", "B"]   # порядок планирования сохранён
    assert len(q) == 1                            # C ещё ждёт
    assert q.tick()[0].label == "C"


# ── исполнение, планирующее новое отложенное, ничего не теряет ────────────────────

def test_новое_отложенное_во_время_исполнения_не_теряется():
    """tick переустанавливает очередь ДО возврата → действие, запланировавшее новое
    отложенное при своём исполнении, кладёт его в живую очередь, а не в выброшенный
    список. Эмулируем «вызыватель исполняет созревшее, оно планирует следующее»."""
    q = DelayedQueue()
    q.schedule(1, _noop, label="первое")
    due = q.tick()                 # очередь уже пуста на этот момент
    assert len(q) == 0
    # вызыватель исполняет созревшее и планирует продолжение
    for _ in due:
        q.schedule(1, _noop, label="второе")
    assert len(q) == 1             # новое легло в живую очередь
    assert q.tick()[0].label == "второе"


# ── инспекция: pending — копия, не мутирует очередь ──────────────────────────────

def test_pending_копия_не_мутирует_очередь():
    q = DelayedQueue()
    q.schedule(2, _noop, label="X")
    snapshot = q.pending
    assert [e.label for e in snapshot] == ["X"]
    snapshot.clear()               # мутация копии
    assert len(q) == 1             # очередь цела
