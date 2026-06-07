# managers/SaveManager.py
# Локальная персистентность МЕТА-ПРОГРЕССИИ (Сессия 40): итоги забегов + история,
# питающие local-first лидерборд и «игра помнит тебя» в HUB. Сейв — единственный
# слой записи на диск (леаэрборд раньше был только облачным и не показывал результат).
#
# Принципы: только ПРИМИТИВЫ (числа/строки/списки) — никакой сериализации живых
# объектов; PyInstaller-safe путь (пишем в пользовательский каталог, НЕ рядом с
# frozen exe); атомарная запись (temp + os.replace); UTF-8 (кириллица); corruption-
# safe чтение (битый/чужой файл → дефолт, игра не падает). Чистый _apply_run
# тестируется без диска. Сейв НЕ критичен для геймплея — сбой записи проглатывается.

import json
import os
import sys
from pathlib import Path

SAVE_VERSION    = 1
RUNS_CAP        = 50     # кольцо истории забегов (последние N)
LEADERBOARD_CAP = 10     # сколько строк отдаём доске

_APP_DIR_NAME  = "Roguelike-CardGame"
_SAVE_FILENAME = "meta_save.json"

_meta = None             # модульный кэш (грузится лениво, обновляется в памяти)


def get_save_path() -> Path:
    """Путь к сейв-файлу в ПИСАБЕЛЬНОМ пользовательском каталоге (PyInstaller-safe:
    НЕ рядом с frozen exe). Windows → %APPDATA%; иначе → ~/.local/share. Каталог
    создаётся при необходимости."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
    else:
        base = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    save_dir = Path(base) / _APP_DIR_NAME
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir / _SAVE_FILENAME


def _default_meta() -> dict:
    return {
        "version": SAVE_VERSION,
        "stats": {
            "total_runs":      0,
            "best_floor":      0,
            "total_kills":     0,
            "total_bosses":    0,
            "max_damage_ever": 0,
        },
        "class_best": {},    # class -> {best_floor, kills, max_damage, runs}
        "runs":       [],    # [{username, class, max_floor, kills, max_damage}]
        "unlocks":    [],    # имена открытых классов яруса 2+ (С50, ярус 1 всегда открыт)
    }


def _load_from_disk() -> dict:
    """Прочитать сейв или вернуть дефолт. Любой сбой (нет файла / битый JSON /
    чужая версия) → чистый дефолт, без падения."""
    try:
        path = get_save_path()
        if not path.exists():
            return _default_meta()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get("version") != SAVE_VERSION:
            return _default_meta()
        # Гарантируем наличие всех ключей (на случай частичного файла).
        merged = _default_meta()
        for key in merged:
            if key in data:
                merged[key] = data[key]
        merged.setdefault("stats", _default_meta()["stats"])
        for sk, sv in _default_meta()["stats"].items():
            merged["stats"].setdefault(sk, sv)
        return merged
    except (OSError, ValueError):
        return _default_meta()


def get_meta() -> dict:
    """Мета-словарь (ленивая загрузка с диска при первом обращении)."""
    global _meta
    if _meta is None:
        _meta = _load_from_disk()
    return _meta


def save() -> None:
    """Атомарно записать кэш на диск. Сбой записи проглатывается (сейв не критичен)."""
    if _meta is None:
        return
    path = get_save_path()
    tmp  = path.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_meta, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)            # атомарная замена
    except OSError:
        pass


def _apply_run(meta: dict, run: dict) -> dict:
    """ЧИСТОЕ обновление meta завершённым забегом (тестируемо без диска).
    run: {username, class, max_floor, kills, bosses, max_damage}."""
    floor  = int(run.get("max_floor", 0))
    kills  = int(run.get("kills", 0))
    bosses = int(run.get("bosses", 0))
    dmg    = int(run.get("max_damage", 0))
    cls    = run.get("class", "Unknown")

    s = meta["stats"]
    s["total_runs"]     += 1
    s["best_floor"]      = max(s["best_floor"], floor)
    s["total_kills"]    += kills
    s["total_bosses"]   += bosses
    s["max_damage_ever"] = max(s["max_damage_ever"], dmg)

    cb = meta["class_best"].setdefault(
        cls, {"best_floor": 0, "kills": 0, "max_damage": 0, "runs": 0})
    cb["best_floor"]  = max(cb["best_floor"], floor)
    cb["kills"]       = max(cb["kills"], kills)
    cb["max_damage"]  = max(cb["max_damage"], dmg)
    cb["runs"]       += 1

    meta["runs"].append({
        "username":   run.get("username", "?"),
        "class":      cls,
        "max_floor":  floor,
        "kills":      kills,
        "max_damage": dmg,
    })
    if len(meta["runs"]) > RUNS_CAP:
        meta["runs"] = meta["runs"][-RUNS_CAP:]
    return meta


def record_run(run: dict) -> list:
    """Записать завершённый забег: обновить кэш в памяти + сохранить на диск.
    Возвращает список НОВООТКРЫТЫХ классов (С50) — забег мог выполнить условие
    анлока яруса 2; вызыватель может показать всплывашку «Открыт новый класс!».
    Список пуст, если ничего не открылось (обычный случай)."""
    from core import progression
    meta = get_meta()
    _apply_run(meta, run)
    fresh = progression.newly_unlocked(meta)   # грант анлоков по итогам забега
    save()
    return fresh


def leaderboard_rows(meta: dict, network_rows=None) -> list:
    """Строки для доски трофеев: ЛОКАЛЬНЫЕ забеги + мерж сетевых, дедуп, сорт по
    этажу↓ (затем убийства↓, урон↓), кап LEADERBOARD_CAP. Local-first: локальные
    забеги показываются всегда (офлайн-устойчиво), сеть — обогащение."""
    rows = []
    for r in meta.get("runs", []):
        rows.append({
            "username":   str(r.get("username", "?")),
            "class":      str(r.get("class", "—")),
            "max_floor":  int(r.get("max_floor", 0)),
            "kills":      int(r.get("kills", 0)),
            "max_damage": int(r.get("max_damage", 0)),
        })
    for r in (network_rows or []):
        if not isinstance(r, dict):
            continue
        rows.append({
            "username":   str(r.get("username", "?")),
            "class":      str(r.get("class", "—")),
            "max_floor":  int(r.get("max_floor", 0)),
            "kills":      int(r.get("kills", 0)),
            "max_damage": int(r.get("max_damage", 0)),
        })
    seen, deduped = set(), []
    for r in rows:
        key = (r["username"], r["class"], r["max_floor"], r["kills"], r["max_damage"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    deduped.sort(
        key=lambda r: (r["max_floor"], r["kills"], r["max_damage"]), reverse=True)
    return deduped[:LEADERBOARD_CAP]


def reset_cache() -> None:
    """Сбросить модульный кэш (для тестов / форс-перезагрузки)."""
    global _meta
    _meta = None
