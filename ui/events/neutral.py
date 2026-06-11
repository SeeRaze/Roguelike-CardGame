NEUTRAL_EVENTS = [
    {
        "type": "neutral",
        "title": "Таинственный алтарь",
        "text": (
            "Посреди тропы стоит древний алтарь.\n"
            "Камень покрыт рунами, от него исходит тепло."
        ),
        "options": [
            {"label": "Принести жертву (-15% HP, +реликвия)",   "effects": ["lose_hp_pct:0.15", "gain_relic:Автодополнение"]},
            {"label": "Закалить дух (-10% HP, +12% макс. HP)",  "effects": ["lose_hp_pct:0.10", "temper_spirit:0.12"]},
            {"label": "Помолиться (+20% HP)",                    "effects": ["heal_pct:0.20"]},
            {"label": "Пройти мимо",                             "effects": ["skip"]},
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
            {"label": "Заплатить золотом (-30% монет, +карта)", "effects": ["lose_gold_pct:0.30", "gain_random_card"]},
            {"label": "Заплатить кровью (-20% HP, +карта)",     "effects": ["lose_hp_pct:0.20", "gain_random_card"]},
            {"label": "Отказаться",                              "effects": ["skip"]},
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
            {"label": "Принять испытание (-25% HP, +реликвия)", "effects": ["lose_hp_pct:0.25", "gain_relic:ДревнееОгниво"]},
            {"label": "Взять Legacy-карту",                      "effects": ["gain_card:create_tech_debt"]},
            {"label": "Отступить",                               "effects": ["skip"]},
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
            {"label": "Помочь (-10% HP, +монеты)", "effects": ["lose_hp_pct:0.10", "gain_gold_floor:5"]},
            {"label": "Ограбить (+монеты)",         "effects": ["gain_gold_floor:3"]},
            {"label": "Пройти мимо",                "effects": ["skip"]},
        ],
    },
]
