POSITIVE_EVENTS = [
    {
        "type": "positive",
        "title": "Подземный родник",
        "text": (
            "Вы находите чистый подземный родник.\n"
            "Вода светится голубым светом."
        ),
        "options": [
            {"label": "Выпить (+30 HP)",                         "effects": ["heal:30"]},
            {"label": "Наполнить флягу (+15 HP, +водная карта)", "effects": ["heal:15", "gain_card:create_splash"]},
            {"label": "Пройти мимо",                             "effects": ["skip"]},
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
            {"label": "Взять золото (+40 монет)",  "effects": ["gain_gold:40"]},
            {"label": "Взять карту (случайная)",   "effects": ["gain_random_card"]},
            {"label": "Взять всё (-10 HP)",         "effects": ["gain_gold:20", "gain_random_card", "lose_hp:10"]},
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
            {"label": "Изучить технику (случайная карта)",      "effects": ["gain_random_card"]},
            {"label": "Продать книгу (+35 золота)",              "effects": ["gain_gold:35"]},
            {"label": "Взять обе (+карта, +20 золота, -15 HP)",  "effects": ["gain_random_card", "gain_gold:20", "lose_hp:15"]},
        ],
    },
]