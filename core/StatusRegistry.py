STATUSES = {
    "vulnerable": {
        "abbr":        "УЯЗВ",
        "badge_bg":    (160, 60, 180),
        "badge_fg":    (255, 255, 255),
        "tooltip":     "Уязвимость: получаемый урон ×1.5.\nОсталось ходов: N",
        "keyword":     ("Уязвимость", "Цель получает урон ×1.5.\nДлится N ход(а)."),
        "is_duration": True,
        "is_stack":    False,
    },
    "weak": {
        "abbr":        "СЛАБ",
        "badge_bg":    (100, 100, 180),
        "badge_fg":    (255, 255, 255),
        "tooltip":     "Слабость: наносимый урон ×0.75.\nОсталось ходов: N",
        "keyword":     ("Слабость", "Цель наносит урон ×0.75.\nДлится N ход(а)."),
        "is_duration": True,
        "is_stack":    False,
    },
    "wet": {
        "abbr":        "МОК",
        "badge_bg":    (50, 120, 200),
        "badge_fg":    (255, 255, 255),
        "tooltip":     "Мокрый: огонь наносит двойной урон.\nОсталось ходов: N",
        "keyword":     ("Мокрый", "Огонь наносит двойной урон.\nДлится N ход(а)."),
        "is_duration": True,
        "is_stack":    False,
    },
    "ignited": {
        "abbr":        "ОГОНЬ",
        "badge_bg":    (210, 80, 20),
        "badge_fg":    (255, 255, 200),
        "tooltip":     "Горение: N урона в конце каждого хода.",
        "keyword":     ("Горение", "N урона в конце каждого хода."),
        "is_duration": True,
        "is_stack":    True,
    },
    "poison": {
        "abbr":        "ЯД",
        "badge_bg":    (60, 160, 60),
        "badge_fg":    (255, 255, 255),
        "tooltip":     "Яд: N урона сквозь щит, затем убывает на 1.",
        "keyword":     ("Яд", "N урона сквозь щит в конце хода.\nЗатем убывает на 1."),
        "is_duration": False,
        "is_stack":    True,
    },
    "strength": {
        "abbr":        "ЯРОСТЬ",
        "badge_bg":    (180, 40, 40),
        "badge_fg":    (255, 220, 180),
        "tooltip":     "Ярость: +N к урону всех атак.",
        "keyword":     ("Ярость", "+N к урону всех атак."),
        "is_duration": False,
        "is_stack":    True,
    },
    "thorns": {
        "abbr":        "ШИПЫ",
        "badge_bg":    (80, 140, 60),
        "badge_fg":    (255, 255, 255),
        "tooltip":     "Шипы: отражает N урона атакующему.",
        "keyword":     ("Шипы", "Отражает N урона атакующему."),
        "is_duration": False,
        "is_stack":    True,
    },
    "regen": {
        "abbr":        "РЕГЕН",
        "badge_bg":    (50, 180, 100),
        "badge_fg":    (255, 255, 255),
        "tooltip":     "Регенерация: восстанавливает N HP в конце хода, затем убывает на 1.",
        "keyword":     ("Регенерация", "Восстанавливает N HP в конце хода.\nЗатем убывает на 1."),
        "is_duration": False,
        "is_stack":    True,
        
    },
        "bleed": {
        "abbr":        "КРОВЬ",
        "badge_bg":    (160, 20, 40),
        "badge_fg":    (255, 200, 200),
        "tooltip":     "Кровотечение: каждый удар наносит +N доп. урона сквозь щит. Убывает на 1 в конце хода.",
        "keyword":     ("Кровотечение", "Каждый удар наносит +N доп. урона сквозь щит.\nУбывает на 1 в конце хода."),
        "is_duration": False,
        "is_stack":    True,
    },
}


def get(key: str) -> dict:
    """Возвращает данные статуса по ключу. KeyError если не найден."""
    return STATUSES[key]


def all_keys() -> list:
    """Список всех ключей статусов."""
    return list(STATUSES.keys())