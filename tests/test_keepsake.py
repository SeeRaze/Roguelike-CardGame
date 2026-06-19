# tests/test_keepsake.py
# С70 полировка: keepsake L1 (core/keepsake.py) — носимая реликвия по выбору.
# Чистая логика equip/equipped/is_unlocked + инъекция в забег apply_to_run.

from types import SimpleNamespace

from core import keepsake


def _meta(grade_xp=0, ks=None):
    return {"grade_xp": grade_xp, "xp": 0, "keepsake": ks}


# ─── Гейт открытия (L1 = 150 Грейд-Опыта) ─────────────────────────────────────

def test_locked_below_l1():
    assert keepsake.is_unlocked(_meta(grade_xp=0)) is False
    assert keepsake.is_unlocked(_meta(grade_xp=149)) is False


def test_unlocked_at_l1():
    assert keepsake.is_unlocked(_meta(grade_xp=150)) is True
    assert keepsake.is_unlocked(_meta(grade_xp=5000)) is True


def test_none_meta_locked():
    assert keepsake.is_unlocked(None) is False
    assert keepsake.equipped(None) is None


# ─── equip / equipped ─────────────────────────────────────────────────────────

def test_equip_requires_unlock():
    m = _meta(grade_xp=0)
    assert keepsake.equip(m, "Линтер") is False
    assert m["keepsake"] is None


def test_equip_valid_relic():
    m = _meta(grade_xp=150)
    assert keepsake.equip(m, "Линтер") is True
    assert m["keepsake"] == "Линтер"
    assert keepsake.equipped(m) == "Линтер"


def test_equip_rejects_unknown_relic():
    m = _meta(grade_xp=150)
    assert keepsake.equip(m, "НесуществующаяРеликвия") is False
    assert m["keepsake"] is None


def test_unequip_with_none():
    m = _meta(grade_xp=150, ks="Кэшбэк")
    assert keepsake.equipped(m) == "Кэшбэк"
    assert keepsake.equip(m, None) is True
    assert m["keepsake"] is None
    assert keepsake.equipped(m) is None


def test_equipped_ignores_garbage_id():
    # Битый/устаревший сейв: id вне пула → equipped возвращает None, не падает.
    assert keepsake.equipped(_meta(grade_xp=150, ks="МусорныйId")) is None


# ─── Инъекция в забег ─────────────────────────────────────────────────────────

def test_apply_to_run_adds_relic():
    gm = SimpleNamespace(relics=[], meta=_meta(grade_xp=150, ks="Линтер"))
    rid = keepsake.apply_to_run(gm)
    assert rid == "Линтер"
    assert len(gm.relics) == 1
    assert type(gm.relics[0]).__name__ == "Линтер"


def test_apply_to_run_dup_guard():
    gm = SimpleNamespace(relics=[], meta=_meta(grade_xp=150, ks="Линтер"))
    keepsake.apply_to_run(gm)
    # Повторный старт / уже надрафтили эту реликвию — второй раз не добавляем.
    rid = keepsake.apply_to_run(gm)
    assert rid is None
    assert len(gm.relics) == 1


def test_apply_to_run_noop_when_locked():
    gm = SimpleNamespace(relics=[], meta=_meta(grade_xp=0, ks="Линтер"))
    assert keepsake.apply_to_run(gm) is None
    assert gm.relics == []


def test_apply_to_run_noop_when_nothing_equipped():
    gm = SimpleNamespace(relics=[], meta=_meta(grade_xp=150, ks=None))
    assert keepsake.apply_to_run(gm) is None
    assert gm.relics == []


# ─── UI-хелперы ───────────────────────────────────────────────────────────────

def test_display_name_and_description_nonempty():
    for rid in keepsake.KEEPSAKE_RELICS:
        assert keepsake.display_name(rid)        # не пусто
        assert isinstance(keepsake.description(rid), str)


def test_pool_ids_all_resolve_to_relics():
    # Каждый id пула должен соответствовать реальному классу реликвии (иначе
    # apply_to_run/чип молча сломается). Имя класса != display-имя — это норма.
    keepsake._ensure_maps()
    for rid in keepsake.KEEPSAKE_RELICS:
        assert rid in keepsake._BY_ID, f"{rid} нет в пуле реликвий"
