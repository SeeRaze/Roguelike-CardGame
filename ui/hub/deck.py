# ui/hub/deck.py
# Отрисовка анимированной стопки стартовой колоды. Возвращает is_deck_hovered.
import pygame
from ui.cards import CardRenderer
from ui.hub.data import (
    CARD_W, CARD_H, CARD_SPREAD, SCREEN_W, _CLS_Y, _CLS_H,
    _BTN_BORDER, _MUTED_COLOR,
)


def draw_card_back(screen, rect):
    pygame.draw.rect(screen, (25, 25, 45), rect, border_radius=10)
    pygame.draw.rect(screen, _BTN_BORDER,  rect, 2,  border_radius=10)
    inner = rect.inflate(-16, -16)
    pygame.draw.rect(screen, (35, 35, 60), inner, border_radius=6)
    pygame.draw.rect(screen, _BTN_BORDER,  inner, 1, border_radius=6)


def draw_deck_section(view, screen, gm, mouse_pos, font_hint, hover_progress) -> bool:
    """Нарисовать стопку колоды (свёрнутую или раскрытую по hover_progress).
    Возвращает True, если курсор над зоной стопки."""
    deck  = gm.current_deck
    count = len(deck)
    prog  = hover_progress

    # Центрируем стопку
    stack_y = _CLS_Y + _CLS_H + 50

    max_spread   = SCREEN_W - CARD_W - 80
    spread_total = min((count - 1) * CARD_SPREAD * prog, max_spread)

    if count > 1 and prog > 0.01:
        card_step = int(spread_total / (count - 1))
    else:
        card_step = CARD_SPREAD

    # Центрируем раскладку
    total_w  = int(spread_total) + CARD_W if prog > 0.01 else CARD_W
    stack_x  = (SCREEN_W - total_w) // 2

    hover_zone = pygame.Rect(
        stack_x - 10, stack_y - 10,
        total_w + 20, CARD_H + 20
    )
    is_deck_hovered = hover_zone.collidepoint(mouse_pos)

    if prog < 0.01:
        stack_rect = pygame.Rect(stack_x, stack_y, CARD_W, CARD_H)
        draw_card_back(screen, stack_rect)

        font_num = pygame.font.SysFont("Arial", 36, bold=True)
        font_sub = pygame.font.SysFont("Arial", 16)
        n = font_num.render(str(count), True, (255, 255, 255))
        screen.blit(n, (stack_rect.centerx - n.get_width() // 2,
                        stack_rect.centery - 24))
        s = font_sub.render("карт в колоде", True, _MUTED_COLOR)
        screen.blit(s, (stack_rect.centerx - s.get_width() // 2,
                        stack_rect.centery + 16))
    else:
        for i, card in enumerate(deck):
            CardRenderer.draw(
                surface    = screen,
                card       = card,
                x          = stack_x + i * card_step,
                y          = stack_y,
                font_title = view.card_font,
                font_desc  = view.card_desc_font,
                is_hovered = False,
            )

    label = "Наведите для просмотра" if prog < 0.5 else "Стартовая колода"
    lbl   = font_hint.render(label, True, _MUTED_COLOR)
    screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2,
                      stack_y + CARD_H + 12))

    return is_deck_hovered
