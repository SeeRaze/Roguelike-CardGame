# tests/test_relic_panel_scroll.py
# Полировка С51 — прокрутка колесом в модальной панели артефактов.
# Headless-смоук (SDL dummy из conftest): переполнение списка включает прокрутку,
# смещение клампится к [0, max], малый список не скроллит, клип сбрасывается.
import pygame
import pytest
from types import SimpleNamespace

from ui.combat.relic_panel import RelicPanel
from core.relics import ALL_RELICS


@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    pygame.font.init()
    yield
    pygame.quit()


def _view(relics):
    font = pygame.font.SysFont("Arial", 16)
    return SimpleNamespace(
        main_font=font, card_font=font, card_desc_font=font,
        gm=SimpleNamespace(relics=relics),
    )


def _many_relics(n):
    pool = [c() for c in ALL_RELICS]
    return [pool[i % len(pool)] for i in range(n)]


def test_переполнение_списка_включает_прокрутку():
    screen = pygame.Surface((1920, 1080))
    view = _view(_many_relics(30))
    RelicPanel.open(view)
    RelicPanel.draw(view, screen)
    assert RelicPanel._max_scroll > 0          # 30 реликвий не влезают


def test_малый_список_не_прокручивается():
    screen = pygame.Surface((1920, 1080))
    view = _view(_many_relics(2))
    RelicPanel.open(view)
    RelicPanel.draw(view, screen)
    assert RelicPanel._max_scroll == 0


def test_прокрутка_вниз_клампится_к_максимуму():
    screen = pygame.Surface((1920, 1080))
    view = _view(_many_relics(30))
    RelicPanel.open(view)
    RelicPanel.draw(view, screen)              # посчитать _max_scroll
    for _ in range(100):                       # заведомо больше предела
        RelicPanel.scroll(1)
    RelicPanel.draw(view, screen)
    assert RelicPanel._scroll == RelicPanel._max_scroll


def test_прокрутка_вверх_клампится_к_нулю():
    screen = pygame.Surface((1920, 1080))
    view = _view(_many_relics(30))
    RelicPanel.open(view)
    RelicPanel.draw(view, screen)
    for _ in range(100):
        RelicPanel.scroll(1)
    for _ in range(200):                        # за нижнюю границу
        RelicPanel.scroll(-1)
    RelicPanel.draw(view, screen)
    assert RelicPanel._scroll == 0


def test_открытие_сбрасывает_прокрутку_на_верх():
    screen = pygame.Surface((1920, 1080))
    view = _view(_many_relics(30))
    RelicPanel.open(view)
    RelicPanel.draw(view, screen)
    for _ in range(10):
        RelicPanel.scroll(1)
    assert RelicPanel._scroll > 0
    RelicPanel.open(view)                       # повторное открытие
    assert RelicPanel._scroll == 0


def test_клип_сбрасывается_после_отрисовки():
    screen = pygame.Surface((1920, 1080))
    view = _view(_many_relics(30))
    RelicPanel.open(view)
    RelicPanel.draw(view, screen)
    assert screen.get_clip() == pygame.Rect(0, 0, 1920, 1080)


def test_видимы_только_попадающие_в_область_ряды():
    screen = pygame.Surface((1920, 1080))
    view = _view(_many_relics(30))
    RelicPanel.open(view)
    RelicPanel.draw(view, screen)
    # При переполнении в кликабельный список идут не все реликвии (часть за краем).
    assert 0 < len(view.relic_panel_cell_rects) < 30
