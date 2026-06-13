NEUTRAL_EVENTS = [
    {
        "type": "neutral",
        "title": "Серверная",
        "text": (
            "Гудит серверная. На стойке мигает прод —\n"
            "он держится на честном слове и старом UPS."
        ),
        "options": [
            {"label": "Задеплоить в прод (-15% HP, +реликвия)",    "effects": ["lose_hp_pct:0.15", "gain_relic:Автодополнение"]},
            {"label": "Захардить сервер (-10% HP, +12% макс. HP)", "effects": ["lose_hp_pct:0.10", "temper_spirit:0.12"]},
            {"label": "Перезагрузить (+20% HP)",                   "effects": ["heal_pct:0.20"]},
            {"label": "Пройти мимо",                               "effects": ["skip"]},
        ],
    },
    {
        "type": "neutral",
        "title": "Призрачный фрилансер",
        "text": (
            "Призрачный фрилансер пишет в чат:\n"
            "«Деньги или твои выходные — выбирай.»"
        ),
        "options": [
            {"label": "Заплатить деньгами (-30% монет, +карта)",  "effects": ["lose_gold_pct:0.30", "gain_random_card"]},
            {"label": "Заплатить переработкой (-20% HP, +карта)", "effects": ["lose_hp_pct:0.20", "gain_random_card"]},
            {"label": "Отказаться",                               "effects": ["skip"]},
        ],
    },
    {
        "type": "neutral",
        "title": "Стресс-тест",
        "text": (
            "Система под пиковой нагрузкой.\n"
            "Выдержишь стресс-тест — получишь закалённый инструмент."
        ),
        "options": [
            {"label": "Пройти стресс-тест (-25% HP, +реликвия)", "effects": ["lose_hp_pct:0.25", "gain_relic:Дебаггер"]},
            {"label": "Срезать костылём (+Legacy-карта)",        "effects": ["gain_card:create_tech_debt"]},
            {"label": "Отступить",                               "effects": ["skip"]},
        ],
    },
    {
        "type": "neutral",
        "title": "Застрявший джун",
        "text": (
            "Джун третий час бьётся над одним багом.\n"
            "Глаза красные, в чате — мольба о помощи."
        ),
        "options": [
            {"label": "Помочь разобраться (-10% HP, +монеты)", "effects": ["lose_hp_pct:0.10", "gain_gold_floor:5"]},
            {"label": "Присвоить его фикс (+монеты)",           "effects": ["gain_gold_floor:3"]},
            {"label": "Пройти мимо",                            "effects": ["skip"]},
        ],
    },
]
