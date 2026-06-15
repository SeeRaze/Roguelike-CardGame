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
    # ── Блок 4 (С65): добор событий под новый контент (FP-ось / новые реликвии) ──
    {
        "type": "positive",
        "title": "Рефакторинг-спринт",
        "text": (
            "Выдалась неделя без задач — можно разгрести\n"
            "техдолг и привести код в порядок."
        ),
        "options": [
            {"label": "Спокойный рефакторинг (+3 CR)",         "effects": ["gain_forge:3"]},
            {"label": "Жёсткий рефакторинг (+6 CR, -15% HP)",  "effects": ["gain_forge:6", "lose_hp_pct:0.15"]},
            {"label": "Не трогать рабочее",                    "effects": ["skip"]},
        ],
    },
    {
        "type": "positive",
        "title": "Хакатон",
        "text": (
            "Внутренний хакатон на выходных.\n"
            "За лучший прототип — приз от компании."
        ),
        "options": [
            {"label": "Запилить киллер-фичу (+реликвия)",   "effects": ["gain_random_relic"]},
            {"label": "Наклепать прототипов (+2 карты)",    "effects": ["gain_random_card", "gain_random_card"]},
            {"label": "Прийти за пиццей (+монеты)",         "effects": ["gain_gold_floor:4"]},
        ],
    },
]
