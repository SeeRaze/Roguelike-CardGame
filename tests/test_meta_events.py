# tests/test_meta_events.py
# Этап 3 С70: pub/sub шина meta_events (core/meta_events.py).

import pytest

from core import meta_events


@pytest.fixture(autouse=True)
def clean_bus():
    """Очищаем шину до/после каждого теста — модульный словарь течёт между ними."""
    meta_events.clear()
    yield
    meta_events.clear()


def test_subscribe_then_publish_delivers():
    received = []
    meta_events.subscribe("foo", lambda x: received.append(x))
    meta_events.publish("foo", x=42)
    assert received == [42]


def test_publish_with_no_subscribers_is_noop():
    meta_events.publish("nothing_listens", payload=123)   # просто не должно упасть


def test_multiple_subscribers_all_fire_in_order():
    order = []
    meta_events.subscribe("evt", lambda **_: order.append("a"))
    meta_events.subscribe("evt", lambda **_: order.append("b"))
    meta_events.subscribe("evt", lambda **_: order.append("c"))
    meta_events.publish("evt")
    assert order == ["a", "b", "c"]


def test_handler_exception_does_not_break_bus(capsys):
    """Если один handler упал — остальные всё равно отрабатывают."""
    received = []
    def bad(**_):
        raise RuntimeError("boom")
    meta_events.subscribe("evt", bad)
    meta_events.subscribe("evt", lambda **_: received.append("ok"))
    meta_events.publish("evt", payload="x")
    assert received == ["ok"]
    # Ошибка логируется в stderr.
    err = capsys.readouterr().out
    assert "boom" in err


def test_unsubscribe_removes_handler():
    received = []
    h = lambda **_: received.append(1)
    meta_events.subscribe("evt", h)
    assert meta_events.unsubscribe("evt", h) is True
    meta_events.publish("evt")
    assert received == []


def test_unsubscribe_unknown_returns_false():
    assert meta_events.unsubscribe("nope", lambda: None) is False


def test_clear_drops_all_subscriptions():
    meta_events.subscribe("a", lambda **_: None)
    meta_events.subscribe("b", lambda **_: None)
    assert meta_events.subscribers_count("a") == 1
    meta_events.clear()
    assert meta_events.subscribers_count("a") == 0
    assert meta_events.subscribers_count("b") == 0
