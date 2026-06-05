# ui/resource_hud.py
# Единая строка ресурсов игрока на ВСЕХ экранах забега: HP / Золото / FP (+ бейджи
# реликвий вне боя). Один источник правды вместо разрозненных подписей по экранам.
# В БОЮ реликвии не дублируются строкой — они в панели героя (ui/combat/panels.py);
# на карте башня-инфо уведена вправо (ui/MapView.py), чтобы освободить верх-лево.
import pygame
from ui.combat.hud import _RELIC_BADGE

_HP_COLOR   = (120, 220, 120)
_GOLD_COLOR = (255, 215,  0)
_FP_COLOR   = (120, 200, 235)
_SEP_COLOR  = (110, 110, 140)
_PAD        = 12
_STRIP_H    = max(46, _RELIC_BADGE + 4)

# Экраны забега с единой строкой ресурсов слева-сверху (включая бой). Меню/
# лидерборд/победа/хаб/библиотека — свои раскладки.
_SHOW_STATES = {"COMBAT", "MAP", "EVENT", "CAMPFIRE", "SHOP", "CHEST"}


def draw_resource_hud(view):
    """Строка HP/Золото/FP + бейджи реликвий слева-сверху на точках интереса."""
    gm = getattr(view, "gm", None)
    if gm is None or gm.current_state not in _SHOW_STATES:
        return
    player = getattr(gm, "player", None)
    if player is None:
        return

    font = view.card_font
    parts = [
        (f"HP {player.hp}/{player.max_hp}",          _HP_COLOR),
        (f"Золото {getattr(gm, 'player_gold', 0)}",  _GOLD_COLOR),
        (f"FP {getattr(player, 'forge_points', 0)}", _FP_COLOR),
    ]
    surfs = [font.render(t, True, c) for t, c in parts]
    sep   = font.render("  •  ", True, _SEP_COLOR)
    text_w = (sum(s.get_width() for s in surfs)
              + sep.get_width() * (len(surfs) - 1))

    x, y = 24, 14
    # Плашка под текст ресурсов.
    plate_w = text_w + _PAD * 2
    bg = pygame.Surface((plate_w, _STRIP_H), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 150))
    view.screen.blit(bg, (x, y))

    cx = x + _PAD
    cy = y + (_STRIP_H - surfs[0].get_height()) // 2
    for i, s in enumerate(surfs):
        view.screen.blit(s, (cx, cy))
        cx += s.get_width()
        if i < len(surfs) - 1:
            view.screen.blit(sep, (cx, cy))
            cx += sep.get_width()

    # Кнопка «АРТЕФАКТЫ (N)» справа от ресурсов — открывает модальную панель
    # RelicPanel (ui/combat/relic_panel.py). В бою реликвии в панели героя,
    # кнопку строкой не дублируем.
    relics = getattr(gm, "relics", None)
    if relics and gm.current_state != "COMBAT":
        btn_text = f"АРТЕФАКТЫ ({len(relics)})"
        btn_surf = font.render(btn_text, True, (255, 220, 60))
        btn_w = btn_surf.get_width() + _PAD * 2
        btn_h = _STRIP_H - 4
        btn_rect = pygame.Rect(x + plate_w + 12, y + 2, btn_w, btn_h)
        view.hud_relic_btn_rect = btn_rect
        hovered = btn_rect.collidepoint(pygame.mouse.get_pos())
        btn_bg = (55, 45, 20) if hovered else (35, 28, 12)
        pygame.draw.rect(view.screen, btn_bg, btn_rect, border_radius=8)
        pygame.draw.rect(view.screen, (180, 140, 40), btn_rect, 2, border_radius=8)
        view.screen.blit(btn_surf, (btn_rect.x + _PAD,
                                     btn_rect.centery - btn_surf.get_height() // 2))
