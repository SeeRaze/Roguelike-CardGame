# tests/test_status_icons.py
# Лёгкий guard иконок статусов: диспатч рисует КАЖДЫЙ статус из StatusRegistry
# без ошибок (включая фолбэк для неизвестного ключа), и бейджи в HUD дают по
# одному rect на активный статус (для тултипов). Рендер — headless (conftest SDL).
import pygame
import pytest

from core.StatusRegistry import all_keys, STATUSES
from core.Creature import Creature
from ui.status_icons import draw_status_icon


@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    yield
    pygame.quit()


def _surf():
    return pygame.Surface((200, 60))


def test_every_status_icon_draws():
    """Каждая иконка из реестра рисуется без исключения."""
    surf = _surf()
    for key in all_keys():
        draw_status_icon(surf, key, 30, 30, 12, STATUSES[key]["badge_fg"])


def test_unknown_key_falls_back():
    """Неизвестный ключ → буквенный фолбэк, не падает."""
    draw_status_icon(_surf(), "definitely_not_a_status", 30, 30, 12, (255, 255, 255))


def test_icon_draws_at_small_radius():
    """Малый радиус (плотный HUD) не вызывает ошибок деления/полигонов."""
    surf = _surf()
    for key in all_keys():
        draw_status_icon(surf, key, 20, 20, 5, STATUSES[key]["badge_fg"])


def test_badges_return_rect_per_active_status():
    """draw_status_badges возвращает (rect, key, val) на каждый активный статус."""
    from ui.combat.hud import CombatHUD
    font = pygame.font.SysFont("Arial", 16)
    c = Creature("t", 50, 50)
    for key in all_keys():
        setattr(c, key, 2)
    rects = CombatHUD.draw_status_badges(_surf(), font, c, 0, 0)
    assert len(rects) == len(all_keys())
    keys = {key for _rect, key, _val in rects}
    assert keys == set(all_keys())
    assert all(val == 2 for _rect, _key, val in rects)


def test_badges_skip_inactive():
    """Статусы со стаком 0 не дают бейджей."""
    from ui.combat.hud import CombatHUD
    font = pygame.font.SysFont("Arial", 16)
    c = Creature("t", 50, 50)
    c.poison = 4   # только один активен
    rects = CombatHUD.draw_status_badges(_surf(), font, c, 0, 0)
    assert len(rects) == 1
    assert rects[0][1] == "poison"
