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
    # ── Блок 4 (С65): risk/reward вокруг FP-оси и техдолга (Баг = цена) ──
    {
        "type": "neutral",
        "title": "Технический долг",
        "text": (
            "Дедлайн горит. Можно срезать углы сейчас —\n"
            "но долг придётся отдавать с процентами."
        ),
        "options": [
            {"label": "Взять кредит под фичу (+7 FP, +1 Баг)", "effects": ["gain_forge:7", "accrue_bug:1"]},
            {"label": "Сделать по уму (+2 FP)",                "effects": ["gain_forge:2"]},
            {"label": "Отложить задачу",                       "effects": ["skip"]},
        ],
    },
    {
        "type": "neutral",
        "title": "Прод-инцидент в 3 ночи",
        "text": (
            "Телефон разрывается: упал прод.\n"
            "Кто починит — тот герой (или крайний)."
        ),
        "options": [
            {"label": "Поднять лично (-20% HP, +реликвия)", "effects": ["lose_hp_pct:0.20", "gain_random_relic"]},
            {"label": "Разбудить джуна (-20% монет)",       "effects": ["lose_gold_pct:0.20"]},
            {"label": "Притвориться спящим",                "effects": ["skip"]},
        ],
    },
    {
        "type": "neutral",
        "title": "Code review от синьора",
        "text": (
            "Синьор оставил 47 комментариев к твоему PR.\n"
            "Правки бьют по самолюбию — но учат."
        ),
        "options": [
            {"label": "Переписать как просят (-15% HP, +карта)", "effects": ["lose_hp_pct:0.15", "gain_random_card"]},
            {"label": "Протащить костылём (+4 FP, +1 Баг)",      "effects": ["gain_forge:4", "accrue_bug:1"]},
            {"label": "Закрыть PR без мерджа",                   "effects": ["skip"]},
        ],
    },
]
