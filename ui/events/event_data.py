import random

from core.cards.basic  import (
    create_strike, create_defend,
    create_heavy_blade, create_iron_wall,
)
from core.cards.fire    import create_ignite, create_fire_breath
from core.cards.poison  import create_poison_stab, create_toxic_cloud
from core.cards.water   import create_splash, create_rain_cloud

from ui.events.positive import POSITIVE_EVENTS
from ui.events.negative import NEGATIVE_EVENTS
from ui.events.neutral  import NEUTRAL_EVENTS
from ui.events.special  import SPECIAL_EVENTS

CARD_FACTORIES = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_ignite, create_fire_breath,
    create_poison_stab, create_toxic_cloud,
    create_splash, create_rain_cloud,
]

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
                # Особый ивент добавляем дважды для небольшого веса
                pool.append(event)
                pool.append(event)

    return random.choice(pool)