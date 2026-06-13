POSITIVE_EVENTS = [
    {
        "type": "positive",
        "title": "Кофемашина",
        "text": (
            "Кофемашина на этаже ещё работает.\n"
            "Пахнет свежесваренным эспрессо."
        ),
        "options": [
            {"label": "Выпить чашку (+30% HP)",                       "effects": ["heal_pct:0.30"]},
            {"label": "Налить с собой (+15% HP, +Разлитый кофе)",     "effects": ["heal_pct:0.15", "gain_card:create_coffee_spill"]},
            {"label": "Пройти мимо",                                  "effects": ["skip"]},
        ],
    },
    {
        "type": "positive",
        "title": "Заброшенный репозиторий",
        "text": (
            "Старый репозиторий без мейнтейнера.\n"
            "В истории коммитов — забытый грант и рабочие модули."
        ),
        "options": [
            {"label": "Забрать грант (+монеты)",                      "effects": ["gain_gold_floor:4"]},
            {"label": "Форкнуть модуль (случайная карта)",            "effects": ["gain_random_card"]},
            {"label": "Склонировать всё (+монеты, +карта, -10% HP)",  "effects": ["gain_gold_floor:2", "gain_random_card", "lose_hp_pct:0.10"]},
        ],
    },
    {
        "type": "positive",
        "title": "Stack Overflow",
        "text": (
            "Тред с твоей ошибкой один в один.\n"
            "Один ответ помечен зелёной галочкой."
        ),
        "options": [
            {"label": "Скопировать решение (случайная карта)",            "effects": ["gain_random_card"]},
            {"label": "Закрыть баунти (+монеты)",                         "effects": ["gain_gold_floor:4"]},
            {"label": "Скопировать весь тред (+карта, +монеты, -15% HP)",  "effects": ["gain_random_card", "gain_gold_floor:2", "lose_hp_pct:0.15"]},
        ],
    },
]
