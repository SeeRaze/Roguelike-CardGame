# core/progression.py
# ЯРУСНАЯ ПРОГРЕССИЯ КЛАССОВ (С50) — какие классы доступны сразу, а какие
# открываются за достижения. Пирамида 3 ярусов ([[class-tier-progression]]):
#
# ДЕВ-ФЛАГ «ПОЛНЫЙ ДОСТУП» (С57, под тест-сессии): пока анлок-слой (казино/
# достижения) не достроен, залоченный контент обедняет пул → честного плейтеста не
# выйдет. dev_unlock_all() открывает ВСЁ (классы+карты+артефакты) — для тест-билда.
# Взводится двумя способами (любой): env ROGUELIKE_DEV_UNLOCK=1 (для тест-билда без
# правки сейва) ИЛИ meta['dev_unlock_all']=True (под будущий тоггл в Хабе). Дефолт
# False → прод/сим/baseline не затронуты (sim зовёт is_*_unlocked с meta=None).
#   • Ярус 1 — фундамент, доступен с первого запуска (лестница Соблюдай/Гни/Ломай).
#   • Ярус 2 — открывается за прогресс (анлок записывается в мету и хранится навсегда).
#   • Ярус 3 — Демиург-ФИНАЛ за «Идеальный аудит» (МАЯК: класс ещё не реализован,
#     условие — заглушка-всегда-False; слот живёт здесь как каркас под анлок-хук).
#
# ЧИСТЫЙ модуль: только примитивы + мета-словарь SaveManager, без pygame и игровых
# объектов → тривиально тестируется без боя. СИМУЛЯТОР/baseline сюда НЕ ходят (там
# классы инстанцируются напрямую, минуя UI-выбор), поэтому блокировка влияет ТОЛЬКО
# на селектор класса в Хабе — baseline остаётся зелёным.
#
# Условия открытия яруса 2 — ПРОСТЫЕ ЗАГЛУШКИ (числа временные): после переделки
# тройки яруса 1 классы яруса 2 пойдут в переосмысление под сеттинг проекта, поэтому
# сейчас на них не зацикливаемся — строим МЕХАНИЗМ, не контент.

# Ярус 1 — всегда доступен (фундамент, который калибруем).
TIER1 = ("Warrior", "Mage", "Berserker")

# Ярус каждого класса. Демиург (tier 3) — маяк, в селекторе пока не показывается
# (нет в CLASS_INFO/CLASS_MAP), слот нужен под будущий анлок-хук.
CLASS_TIERS = {
    "Warrior":   1,
    "Mage":      1,
    "Berserker": 1,
    "Chemist":   2,
    "Demiurge":  3,
}


def dev_unlock_all(meta: dict = None) -> bool:
    """Дев-флаг «полный доступ»: открыт ли ВЕСЬ контент (классы+карты+артефакты).

    Для тест-сессий, пока анлок-слой (казино/достижения) не достроен. Источники
    (любой истинный → True): env ROGUELIKE_DEV_UNLOCK (для тест-билда без правки
    сейва) ИЛИ meta['dev_unlock_all'] (под будущий тоггл в Хабе). Дефолт False.

    Sim/baseline зовут is_*_unlocked с meta=None и без env → флаг False → поведение
    байт-в-байт прежнее (эталон не задет)."""
    import os
    env = os.environ.get("ROGUELIKE_DEV_UNLOCK", "")
    if env and env not in ("0", "false", "False", ""):
        return True
    return bool(meta) and bool(meta.get("dev_unlock_all", False))


def _reached_floor(n):
    """Условие: лучший этаж за всю историю ≥ n (по мета-статам)."""
    return lambda meta: meta.get("stats", {}).get("best_floor", 0) >= n


def _killed_bosses(n):
    """Условие: всего побеждено боссов ≥ n."""
    return lambda meta: meta.get("stats", {}).get("total_bosses", 0) >= n


