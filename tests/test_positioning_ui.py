# tests/test_positioning_ui.py
# Позиционка §5b — визуальный «read»: бейдж ранга + разнос союзников по рядам.
# Headless-смоук (SDL dummy из conftest): рендер не падает, раскладка корректна.
import pygame
import pytest
from types import SimpleNamespace

from core.players import Summoner
from core.Summon import Summon
from core.positioning import Rank, assign_party_ranks
from ui.combat import panels


@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    pygame.font.init()
    yield
    pygame.quit()


def _view():
    font = pygame.font.SysFont("Arial", 16)
    return SimpleNamespace(
        main_font=font, card_desc_font=font,
        gm=SimpleNamespace(relics=[]),
    )


def _wolf(name):
    return Summon(name=name, hp=12, attack_power=4)


def test_панель_игрока_с_бейджем_ранга_рисуется():
    screen = pygame.Surface((1920, 1080))
    view = _view()
    player = Summoner()
    player.rank = Rank.BACK
    panels.draw_player_panel(view, screen, player, 0)   # не падает
    assert hasattr(view, "player_badge_rects")


def test_союзники_без_рангов_одноряд():
    screen = pygame.Surface((1920, 1080))
    view = _view()
    w1, w2 = _wolf("Волк1"), _wolf("Волк2")             # rank=None
    panels.draw_ally_panels(view, screen, [w1, w2])
    assert len(view.ally_panel_rects) == 2
    # Одноряд: одинаковый y, разный x (как было до позиционки).
    assert view.ally_panel_rects[0].y == view.ally_panel_rects[1].y
    assert view.ally_panel_rects[0].x != view.ally_panel_rects[1].x


def test_союзники_с_рангами_два_ряда():
    screen = pygame.Surface((1920, 1080))
    view = _view()
    front, back = _wolf("Фронт"), _wolf("Тыл")
    front.rank = Rank.FRONT
    back.rank = Rank.BACK
    panels.draw_ally_panels(view, screen, [front, back])
    assert len(view.ally_panel_rects) == 2
    # Два ряда: фронт-ряд выше тыл-ряда (разный y).
    ys = sorted(r.y for r in view.ally_panel_rects)
    assert ys[0] < ys[1]


def test_зеркало_оба_саммона_во_фронт_ряду():
    screen = pygame.Surface((1920, 1080))
    view = _view()
    hero = Summoner()
    w1, w2 = _wolf("Волк1"), _wolf("Волк2")
    assign_party_ranks(hero, [w1, w2], mirrored=True)   # оба фронт
    panels.draw_ally_panels(view, screen, [w1, w2])
    assert len(view.ally_panel_rects) == 2
    # Оба во фронте → один ряд (одинаковый y).
    assert view.ally_panel_rects[0].y == view.ally_panel_rects[1].y
