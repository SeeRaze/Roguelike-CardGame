# tests/test_positioning_ui.py
# Позиционка §5b — визуальный «read»: бейдж ранга + разнос союзников по рядам.
# Headless-смоук (SDL dummy из conftest): рендер не падает, раскладка корректна.
import pygame
import pytest
from types import SimpleNamespace

from core.players import Summoner
from core.Summon import Summon
from core.positioning import Rank, Line, assign_party_ranks
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


# ═══════════════════════════════════════════════════════════
# §11 — ось ЛИНИЙ в визуале: бейдж +линия, колонки союзников Л→Ц→П, бейдж врага
# ═══════════════════════════════════════════════════════════

def test_бейдж_с_линией_шире_чем_без():
    screen = pygame.Surface((400, 200))
    font = pygame.font.SysFont("Arial", 16)
    no_line = panels._draw_rank_chip(screen, font, Rank.FRONT, 0, 0)
    with_line = panels._draw_rank_chip(screen, font, Rank.FRONT, 0, 0, Line.CENTER)
    assert with_line.width > no_line.width      # «·Ц» добавилось


def test_бейдж_none_ничего_не_рисует():
    screen = pygame.Surface((400, 200))
    font = pygame.font.SysFont("Arial", 16)
    assert panels._draw_rank_chip(screen, font, None, 0, 0, Line.LEFT) is None


def test_союзники_фронт_сортируются_по_линии_лево_раньше_право():
    screen = pygame.Surface((1920, 1080))
    view = _view()
    right, left = _wolf("Правый"), _wolf("Левый")
    right.rank = Rank.FRONT
    right.line = Line.RIGHT
    left.rank = Rank.FRONT
    left.line = Line.LEFT
    # На вход подаём в ОБРАТНОМ порядке (правый раньше) → сорт по линии переставит.
    panels.draw_ally_panels(view, screen, [right, left])
    assert len(view.ally_panel_rects) == 2
    # Колонки по линии: ЛЕВО (меньший x) раньше ПРАВО.
    assert view.ally_panel_rects[0].x < view.ally_panel_rects[1].x


def test_панели_врагов_с_рангами_рисуются():
    from core.enemies.cultist import Cultist
    screen = pygame.Surface((1920, 1080))
    view = _view()
    es = [Cultist(f"К{i}", 30, 30) for i in range(3)]
    for e in es:
        e.set_intent("attack", 5)
    from core.positioning import assign_enemy_ranks
    assign_enemy_ranks(es)                       # 1 фронт / 2 тыл + линии
    panels.draw_enemy_panels(view, screen, es, Summoner())   # не падает
    assert len(view.enemy_panel_rects) == 3      # rect на каждого врага (таргет-маппинг цел)


def test_враги_с_рангами_два_ряда_фронт_выше_тыла():
    from core.enemies.cultist import Cultist
    from core.positioning import assign_enemy_ranks
    screen = pygame.Surface((1920, 1080))
    view = _view()
    es = [Cultist(f"К{i}", 30, 30) for i in range(3)]
    for e in es:
        e.set_intent("attack", 5)
    assign_enemy_ranks(es)                       # es[0]=фронт, es[1..2]=тыл
    panels.draw_enemy_panels(view, screen, es, Summoner())
    front_y = view.enemy_panel_rects[0].y        # фронт
    back_ys = [view.enemy_panel_rects[i].y for i in (1, 2)]  # тыл
    # Два ряда: фронт-ряд выше тыл-ряда.
    assert all(front_y < by for by in back_ys)
    # Тыловые враги в одном ряду (одинаковый y).
    assert back_ys[0] == back_ys[1]


def test_враги_index_alignment_таргетинг_цел():
    """ИНВАРИАНТ: enemy_panel_rects[i] принадлежит enemies[i] даже когда враг в
    тылу и рисуется в порядке рангов (по нему работает клик-таргетинг)."""
    from core.enemies.cultist import Cultist
    from core.positioning import assign_enemy_ranks
    screen = pygame.Surface((1920, 1080))
    view = _view()
    es = [Cultist(f"К{i}", 30, 30) for i in range(3)]
    for e in es:
        e.set_intent("attack", 5)
    assign_enemy_ranks(es)
    panels.draw_enemy_panels(view, screen, es, Summoner())
    # Все ячейки заполнены rect'ами (ни одного None — таргетинг по индексу не падает).
    assert all(r is not None for r in view.enemy_panel_rects)
    assert len(view.enemy_panel_rects) == 3
    # es[0] — единственный фронт → его rect в верхнем ряду, тыловые ниже.
    assert view.enemy_panel_rects[0].y < view.enemy_panel_rects[2].y


def test_один_враг_босс_полноразмерная_панель():
    from core.enemies.cultist import Cultist
    from core.positioning import assign_enemy_ranks
    from ui.combat.layout import _PANEL_W
    screen = pygame.Surface((1920, 1080))
    view = _view()
    boss = Cultist("Босс", 200, 200)
    boss.set_intent("attack", 20)
    assign_enemy_ranks([boss])                   # 1 враг → фронт, но один ряд
    panels.draw_enemy_panels(view, screen, [boss], Summoner())
    assert len(view.enemy_panel_rects) == 1
    # n==1 остаётся большой полноразмерной панелью (нулевой регресс для боссов).
    assert view.enemy_panel_rects[0].width == _PANEL_W

