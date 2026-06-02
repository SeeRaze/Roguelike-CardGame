NEUTRAL_EVENTS = [
    {
        "type": "neutral",
        "title": "Таинственный алтарь",
        "text": (
            "Посреди тропы стоит древний алтарь.\n"
            "Камень покрыт рунами, от него исходит тепло."
        ),
        "options": [
            {"label": "Принести жертву (-15 HP, +реликвия)", "effects": ["lose_hp:15", "gain_relic:LuckyClover"]},
            {"label": "Помолиться (+20 HP)",                  "effects": ["heal:20"]},
            {"label": "Пройти мимо",                          "effects": ["skip"]},
        ],
    },
    {
        "type": "neutral",
        "title": "Торговец-призрак",
        "text": (
            "Полупрозрачный торговец предлагает сделку.\n"
            "«Твоя кровь или твоё золото — выбирай.»"
        ),
        "options": [
            {"label": "Заплатить золотом (-30, +карта)",   "effects": ["lose_gold:30", "gain_random_card"]},
            {"label": "Заплатить кровью (-20 HP, +карта)", "effects": ["lose_hp:20", "gain_random_card"]},
            {"label": "Отказаться",                         "effects": ["skip"]},
        ],
    },
    {
        "type": "neutral",
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
        "type": "neutral",
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
]