# Условие открытия → функция от меты, возвращает bool. ВРЕМЕННЫЕ заглушки (С50).
# Ярус 1 здесь не нужен (всегда открыт). Демиург — всегда False (маяк).
UNLOCK_CONDITIONS = {
    "Chemist":  _reached_floor(8),
    "Demiurge": lambda meta: False,   # «Идеальный аудит» — контент финала, позже
}


def class_tier(class_name: str) -> int:
    """Ярус класса (1/2/3). Неизвестный класс → 1 (безопасный дефолт)."""
    return CLASS_TIERS.get(class_name, 1)


def is_unlocked(meta: dict, class_name: str) -> bool:
    """Доступен ли класс для выбора в Хабе. Ярус 1 — всегда. Иначе — записан ли он
    в meta['unlocks'] (постоянный анлок, выданный за достижение)."""
    if class_name in TIER1:
        return True
    if dev_unlock_all(meta):
        return True
    if not meta:
        return False
    return class_name in meta.get("unlocks", [])


def newly_unlocked(meta: dict) -> list:
    """Проверить условия и ВЫДАТЬ новые анлоки: какие ещё-не-открытые классы теперь
    проходят своё условие. Дописывает их в meta['unlocks'] (хранится навсегда) и
    возвращает список новооткрытых имён — для всплывашки «Открыт новый класс!».
    Идемпотентна: повторный вызов без нового прогресса вернёт []."""
    unlocks = meta.setdefault("unlocks", [])
    fresh = []
    for cls, condition in UNLOCK_CONDITIONS.items():
        if cls in TIER1 or cls in unlocks:
            continue
        if condition(meta):
            unlocks.append(cls)
            fresh.append(cls)
    return fresh


# ════════════════════════════════════════════════════════════════════════════
# АНЛОК КАРТ И АРТЕФАКТОВ (С57, step 1 капстоуна) — узкий стартовый пул
# ════════════════════════════════════════════════════════════════════════════
# Философия «Узкий пул + анлоки (StS)» ([[capstone-reorder-content-first]],
# спека `_starter_pool_design.md`): часть карт/артефактов LOCKED — вливаются за
# мета-прогрессию (достижения→артефакты, казино-без-дублей→карты, джекпот-персонаж).
#
# ТРИГГЕР-АГНОСТИЧНО: этот слой ДАННЫХ лишь проверяет членство id в meta['unlocks'].
# КАК id туда попадает (грант за достижение / прокрутка казино) — ВЕРХНИЙ
# экономический слой, строится позже. Здесь — только «доступно ли сейчас».
#
# КОНВЕНЦИЯ: карта/артефакт БЕЗ записи в LOCKED_* = СТАРТОВЫЙ (всегда доступен).
# unlock_id предмета == его собственный стабильный id (анлочим конкретный предмет).
# meta['unlocks'] — общий список (классы + card_id'ы + relic_id'ы; namespace'ы не
# пересекаются: классы "Chemist", карты "legacy_patch", реликвии "ОткатКБэкапу").
#
# РАЗМЕТКА (К3, страman `_starter_pool_design.md`, согласовано юзером):
#   СТАРТОВЫЕ generic (12, НЕ заперты): базовые strike/defend/heavy_blade/iron_wall +
#     по 1 простейшей COMMON-карте новых стихий (legacy_patch/coffee_spill/voltage_spike/
#     micromanage/memory_leak/disassembler — micromanage=tox несёт дебафф-слот) + bandage
#     (сустейн) + cleaving_strike (позиц-вкус).
#   СТАРТОВЫЕ артефакты (6): Линтер(FP)/УтреннийСозвон(+урон)/ДМСБазовый(HP)/
#     Кэшбэк(золото)/ФоновоеИндексирование(удача)/ЛидЗаСпиной — разные механики
#     ВИДНЫ и ОЩУТИМЫ, но слабы; мощь (UNCOMMON+) за достижениями.
#   Сигнатурки тир-1 (Воин/Маг/Берсерк) — стартовые (НЕ в этом списке; гейтятся
#     блокировкой КЛАССА у тир-2). Стартдеки не трогаем.
# Карта/артефакт здесь = LOCKED (вливается за мета-прогрессию). Остальное — стартовое.

