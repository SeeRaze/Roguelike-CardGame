# ui/resource_hud.py
# Единая верхняя панель игрока на точках интереса забега: HP / Золото / FP +
# бейджи реликвий. Один источник правды вместо разрозненных подписей по экранам.
# В БОЮ не рисуется: там верх занят плашкой реликвий, а ресурсы показывает боевая
# панель игрока (HP-бар + Золото + FP). См. ui/combat/panels.py.
import pygame
from ui.combat.hud import CombatHUD, _RELIC_BADGE

_HP_COLOR   = (120, 220, 120)
_GOLD_COLOR = (255, 215,  0)
_FP_COLOR   = (120, 200, 235)
_SEP_COLOR  = (110, 110, 140)
_PAD        = 12
_STRIP_H    = max(46, _RELIC_BADGE + 4)

# Экраны-точки интереса с СВОБОДНЫМ верх-лево (панель центрирована). Карта НЕ
# входит: её верх-лево занят заголовком, а ресурсы (золото/ключи/HP/FP/реликвии)
# показывает её собственная правая шапка (ui/MapView.py). Бой/меню/лидерборд/
# победа/хаб/библиотека — свои раскладки.
_SHOW_STATES = {"EVENT", "CAMPFIRE", "SHOP", "CHEST"}


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

    # Бейджи реликвий справа от ресурсов (тот же вид, что в бою). Только показ:
    # ховер-тултип реликвий — отдельная итерация (HUD-читаемость).
    relics = getattr(gm, "relics", None)
    if relics:
        rx = x + plate_w + 12
        ry = y + (_STRIP_H - _RELIC_BADGE) // 2
        view.hud_relic_rects, _ = CombatHUD.draw_relics(
            view.screen, relics, rx, ry, max_x=1900)
