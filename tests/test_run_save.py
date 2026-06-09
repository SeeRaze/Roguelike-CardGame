# tests/test_run_save.py
# Сохранение/возобновление активного забега (С57): serialize_run/restore_run —
# round-trip состояния (player/колода/ковка/реликвии/карта/скаляры) без диска +
# дисковый слой save_run/load_run/has_saved_run/clear_run на временном пути.
import json

import pytest

from managers import RunSave
from managers.GameManager import GameManager
from managers.MapGenerator import generate_map
from core.forge import forge_card_one_level, forge_level


@pytest.fixture
def run_gm():
    """Забег в характерном MAP-состоянии: этаж/золото/HP/ковка/статус/карта."""
    gm = GameManager()
    gm.current_floor = 7
    gm.player_gold   = 250
    gm.player_keys   = 2
    gm.player.hp     = 55
    gm.player.forge_points = 12
    gm.player.set_status("discipline", 4)
    gm.map_grid    = generate_map()
    gm.player_path = [(0, 1), (1, 2)]
    gm.current_col = 2
    # Выковать первую карту на 2 уровня (мутация base_val + name+).
    forge_card_one_level(gm.player, gm.current_deck[0], "Warrior")
    forge_card_one_level(gm.player, gm.current_deck[0], "Warrior")
    return gm


def test_снимок_json_сериализуем(run_gm):
    snap = RunSave.serialize_run(run_gm)
    json.dumps(snap, ensure_ascii=False)           # не должно бросить


def test_round_trip_скаляры(run_gm):
    snap = RunSave.serialize_run(run_gm)
    gm2 = GameManager()
    assert RunSave.restore_run(gm2, snap) is True
    assert type(gm2.player).__name__ == "Warrior"
    assert gm2.player.hp == 55
    assert gm2.current_floor == 7
    assert gm2.player_gold == 250
    assert gm2.player_keys == 2
    assert gm2.player.discipline == 4
    assert gm2.current_col == 2
    assert gm2.player_path == [(0, 1), (1, 2)]
    assert gm2.current_state == "MAP"


def test_round_trip_колода_полная(run_gm):
    snap = RunSave.serialize_run(run_gm)
    gm2 = GameManager()
    RunSave.restore_run(gm2, snap)
    assert len(gm2.current_deck) == len(run_gm.current_deck)   # ни одна карта не потеряна


def test_round_trip_ковка_восстановлена(run_gm):
    c0 = run_gm.current_deck[0]
    fuid, base = c0._fuid, c0.effects[0].base_val
    snap = RunSave.serialize_run(run_gm)
    gm2 = GameManager()
    RunSave.restore_run(gm2, snap)
    rc = next(c for c in gm2.current_deck if getattr(c, "_fuid", None) == fuid)
    assert forge_level(gm2.player, rc) == 2                    # уровень ковки восстановлен
    assert rc.effects[0].base_val == base                     # линейная мутация воспроизведена


def test_round_trip_карта_этажей(run_gm):
    snap = RunSave.serialize_run(run_gm)
    gm2 = GameManager()
    RunSave.restore_run(gm2, snap)
    assert len(gm2.map_grid) == len(run_gm.map_grid)
    n0_orig = run_gm.map_grid[0][0]
    n0_rest = gm2.map_grid[0][0]
    assert n0_rest.node_type == n0_orig.node_type
    assert n0_rest.connections == n0_orig.connections


def test_round_trip_реликвии(run_gm):
    from core.relics import ALL_RELICS
    run_gm.relics = [ALL_RELICS[0](), ALL_RELICS[1]()]
    names = [type(r).__name__ for r in run_gm.relics]
    snap = RunSave.serialize_run(run_gm)
    gm2 = GameManager()
    RunSave.restore_run(gm2, snap)
    assert [type(r).__name__ for r in gm2.relics] == names


def test_restore_несовместимая_версия(run_gm):
    snap = RunSave.serialize_run(run_gm)
    snap["version"] = 999
    gm2 = GameManager()
    assert RunSave.restore_run(gm2, snap) is False             # не падает, отказ


def test_дисковый_слой_save_load_clear(run_gm, tmp_path, monkeypatch):
    # Перенаправляем путь сейва во временный каталог.
    fake = tmp_path / "run_save.json"
    monkeypatch.setattr(RunSave, "get_run_path", lambda: fake)
    assert RunSave.has_saved_run() is False
    RunSave.save_run(run_gm)
    assert fake.exists()
    assert RunSave.has_saved_run() is True
    data = RunSave.load_run()
    assert data is not None and data["floor"] == 7
    RunSave.clear_run()
    assert RunSave.has_saved_run() is False


def test_load_битый_файл_none(tmp_path, monkeypatch):
    fake = tmp_path / "run_save.json"
    fake.write_text("{ не json", encoding="utf-8")
    monkeypatch.setattr(RunSave, "get_run_path", lambda: fake)
    assert RunSave.load_run() is None                          # битый → None, не падает


# ═══════════════════════════════════════════════════════════
# UI-флоу: карта «сохранить и выйти» → меню «продолжить»
# ═══════════════════════════════════════════════════════════

def test_ui_флоу_сохранить_продолжить(run_gm, tmp_path, monkeypatch):
    import pygame
    pygame.init()
    pygame.display.set_mode((1920, 1080))
    from ui.MainMenu import MainMenu
    from ui.MapView import MapView

    monkeypatch.setattr(RunSave, "get_run_path", lambda: tmp_path / "run_save.json")

    class _V:
        screen = pygame.display.get_surface()
        screen_width, screen_height = 1920, 1080
        main_font = pygame.font.SysFont("Arial", 20)
        gm = None

    v = _V(); v.gm = run_gm
    run_gm.current_state = "MAP"

    # Карта: рисуем → клик «сохранить и выйти»
    MapView.draw_map(v)
    MapView.handle_click(v, v.btn_map_menu.center)
    assert run_gm.current_state == "MAIN_MENU"
    assert RunSave.has_saved_run() is True

    # Меню (новый gm): кнопка «Продолжить» видна → восстановление в MAP
    gm2 = GameManager()
    v.gm = gm2
    gm2.current_state = "MAIN_MENU"
    MainMenu.draw_menu(v)
    assert v.btn_menu_continue is not None
    MainMenu.handle_clicks(v, v.btn_menu_continue.center)
    assert gm2.current_state == "MAP"
    assert gm2.current_floor == run_gm.current_floor


def test_ui_меню_без_сейва_нет_продолжить(tmp_path, monkeypatch):
    import pygame
    pygame.init()
    pygame.display.set_mode((1920, 1080))
    from ui.MainMenu import MainMenu
    monkeypatch.setattr(RunSave, "get_run_path", lambda: tmp_path / "none.json")

    class _V:
        screen = pygame.display.get_surface()
        screen_width, screen_height = 1920, 1080
        main_font = pygame.font.SysFont("Arial", 20)
        gm = None
    v = _V(); v.gm = GameManager(); v.gm.current_state = "MAIN_MENU"
    MainMenu.draw_menu(v)
    assert v.btn_menu_continue is None          # нет сейва → нет кнопки
