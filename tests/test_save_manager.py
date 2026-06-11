# tests/test_save_manager.py
# Локальная персистентность мета-прогрессии (managers/SaveManager.py, Сессия 40).
# Изоляция: monkeypatch get_save_path → tmp_path (без записи в реальный %APPDATA%),
# reset_cache между тестами (модульный кэш не течёт между кейсами).

import json

import pytest

from managers import SaveManager as SM


@pytest.fixture
def isolated_save(tmp_path, monkeypatch):
    """SaveManager, пишущий в tmp_path; кэш сброшен до и после теста."""
    save_file = tmp_path / "meta_save.json"
    monkeypatch.setattr(SM, "get_save_path", lambda: save_file)
    SM.reset_cache()
    yield save_file
    SM.reset_cache()


def _run(cls="Warrior", floor=5, kills=10, bosses=1, dmg=30, name="tester"):
    return {"username": name, "class": cls, "max_floor": floor,
            "kills": kills, "bosses": bosses, "max_damage": dmg}


# ─── Загрузка / дефолт ────────────────────────────────────────────────────────

def test_default_meta_when_no_file(isolated_save):
    meta = SM.get_meta()
    assert meta["version"] == SM.SAVE_VERSION
    assert meta["stats"]["total_runs"] == 0
    assert meta["runs"] == []
    assert meta["class_best"] == {}


def test_corrupted_file_falls_back_to_default(isolated_save):
    isolated_save.write_text("{ это не валидный json", encoding="utf-8")
    SM.reset_cache()
    meta = SM.get_meta()
    assert meta["stats"]["total_runs"] == 0      # дефолт, без падения


def test_wrong_version_falls_back(isolated_save):
    isolated_save.write_text(json.dumps({"version": 999, "stats": {}}),
                             encoding="utf-8")
    SM.reset_cache()
    assert SM.get_meta()["version"] == SM.SAVE_VERSION


# ─── Запись / round-trip ──────────────────────────────────────────────────────

def test_record_run_writes_file_and_updates_cache(isolated_save):
    SM.record_run(_run(floor=7, kills=12, bosses=1, dmg=40))
    assert isolated_save.exists()                 # файл записан
    meta = SM.get_meta()
    assert meta["stats"]["total_runs"] == 1
    assert meta["stats"]["best_floor"] == 7
    assert meta["stats"]["max_damage_ever"] == 40


def test_round_trip_persists_across_reload(isolated_save):
    SM.record_run(_run(floor=9))
    SM.reset_cache()                              # имитируем перезапуск игры
    meta = SM.get_meta()
    assert meta["stats"]["total_runs"] == 1
    assert meta["stats"]["best_floor"] == 9


def test_atomic_write_no_tmp_left(isolated_save):
    SM.record_run(_run())
    assert not isolated_save.with_suffix(".tmp").exists()   # temp убран os.replace


# ─── _apply_run (чистая логика, без диска) ────────────────────────────────────

def test_apply_run_accumulates_and_takes_max():
    meta = SM._default_meta()
    SM._apply_run(meta, _run(floor=5, kills=10, bosses=1, dmg=30))
    SM._apply_run(meta, _run(floor=3, kills=8,  bosses=0, dmg=50))
    s = meta["stats"]
    assert s["total_runs"]      == 2
    assert s["best_floor"]      == 5      # max
    assert s["total_kills"]     == 18     # sum
    assert s["total_bosses"]    == 1      # sum
    assert s["max_damage_ever"] == 50     # max


def test_apply_run_class_best_per_class():
    meta = SM._default_meta()
    SM._apply_run(meta, _run(cls="Mage",   floor=4, dmg=20))
    SM._apply_run(meta, _run(cls="Mage",   floor=8, dmg=15))
    SM._apply_run(meta, _run(cls="Berserker", floor=6, dmg=99))
    assert meta["class_best"]["Mage"]["best_floor"]  == 8
    assert meta["class_best"]["Mage"]["max_damage"]  == 20    # max по классу
    assert meta["class_best"]["Mage"]["runs"]        == 2
    assert meta["class_best"]["Berserker"]["best_floor"] == 6


