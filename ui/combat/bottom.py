# ui/combat/bottom.py
# Нижняя зона боевого экрана: рука, стопки добора/сброса, кнопка конца хода.
import pygame
from ui.combat.layout import _PANEL_BORDER, _WHITE, _BLUE, _GRAY


def draw_hand(view, screen, dm, enemies, player):
    # Для превью карт берём первого живого врага
    target = None
    if enemies:
        target = next((e for e in enemies if e.hp > 0), enemies[0])
    hand_size = len(dm.hand)
    for index, card in enumerate(dm.hand):
        card_x = view.calculate_card_x(index, hand_size)
        card_y = (view.base_y - 40
                  if index == view.hover.card_index
                  else view.base_y)
        view.draw_card_by_data(card, card_x, card_y,
                               enemy=target, player=player)


def draw_piles(view, screen, dm):
    _draw_pile(
        screen, view.card_font, view.card_desc_font,
        view.draw_pile_rect, len(dm.draw_pile), "ДОБОР", _BLUE
    )
    _draw_pile(
        screen, view.card_font, view.card_desc_font,
        view.discard_pile_rect, len(dm.discard_pile), "СБРОС", _GRAY
    )


def _draw_pile(screen, font_title, font_desc, rect, count, label, color):
    pygame.draw.rect(screen, (28, 28, 48), rect, border_radius=8)
    pygame.draw.rect(screen, color, rect, 2, border_radius=8)

    inner = rect.inflate(-12, -12)
    pygame.draw.rect(screen, (38, 38, 60), inner, border_radius=4)
    for i in range(inner.left + 8, inner.right, 16):
        pygame.draw.line(screen, (48, 48, 72),
                         (i, inner.top), (i, inner.bottom))
    for j in range(inner.top + 8, inner.bottom, 16):
        pygame.draw.line(screen, (48, 48, 72),
                         (inner.left, j), (inner.right, j))

    count_surf = font_title.render(str(count), True, (230, 230, 230))
    screen.blit(count_surf, (
        rect.centerx - count_surf.get_width() // 2,
        rect.centery - count_surf.get_height() // 2
    ))
    label_surf = font_desc.render(label, True, color)
    screen.blit(label_surf, (
        rect.centerx - label_surf.get_width() // 2,
        rect.bottom + 6
    ))


def draw_end_turn_btn(view, screen):
    dr    = view.discard_pile_rect
    btn_w = 220
    btn_h = 52
    btn   = pygame.Rect(dr.right - btn_w, dr.top - btn_h - 12, btn_w, btn_h)
    view.end_turn_rect = btn

    # Hover считаем напрямую -- не зависим от InputHandler
    hover        = btn.collidepoint(pygame.mouse.get_pos())
    bg           = (70, 70, 120) if hover else (40, 40, 75)
    border_color = (200, 200, 255) if hover else _PANEL_BORDER

    pygame.draw.rect(screen, bg, btn, border_radius=12)
    pygame.draw.rect(screen, border_color, btn, 2, border_radius=12)

    if hover:
        glow = btn.inflate(-4, -4)
        pygame.draw.rect(screen, (100, 100, 180), glow, 1, border_radius=10)

    lbl = view.card_desc_font.render("КОНЕЦ ХОДА", True,
                                     (255, 255, 255) if hover else _WHITE)
    screen.blit(lbl, (
        btn.centerx - lbl.get_width() // 2,
        btn.centery - lbl.get_height() // 2
    ))
