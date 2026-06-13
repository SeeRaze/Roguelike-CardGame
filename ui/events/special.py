# Условие: у игрока есть флаг gm.has_basilisk_egg (внутр. идентификатор сохранён;
# флейвор — «утёкший прод-токен». Сеттер флага пока нигде нет → событие дремлет.)
def _has_basilisk_egg(gm):
    return getattr(gm, "has_basilisk_egg", False)


SPECIAL_EVENTS = [
    {
        "type": "special",
        "title": "Утечка ключей",
        "text": (
            "Ты находишь, откуда утекли ключи.\n"
            "В руках — рабочий прод-токен. Сервис ещё живёт.\n"
            "Никто пока не заметил."
        ),
        "condition": _has_basilisk_egg,
        "options": [
            {
                "label": "Отозвать ключ (реликвия)",
                "effects": ["remove_flag:has_basilisk_egg", "gain_relic:Автодополнение"],
            },
            {
                "label": "Слить второй токен (-30 HP, +карта)",
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
