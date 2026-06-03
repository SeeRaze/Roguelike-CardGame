# ui/victory/modal.py
# Модальное окно подтверждения «Пропустить награду?».
import pygame
from ui.victory.data import (
    _GOLD_C, _WHITE, _GRAY, _GREEN, _MODAL_BG,
    _BTN_YES, _BTN_YES_H, _BTN_NO, _BTN_NO_H,
)


def draw_modal(vs, screen, W, H, body_font, small_font, mouse):
    """Рисует модалку. Заполняет vs._modal_yes / vs._modal_no."""
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    mw, mh = 480, 220
    mx     = W // 2 - mw // 2
    my     = H // 2 - mh // 2
    modal  = pygame.Rect(mx, my, mw, mh)
    pygame.draw.rect(screen, _MODAL_BG, modal, border_radius=12)
    pygame.draw.rect(screen, (180, 180, 100), modal, 2, border_radius=12)

    q_surf = body_font.render("Пропустить награду?", True, _GOLD_C)
    screen.blit(q_surf, (mx + mw // 2 - q_surf.get_width() // 2, my + 40))

    hint = small_font.render("Неполученные награды будут потеряны", True, _GRAY)
    screen.blit(hint, (mx + mw // 2 - hint.get_width() // 2, my + 85))

    vs._modal_yes = pygame.Rect(mx + 60, my + 135, 160, 50)
    hov_yes = vs._modal_yes.collidepoint(mouse)
    pygame.draw.rect(screen, _BTN_YES_H if hov_yes else _BTN_YES,
                     vs._modal_yes, border_radius=8)
    pygame.draw.rect(screen, (220, 80, 80), vs._modal_yes, 1, border_radius=8)
    yes_lbl = body_font.render("Да", True, _WHITE)
    screen.blit(yes_lbl, (vs._modal_yes.centerx - yes_lbl.get_width() // 2,
                          vs._modal_yes.centery - yes_lbl.get_height() // 2))

    vs._modal_no = pygame.Rect(mx + 260, my + 135, 160, 50)
    hov_no = vs._modal_no.collidepoint(mouse)
    pygame.draw.rect(screen, _BTN_NO_H if hov_no else _BTN_NO,
                     vs._modal_no, border_radius=8)
    pygame.draw.rect(screen, _GREEN, vs._modal_no, 1, border_radius=8)
    no_lbl = body_font.render("Нет", True, _WHITE)
    screen.blit(no_lbl, (vs._modal_no.centerx - no_lbl.get_width() // 2,
                         vs._modal_no.centery - no_lbl.get_height() // 2))
