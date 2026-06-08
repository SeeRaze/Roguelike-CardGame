POSITIVE_EVENTS = [
    {
        "type": "positive",
        "title": "Подземный родник",
        "text": (
            "Вы находите чистый подземный родник.\n"
            "Вода светится голубым светом."
        ),
        "options": [
            {"label": "Выпить (+30% HP)",                         "effects": ["heal_pct:0.30"]},
            {"label": "Наполнить флягу (+15% HP, +водная карта)", "effects": ["heal_pct:0.15", "gain_card:create_splash"]},
            {"label": "Пройти мимо",                              "effects": ["skip"]},
        ],
    },
    {
        "type": "positive",
        "title": "Брошенный лагерь",
        "text": (
            "Вы находите покинутый лагерь.\n"
            "Среди вещей — монеты и старая колода карт."
        ),
        "options": [
            {"label": "Взять золото (+монеты)",          "effects": ["gain_gold_floor:4"]},
            {"label": "Взять карту (случайная)",          "effects": ["gain_random_card"]},
            {"label": "Взять всё (+монеты, +карта, -10% HP)", "effects": ["gain_gold_floor:2", "gain_random_card", "lose_hp_pct:0.10"]},
        ],
    },
    {
        "type": "positive",
        "title": "Старая библиотека",
        "text": (
            "Заброшенная библиотека. Полки ломятся от книг.\n"
            "Одна из них светится — внутри боевые техники."
        ),
        "options": [
            {"label": "Изучить технику (случайная карта)",       "effects": ["gain_random_card"]},
            {"label": "Продать книгу (+монеты)",                  "effects": ["gain_gold_floor:4"]},
            {"label": "Взять обе (+карта, +монеты, -15% HP)",     "effects": ["gain_random_card", "gain_gold_floor:2", "lose_hp_pct:0.15"]},
        ],
    },
]
