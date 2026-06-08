# ui/shop/remove_view.py
# Экран утилизации: сетка карт колоды с прокруткой, клик по карте — сжечь.
import pygame
from ui.shop.data import _PANEL_COLOR, _BTN_BORDER, _TEXT_COLOR, _RED_COLOR


def draw_remove(shop, view, screen, fonts):
    W, H      = screen.get_size()
    mouse_pos = pygame.mouse.get_pos()
    title_font, text_font = fonts["title"], fonts["text"]

    panel = pygame.Rect(40, 20, W - 80, H - 40)
    pygame.draw.rect(screen, _PANEL_COLOR, panel, border_radius=16)
    pygame.draw.rect(screen, _BTN_BORDER,  panel, 2, border_radius=16)

    title = title_font.render("УТИЛИЗАЦИЯ: ВЫБЕРИТЕ КАРТУ", True, _RED_COLOR)
    screen.blit(title, (W // 2 - title.get_width() // 2, 45))

    hint = text_font.render(
        "Кликните по карте для уничтожения  |  Колесо мыши -- прокрутка",
        True, _TEXT_COLOR)
    screen.blit(hint, (W // 2 - hint.get_width() // 2, 110))

    # Кнопка «Назад» — выйти без удаления (игрок мог зайти просто посмотреть колоду).
    # Справа, чтобы не налезать на HUD ресурсов (как «← ГОТОВО» в ковке карт).
    back_rect = pygame.Rect(W - 40 - 200, 42, 200, 52)
    back_hov  = back_rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, (60, 50, 30) if back_hov else (40, 34, 22),
                     back_rect, border_radius=10)
    pygame.draw.rect(screen, _BTN_BORDER, back_rect, 2, border_radius=10)
    back_lbl = text_font.render("← Назад", True, _TEXT_COLOR)
    screen.blit(back_lbl, (back_rect.centerx - back_lbl.get_width() // 2,
                           back_rect.centery - back_lbl.get_height() // 2))
    view.shop_remove_back_rect = back_rect

    cards_per_row = 7
    card_w, card_h = view.card_width, view.card_height
    spacing_x = card_w + 24
    spacing_y = card_h + 36
    total_w   = cards_per_row * spacing_x - 24
    start_x   = W // 2 - total_w // 2
    start_y   = 165

    clip_rect = pygame.Rect(60, start_y, W - 120, H - start_y - 30)
    screen.set_clip(clip_rect)

    hovered_card_data = None
    view.shop_remove_card_rects = []

    for index, card in enumerate(view.gm.current_deck):
        row    = index // cards_per_row
        col    = index % cards_per_row
        card_x = start_x + col * spacing_x
        card_y = start_y + 10 + row * spacing_y - view.scroll_y
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        view.shop_remove_card_rects.append((card_rect, index))
        is_hov = card_rect.collidepoint(mouse_pos)
        if is_hov:
            hovered_card_data = (card, card_rect)
        draw_y = card_y - 10 if is_hov else card_y
        view.draw_card_by_data(card, card_x, draw_y)

    screen.set_clip(None)

    # Тултип поверх clip -- последним
    if hovered_card_data:
        card, rect = hovered_card_data
        from ui.cards import CardRenderer
        CardRenderer.draw_card_keyword_tooltip(
            screen, view.card_font, view.card_desc_font, card, rect
        )
