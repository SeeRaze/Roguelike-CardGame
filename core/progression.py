# core/progression.py
# ЯРУСНАЯ ПРОГРЕССИЯ КЛАССОВ (С50) — какие классы доступны сразу, а какие
# открываются за достижения. Пирамида 3 ярусов ([[class-tier-progression]]):
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
    "Rogue":     2,
    "Druid":     2,
    "Summoner":  2,
    "Chemist":   2,
    "Demiurge":  3,
}


def _reached_floor(n):
    """Условие: лучший этаж за всю историю ≥ n (по мета-статам)."""
    return lambda meta: meta.get("stats", {}).get("best_floor", 0) >= n


def _killed_bosses(n):
    """Условие: всего побеждено боссов ≥ n."""
    return lambda meta: meta.get("stats", {}).get("total_bosses", 0) >= n


# Условие открытия → функция от меты, возвращает bool. ВРЕМЕННЫЕ заглушки (С50).
# Ярус 1 здесь не нужен (всегда открыт). Демиург — всегда False (маяк).
UNLOCK_CONDITIONS = {
    "Rogue":    _reached_floor(5),
    "Druid":    _killed_bosses(1),
    "Summoner": _reached_floor(6),
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
