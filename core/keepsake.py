# core/keepsake.py
# KEEPSAKE (С70 полировка, бонус L1 Грейда) — носимая реликвия по выбору, надеваемая
# на старт КАЖДОГО забега. Канал ачивок = «Я ВЫБРАЛ» (в отличие от рандома казино):
# keepsake = осознанный выбор стартовой грани под билд.
#
# Пул = 6 СТАРТОВЫХ артефактов (Линтер/УтреннийСозвон/ДМСБазовый/Кэшбэк/
# ФоновоеИндексирование/ЛидЗаСпиной) — по дизайну «слабые, но видные» (см.
# core/progression.py): гарантия одной из них с 1-го хода = скромный, но осязаемый
# бонус, разные keepsake направляют разные забеги ([[replayability-doctrine]]).
#
# Открывается на L1 Грейда (current_grade >= 1). Хранится в meta['keepsake'] = relic_id
# (имя класса реликвии) или None (ничего не надето).
#
# Чистый слой: equip/equipped/is_unlocked — примитивы над dict (тестируемы без боя).
# Инстанцирование реликвии (apply_to_run) — лениво, чтобы модуль не тянул весь пул
# реликвий при импорте sim/baseline.

from core import meta_currency

# Пул keepsake — relic_id (== имя класса реликвии). Подмножество стартовых артефактов.
KEEPSAKE_RELICS = (
    "Линтер",
    "УтреннийСозвон",
    "ДМСБазовый",
    "Кэшбэк",
    "ФоновоеИндексирование",
    "ЛидЗаСпиной",
)

# Ленивые кэши: relic_id -> класс, relic_id -> (display_name, description).
_BY_ID: dict | None = None
_DISPLAY: dict | None = None


def _ensure_maps() -> None:
    """Лениво построить карты id→класс и id→(имя,описание) из пула реликвий.

    Импорт core.relics отложен: модуль keepsake импортируется чистыми слоями
    (meta_currency и т.п.), а весь пул реликвий нужен только в живой игре/UI."""
    global _BY_ID, _DISPLAY
    if _BY_ID is not None:
        return
    from core.relics import ALL_RELICS
    _BY_ID = {cls.__name__: cls for cls in ALL_RELICS}
    _DISPLAY = {}
    for rid in KEEPSAKE_RELICS:
        cls = _BY_ID.get(rid)
        if cls is None:
            _DISPLAY[rid] = (rid, "")
            continue
        try:
            inst = cls()
            _DISPLAY[rid] = (inst.name, inst.description)
        except Exception:
            _DISPLAY[rid] = (rid, "")


# ─── Чистая логика (над dict) ─────────────────────────────────────────────────

def is_unlocked(meta) -> bool:
    """keepsake открывается на L1 Грейда (Первый PR). meta=None → False."""
    return meta_currency.current_grade(meta) >= 1


def equipped(meta):
    """Текущий надетый keepsake (relic_id) или None. Игнорирует мусор в поле
    (id вне пула → None) — устойчиво к старым/битым сейвам."""
    if meta is None:
        return None
    rid = meta.get("keepsake")
    return rid if rid in KEEPSAKE_RELICS else None


def equip(meta, relic_id) -> bool:
    """Надеть keepsake (relic_id) или снять (relic_id=None). Возвращает True если
    применено. Гейт: нужен L1 Грейда. relic_id вне пула → False (мета не изменена)."""
    if meta is None or not is_unlocked(meta):
        return False
    if relic_id is None:
        meta["keepsake"] = None
        return True
    if relic_id not in KEEPSAKE_RELICS:
        return False
    meta["keepsake"] = relic_id
    return True


# ─── UI-хелперы (дисплей) ─────────────────────────────────────────────────────

def display_name(relic_id) -> str:
    """Внутриигровое имя реликвии (для чипа keepsake). Фолбэк — relic_id."""
    _ensure_maps()
    return _DISPLAY.get(relic_id, (relic_id, ""))[0]


def description(relic_id) -> str:
    """Описание эффекта реликвии (для подсказки под чипом). Фолбэк — пусто."""
    _ensure_maps()
    return _DISPLAY.get(relic_id, (relic_id, ""))[1]


# ─── Применение к забегу ──────────────────────────────────────────────────────

def apply_to_run(gm) -> str | None:
    """Надеть keepsake на старте забега: добавить инстанс реликвии в gm.relics.

    Возвращает relic_id добавленной реликвии или None (нет keepsake / заперт /
    дубль). Дубль-гард по КЛАССУ: если реликвия того же типа уже в инвентаре
    (надрафтили в прошлом забеге / повтор старта) — не добавляем второй раз.
    Зовётся из HubView на старте забега (живая игра); sim/baseline не зовут."""
    meta = getattr(gm, "meta", None)
    rid = equipped(meta)
    if rid is None or not is_unlocked(meta):
        return None
    _ensure_maps()
    cls = _BY_ID.get(rid)
    if cls is None:
        return None
    if any(type(r) is cls for r in gm.relics):
        return None
    gm.relics.append(cls())
    return rid
