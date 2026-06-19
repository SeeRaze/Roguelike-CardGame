# core/meta_events.py
# Шина meta-событий (С70, Этап 3 мета-прогрессии) — pub/sub для боевых фактов,
# на которые опираются ачивки и (в будущем) другие мета-системы.
#
# Архитектура минимальная: модульный словарь типов → список обработчиков.
# Публикация безопасна даже без подписчиков (no-op) — sim/baseline на каждое
# событие публикуется БЕСПЛАТНО, потому что AchievementChecker подписывается
# только из живой игры (GameManager), а sim/baseline не зовёт register_handlers().
#
# Изоляция ошибок: handler упал → шина не валит вызывающий код. Это критично
# для боя — кривая ачивка не должна крашить розыгрыш карты.
#
# Чистые примитивы + dict, никакого pygame.

from collections import defaultdict

_subscribers: dict = defaultdict(list)


def subscribe(event_type: str, handler) -> None:
    """Подписать обработчик на событие. Дубль-подписка одного и того же handler'а
    допустима (он сработает дважды) — вызывающий код отвечает за идемпотентность."""
    _subscribers[event_type].append(handler)


def unsubscribe(event_type: str, handler) -> bool:
    """Снять подписку. True если действительно сняли (handler был подписан)."""
    lst = _subscribers.get(event_type, [])
    if handler in lst:
        lst.remove(handler)
        return True
    return False


def publish(event_type: str, **payload) -> None:
    """Опубликовать событие. Перебирает КОПИЮ списка подписчиков (handler может
    отписаться сам внутри обработки — это нормально, мы итерируем по снимку).
    Исключение в одном handler'е не валит остальных и не пробрасывается наружу."""
    for handler in list(_subscribers.get(event_type, [])):
        try:
            handler(**payload)
        except Exception as exc:
            # Логирую в stderr, не падаю — шина обязана быть устойчивой
            # к багу в одном подписчике.
            print(f"[meta_events] handler '{handler}' упал на {event_type!r}: {exc}")


def clear() -> None:
    """Полностью сбросить все подписки (для тестов и форс-перезагрузки)."""
    _subscribers.clear()


def subscribers_count(event_type: str) -> int:
    """Сколько подписчиков на конкретный тип события (для тестов/диагностики)."""
    return len(_subscribers.get(event_type, []))
