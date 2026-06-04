import random

from ui.events.positive import POSITIVE_EVENTS
from ui.events.negative import NEGATIVE_EVENTS
from ui.events.neutral  import NEUTRAL_EVENTS
from ui.events.special  import SPECIAL_EVENTS

# Базовый пул (без особых)
_BASE_POOL = POSITIVE_EVENTS + NEGATIVE_EVENTS + NEUTRAL_EVENTS


def get_random_event(gm=None):
    """
    Возвращает случайный ивент.
    Если передан gm — особые ивенты с выполненным условием
    добавляются в пул с повышенным весом.
    """
    pool = list(_BASE_POOL)

    if gm is not None:
        for event in SPECIAL_EVENTS:
            condition = event.get("condition")
            if condition is None or condition(gm):
                pool.append(event)
                pool.append(event)

    return random.choice(pool)