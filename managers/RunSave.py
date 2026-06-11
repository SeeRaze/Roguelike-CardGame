# managers/RunSave.py
# Сохранение/возобновление АКТИВНОГО ЗАБЕГА (С57). В отличие от SaveManager (мета-
# прогрессия между забегами) — это снимок ТЕКУЩЕГО прохождения, чтобы выйти в меню и
# продолжить позже. Точка сейва — ТОЛЬКО КАРТА (state=MAP): чистое состояние без
# активного боя/магазина/события (решение юзера — снапшот MAP).
#
# Принципы (как SaveManager): только примитивы в JSON; PyInstaller-safe путь; атомарная
# запись; corruption/version-safe чтение (битый/чужой/несовместимый файл → нет сейва,
# игра не падает). Карты воссоздаются по card_id (RAW_FACTORIES) + накат линейной ковки;
# реликвии — по имени класса (ALL_RELICS). Сейв НЕ критичен — сбой записи проглатывается.
#
# ОГРАНИЧЕНИЯ MVP (задокументировано): активные Ставки сохраняются как id'ы, но их
# RuleStack-моды (напр. урон ×1.25 Хрупкости) при загрузке НЕ переактивируются —
# фактическое состояние (урезанный max_hp, обрезанная колода) уже несёт их результат.
# Внутреннее состояние реликвий (редкие заряды) не сохраняется — пересоздаются чистыми.

import json
import os

from managers.SaveManager import get_save_path
from core.cards.catalog import make_card_by_id, card_id_of
from core.forge import rebuild_card_linear_to
from core.relics import ALL_RELICS

RUN_SAVE_VERSION = 1
_RUN_FILENAME    = "run_save.json"

_RELIC_BY_ID = {r.__name__: r for r in ALL_RELICS}


def get_run_path():
    """Путь к файлу сейва забега — рядом с мета-сейвом (тот же писабельный каталог)."""
    return get_save_path().with_name(_RUN_FILENAME)


# ── СЕРИАЛИЗАЦИЯ ──────────────────────────────────────────────────────────────

def _node_to_dict(node):
    return {
        "node_type":   node.node_type,
        "col":         node.col,
        "row":         node.row,
        "connections": list(node.connections),
    }


def serialize_run(gm) -> dict:
    """Чистый снимок активного забега в JSON-словарь (тестируется без диска).
    Зовётся ТОЛЬКО на карте (state=MAP)."""
    p = gm.player
    hint = type(p).__name__
    deck = []
    for card in gm.current_deck:
        cid = card_id_of(card, hint_class=hint)
        if cid is None:
            continue   # карта вне реестра (транзиентный Глитч/особая) — пропускаем
        deck.append({
            "id":    cid,
            "fuid":  getattr(card, "_fuid", None),
            "level": _card_level(p, card),
        })

    return {
        "version":      RUN_SAVE_VERSION,
        "player_class": type(p).__name__,
        "hp":           p.hp,
        "max_hp":       p.max_hp,
        "energy":       p.energy,
        "max_energy":   p.max_energy,
        "statuses":     {k: v for k, v in p.statuses.items() if v},
        "forge_points": getattr(p, "forge_points", 0),
        "forge_level_cap": getattr(p, "forge_level_cap", 0),
        "forge_uid_next":  getattr(p, "_forge_uid_next", 0),
        "deck_forge_state": {str(k): v for k, v in getattr(p, "deck_forge_state", {}).items()},
        "mirrored_layout":  getattr(p, "mirrored_layout", False),
        "deck":         deck,
        "relics":       [type(r).__name__ for r in gm.relics],
        "gold":         gm.player_gold,
        "keys":         gm.player_keys,
        "floor":        gm.current_floor,
        "removal_count": gm.removal_count,
        "stats":        dict(gm.stats),
        "map_grid":     [[_node_to_dict(n) for n in row] for row in gm.map_grid],
        "player_path":  list(gm.player_path),
        "current_col":  gm.current_col,
        "stakes":       list(getattr(gm, "pending_stakes", [])),
    }


def _card_level(player, card) -> int:
    from core.forge import forge_level
    return forge_level(player, card)


# ── ВОССТАНОВЛЕНИЕ ────────────────────────────────────────────────────────────

