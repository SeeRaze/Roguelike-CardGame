import random

from core.cards.basic import (
    create_strike, create_defend,
    create_heavy_blade, create_iron_wall,
)
from core.cards.fire    import create_ignite, create_fire_breath
from core.cards.poison  import create_poison_stab, create_toxic_cloud
from core.cards.water   import create_splash, create_rain_cloud
from core.relics.starter   import LuckyClover, SpikedBracelet, ТочильныйКамень
from core.relics.elemental import ДревнееОгниво, НамокшаяРукавица

CARD_FACTORIES = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_ignite, create_fire_breath,
    create_poison_stab, create_toxic_cloud,
    create_splash, create_rain_cloud,
]

EVENTS = [
    {
        "title": "Таинственный алтарь",
        "text": (
            "Посреди тропы стоит древний алтарь.\n"
            "Камень покрыт рунами, от него исходит тепло.\n"
            "Что вы сделаете?"
        ),
        "options": [
            {"label": "Принести жертву (-15 HP, +реликвия)", "effects": ["lose_hp:15", "gain_relic:LuckyClover"]},
            {"label": "Помолиться (+20 HP)",                  "effects": ["heal:20"]},
            {"label": "Пройти мимо",                          "effects": ["skip"]},
        ],
    },
    {
        "title": "Брошенный лагерь",
        "text": (
            "Вы находите покинутый лагерь.\n"
            "Среди вещей — монеты и старая колода карт.\n"
            "Что возьмёте?"
        ),
        "options": [
            {"label": "Взять золото (+40 монет)",   "effects": ["gain_gold:40"]},
            {"label": "Взять карту (случайная)",    "effects": ["gain_random_card"]},
            {"label": "Взять и то, и то (-10 HP)",  "effects": ["gain_gold:20", "gain_random_card", "lose_hp:10"]},
        ],
    },
    {
        "title": "Торговец-призрак",
        "text": (
            "Полупрозрачный торговец предлагает сделку.\n"
            "«Твоя кровь или твоё золото — выбирай.»"
        ),
        "options": [
            {"label": "Заплатить золотом (-30, +карта)",    "effects": ["lose_gold:30", "gain_random_card"]},
            {"label": "Заплатить кровью (-20 HP, +карта)",  "effects": ["lose_hp:20", "gain_random_card"]},
            {"label": "Отказаться",                          "effects": ["skip"]},
        ],
    },
    {
        "title": "Раненый путник",
        "text": (
            "На обочине лежит раненый путник.\n"
            "Он просит о помощи. Рядом — его сумка с монетами."
        ),
        "options": [
            {"label": "Помочь (-10 HP, +50 золота)", "effects": ["lose_hp:10", "gain_gold:50"]},
            {"label": "Ограбить (+30 золота)",        "effects": ["gain_gold:30"]},
            {"label": "Пройти мимо",                  "effects": ["skip"]},
        ],
    },
    {
        "title": "Огненный дух",
        "text": (
            "Из трещины в земле вырывается огненный дух.\n"
            "Он предлагает силу в обмен на испытание."
        ),
        "options": [
            {"label": "Принять испытание (-25 HP, +реликвия)", "effects": ["lose_hp:25", "gain_relic:ДревнееОгниво"]},
            {"label": "Взять огненную карту",                   "effects": ["gain_card:create_fire_breath"]},
            {"label": "Отступить",                              "effects": ["skip"]},
        ],
    },
    {
        "title": "Подземный родник",
        "text": (
            "Вы находите чистый подземный родник.\n"
            "Вода светится голубым светом."
        ),
        "options": [
            {"label": "Выпить (+30 HP)",                        "effects": ["heal:30"]},
            {"label": "Наполнить флягу (+15 HP, +водная карта)", "effects": ["heal:15", "gain_card:create_splash"]},
            {"label": "Пройти мимо",                            "effects": ["skip"]},
        ],
    },
    {
        "title": "Старая библиотека",
        "text": (
            "Заброшенная библиотека. Полки ломятся от книг.\n"
            "Одна из них светится — внутри боевые техники."
        ),
        "options": [
            {"label": "Изучить технику (случайная карта)",       "effects": ["gain_random_card"]},
            {"label": "Продать книгу (+35 золота)",               "effects": ["gain_gold:35"]},
            {"label": "Взять обе (+карта, +20 золота, -15 HP)",   "effects": ["gain_random_card", "gain_gold:20", "lose_hp:15"]},
        ],
    },
]


def get_random_event():
    return random.choice(EVENTS)