def test_runs_ring_capped():
    meta = SM._default_meta()
    for i in range(SM.RUNS_CAP + 10):
        SM._apply_run(meta, _run(floor=i))
    assert len(meta["runs"]) == SM.RUNS_CAP
    assert meta["runs"][-1]["max_floor"] == SM.RUNS_CAP + 9   # последние сохранены


# ─── Анлоки классов (С50) ─────────────────────────────────────────────────────

def test_default_meta_has_empty_unlocks():
    assert SM._default_meta()["unlocks"] == []


def test_record_run_grants_and_persists_unlock(isolated_save):
    # Этаж 8 выполняет условие Summoner(≥6)+Chemist(≥8).
    fresh = SM.record_run(_run(floor=8, bosses=1))
    assert set(fresh) == {"Summoner", "Chemist"}          # возвращены новооткрытые
    SM.reset_cache()                                       # имитируем перезапуск
    assert set(SM.get_meta()["unlocks"]) == {"Summoner", "Chemist"}


def test_record_run_no_unlock_returns_empty(isolated_save):
    assert SM.record_run(_run(floor=3, bosses=0)) == []    # условия не выполнены


def test_old_save_without_unlocks_key_is_merge_safe(isolated_save):
    # Сейв из старой версии (Сессия 40) не имеет ключа "unlocks".
    isolated_save.write_text(json.dumps({
        "version": SM.SAVE_VERSION,
        "stats": {"total_runs": 1, "best_floor": 4},
    }), encoding="utf-8")
    SM.reset_cache()
    assert SM.get_meta()["unlocks"] == []                  # дефолт подставлен, не падаем


# ─── leaderboard_rows ─────────────────────────────────────────────────────────

def test_leaderboard_sorts_by_floor_then_kills():
    meta = SM._default_meta()
    SM._apply_run(meta, _run(name="a", floor=5, kills=10))
    SM._apply_run(meta, _run(name="b", floor=9, kills=2))
    SM._apply_run(meta, _run(name="c", floor=9, kills=8))
    rows = SM.leaderboard_rows(meta)
    assert [r["username"] for r in rows[:3]] == ["c", "b", "a"]   # 9/8, 9/2, 5/10


def test_leaderboard_merges_network_with_class():
    meta = SM._default_meta()
    SM._apply_run(meta, _run(name="local", cls="Mage", floor=4))
    net = [{"username": "cloud", "max_floor": 12, "kills": 5, "max_damage": 7}]
    rows = SM.leaderboard_rows(meta, network_rows=net)
    top = rows[0]
    assert top["username"] == "cloud" and top["max_floor"] == 12
    assert top["class"] == "—"                    # сетевая строка без класса
    assert any(r["username"] == "local" and r["class"] == "Mage" for r in rows)


def test_leaderboard_dedup_and_cap():
    meta = SM._default_meta()
    for _ in range(SM.LEADERBOARD_CAP + 5):
        SM._apply_run(meta, _run(name="dup", floor=5, kills=5, dmg=5))
    rows = SM.leaderboard_rows(meta)
    assert len(rows) == 1                          # идентичные схлопнуты в одну


def test_leaderboard_dedup_local_and_network_echo():
    # Регресс: один забег приходит локально (с классом) И из сети (эхо Google POST
    # БЕЗ класса). Раньше класс входил в ключ дедупа → две строки на один забег.
    # Теперь дедуп игнорирует класс, а известный класс подтягивается в строку.
    meta = SM._default_meta()
    SM._apply_run(meta, _run(name="me", cls="Warrior", floor=8, kills=12, dmg=40))
    net_echo = [{"username": "me", "class": "—", "max_floor": 8,
                 "kills": 12, "max_damage": 40}]
    rows = SM.leaderboard_rows(meta, network_rows=net_echo)
    assert len(rows) == 1                           # НЕ дублируется
    assert rows[0]["class"] == "Warrior"            # класс не потерян из-за сети


def test_leaderboard_network_class_fills_when_local_unknown():
    # Обратный порядок: локальный забег без класса, сеть знает класс → подтянуть.
    meta = SM._default_meta()
    SM._apply_run(meta, _run(name="me", cls="—", floor=8, kills=12, dmg=40))
    net = [{"username": "me", "class": "Mage", "max_floor": 8,
            "kills": 12, "max_damage": 40}]
    rows = SM.leaderboard_rows(meta, network_rows=net)
    assert len(rows) == 1
    assert rows[0]["class"] == "Mage"