def restore_run(gm, data: dict) -> bool:
    """Восстановить состояние забега из снимка В существующий gm. Возвращает True при
    успехе. Несовместимая версия / отсутствие класса → False (gm не тронут наполовину:
    проверки делаем ДО мутаций)."""
    if not isinstance(data, dict) or data.get("version") != RUN_SAVE_VERSION:
        return False

    from core.players import (
        Warrior, Mage, Berserker, Chemist,
    )
    CLASS_MAP = {
        "Warrior": Warrior, "Mage": Mage,
        "Berserker": Berserker, "Chemist": Chemist,
    }
    cls = CLASS_MAP.get(data.get("player_class"))
    if cls is None:
        return False

    # Пересоздаём игрока (проставит интринсики класса: hp_overdraft/fusion_enabled и т.д.),
    # затем перезаписываем сохранённые поля.
    p = cls()
    p.max_hp = data["max_hp"]
    p.hp     = data["hp"]
    p.max_energy = data.get("max_energy", p.max_energy)
    p.energy = data.get("energy", p.energy)
    for k in list(p.statuses.keys()):
        p.statuses[k] = 0
    for k, v in data.get("statuses", {}).items():
        p.set_status(k, v)
    p.forge_points    = data.get("forge_points", 0)
    p.forge_level_cap = data.get("forge_level_cap", p.forge_level_cap)
    p._forge_uid_next = data.get("forge_uid_next", 0)
    p.deck_forge_state = {int(k): v for k, v in data.get("deck_forge_state", {}).items()}
    if data.get("mirrored_layout"):
        p.mirrored_layout = True

    # Колода: пересоздать карты по id + проставить uid + накатить линейную ковку.
    deck = []
    for entry in data.get("deck", []):
        card = make_card_by_id(entry["id"])
        if card is None:
            continue
        if entry.get("fuid") is not None:
            card._fuid = entry["fuid"]
        rebuild_card_linear_to(card, entry.get("level", 0))
        deck.append(card)

    # Реликвии: пересоздать по имени класса (неизвестные — пропустить).
    relics = []
    for rid in data.get("relics", []):
        rcls = _RELIC_BY_ID.get(rid)
        if rcls is not None:
            relics.append(rcls())

    # Карта этажей.
    from managers.MapGenerator import MapNode
    map_grid = []
    for row in data.get("map_grid", []):
        row_nodes = []
        for nd in row:
            node = MapNode(nd["node_type"], nd["col"], nd["row"])
            node.connections = list(nd.get("connections", []))
            row_nodes.append(node)
        map_grid.append(row_nodes)

    # Заливаем в gm (после успешной сборки — без полу-состояния).
    gm.player        = p
    gm.current_deck  = deck
    gm.relics        = relics
    gm.player_gold   = data.get("gold", 0)
    gm.player_keys   = data.get("keys", 0)
    gm.current_floor = data.get("floor", 1)
    gm.removal_count = data.get("removal_count", 0)
    gm.stats         = data.get("stats", gm.stats)
    gm.map_grid      = map_grid
    gm.player_path   = list(data.get("player_path", []))
    gm.current_col   = data.get("current_col", 1)
    gm.current_state = "MAP"
    gm.active_combat = None
    return True


# ── ДИСКОВЫЙ СЛОЙ ─────────────────────────────────────────────────────────────

def save_run(gm) -> None:
    """Атомарно записать снимок забега. Сбой проглатывается (сейв не критичен)."""
    path = get_run_path()
    tmp  = path.with_suffix(".tmp")
    try:
        data = serialize_run(gm)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except (OSError, ValueError, AttributeError):
        pass


def load_run():
    """Прочитать снимок забега → dict, или None (нет файла / битый / чужая версия)."""
    try:
        path = get_run_path()
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get("version") != RUN_SAVE_VERSION:
            return None
        return data
    except (OSError, ValueError):
        return None


def has_saved_run() -> bool:
    """Есть ли валидный сейв забега (для кнопки «Продолжить» в меню)."""
    return load_run() is not None


def clear_run() -> None:
    """Удалить сейв забега (смерть/победа/начало нового). Тихо, если файла нет."""
    try:
        get_run_path().unlink(missing_ok=True)
    except OSError:
        pass