# card_id'ы карт, требующие анлока. С58: старые стихии убраны из пула; С59: weak/vulnerable
# (bash/neutralize/intimidate) дропнуты при консолидации в стихии (tox/coffee).
# Новые стихии — пол (6 COMMON-applier'ов) стартовый, UNCOMMON/RARE заперты.
LOCKED_CARDS: set = {
    "catalyst",
    # Песочница (С60, задача 4): UNCOMMON-награда за прогресс; открытый пол цикла
    # разработки = Коммит/Пуш в прод/Код-ревью (COMMON, в стартдеках тройки).
    "sandbox",
    # Новые стихии (С58): UNCOMMON/RARE заперты (пол = простейшие COMMON-карты семей).
    "tech_debt", "coffee_flood", "overload", "mass_short", "overtime",
    "infinite_loop", "reverse_engineer",
    "flex", "battle_cry",
    "thorn_armor", "second_wind", "elixir", "regenerate", "vitality", "triage",
    "echo_resonance", "echo_cascade", "piercing_thrust", "wide_swing",
    # Барьер: переехал из классового пула Воина (С57); мощный (несгораемый щит) → за прогресс.
    "steel_barricade", "bastion",
    # Закипание: ПАР-сетап Мага (мигрирует в C4) → за прогресс.
    "boil",
    # ENGINE-карты (С58): шорткаты-движок = награда за прогресс, не стартдек.
    "window_swap", "refresh", "coffee_break", "hard_delete", "stack_trace",
    "task_manager", "undo", "copy", "paste",
}
# relic_id'ы (имена классов), требующие анлока (27 из 33 = весь UNCOMMON+ и часть COMMON).
LOCKED_RELICS: set = {
    "Автодополнение", "РеверсПрокси", "СнекБар", "Антивирус",
    "БагРепорт", "Кофемашина",
    "Дебаггер", "ПассивнаяАгрессия", "СборщикМусора", "GitBlame",
    "Дедлайн", "Санитайзер", "ЗакрытыйТикет", "ДМСПлатиновый",
    "Оверклокинг", "ОткатКБэкапу", "ЗомбиПроцесс", "Кэш", "ЗакрытыйСпринт",
    "ПовышениеГрейда", "Стрессоустойчивость", "Автоматизация", "Аутсорс",
    "Аптайм", "ДеплойВПятницу", "ТочкаОтказа",
}


def card_id_for(factory) -> str:
    """Стабильный id карты = имя фабрики без префикса 'create_' (иммунен к
    переименованию/локализации display-имени). Пример: create_strike → 'strike'."""
    name = getattr(factory, "__name__", str(factory))
    return name[len("create_"):] if name.startswith("create_") else name


def relic_id_for(relic_cls) -> str:
    """Стабильный id артефакта = имя класса реликвии (напр. 'Линтер')."""
    return getattr(relic_cls, "__name__", str(relic_cls))


def is_card_unlocked(meta: dict, card_id: str) -> bool:
    """Доступна ли карта в выдаче забега. Стартовые (не в LOCKED_CARDS) — всегда.
    Иначе — записан ли id в meta['unlocks'] (постоянный анлок за прогресс)."""
    if card_id not in LOCKED_CARDS:
        return True
    if dev_unlock_all(meta):
        return True
    if not meta:
        return False
    return card_id in meta.get("unlocks", [])


def is_relic_unlocked(meta: dict, relic_id: str) -> bool:
    """Доступен ли артефакт в выдаче забега. Стартовые — всегда; иначе по meta."""
    if relic_id not in LOCKED_RELICS:
        return True
    if dev_unlock_all(meta):
        return True
    if not meta:
        return False
    return relic_id in meta.get("unlocks", [])
