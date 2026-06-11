# Условие: у игрока есть флаг gm.has_basilisk_egg
def _has_basilisk_egg(gm):
    return getattr(gm, "has_basilisk_egg", False)


SPECIAL_EVENTS = [
    {
        "type": "special",
        "title": "Гнездо василиска",
        "text": (
            "Вы находите огромное гнездо.\n"
            "В руках — яйцо василиска. Мать смотрит на вас.\n"
            "Она не нападает... пока."
        ),
        "condition": _has_basilisk_egg,
        "options": [
            {
                "label": "Вернуть яйцо (реликвия василиска)",
                "effects": ["remove_flag:has_basilisk_egg", "gain_relic:Автодополнение"],
            },
            {
                "label": "Забрать второе яйцо (-30 HP, +карта)",
                "effects": ["lose_hp:30", "gain_random_card"],
            },
            {
                "label": "Тихо уйти",
                "effects": ["skip"],
            },
        ],
    },
    # Сюда легко добавлять новые особые ивенты с любыми условиями
]