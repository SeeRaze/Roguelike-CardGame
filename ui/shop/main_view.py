# ui/shop/main_view.py
# Главный экран магазина: 2 карты на продажу, кнопки «Сжечь карту» / «Покинуть».
import pygame
from ui.shop.data import (
    _PANEL_COLOR, _BTN_COLOR, _BTN_HOVER_COLOR, _BTN_BORDER, _TITLE_COLOR,
    _GOLD_COLOR, _RED_COLOR, _GRAY_COLOR, _SOLD_COLOR, get_card_price,
)


def _draw_sold_slot(screen, rect, text_font):
    pygame.draw.rect(screen, _SOLD_COLOR, rect, border_radius=8)
    pygame.draw.rect(screen, _GRAY_COLOR, rect, 1, border_radius=8)
    lbl = text_font.render("[ПРОДАНО]", True, _GRAY_COLOR)
    screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                      rect.centery - lbl.get_height() // 2))


def draw_main(shop, view, screen, fonts):
    W, _H     = screen.get_size()
    mouse_pos = pygame.mouse.get_pos()
    title_font, text_font, btn_font, price_font = (
        fonts["title"], fonts["text"], fonts["btn"], fonts["price"]
    )

    panel = pygame.Rect(W // 2 - 560, 40, 1120, 960)
    pygame.draw.rect(screen, _PANEL_COLOR, panel, border_radius=16)
    pygame.draw.rect(screen, _BTN_BORDER,  panel, 2, border_radius=16)

    title = title_font.render(
        f"ЭТАЖ {view.gm.current_floor}: ЛАВКА ТОРГОВЦА", True, _TITLE_COLOR)
    screen.blit(title, (W // 2 - title.get_width() // 2, 70))

    gold_surf = text_font.render(
        f"Золото: {view.gm.player_gold} монет", True, _GOLD_COLOR)
    screen.blit(gold_surf, (W // 2 - gold_surf.get_width() // 2, 135))

    card_price = get_card_price(view.gm.current_floor)
    card_w, card_h = view.card_width, view.card_height
    gap    = 80
    total_cards_w = card_w * 2 + gap
    card1_x = W // 2 - total_cards_w // 2
    card2_x = card1_x + card_w + gap
    cards_y = 210

    hovered_card_data = None

    for item, item_x, rect_attr in (
        (shop.item_1, card1_x, "shop_item_1_rect"),
        (shop.item_2, card2_x, "shop_item_2_rect"),
    ):
        rect = pygame.Rect(item_x, cards_y, card_w, card_h)
        setattr(view, rect_attr, rect)
        if item:
            is_hov = rect.collidepoint(mouse_pos)
            if is_hov:
                hovered_card_data = (item, rect)
            draw_y = cards_y - 15 if is_hov else cards_y
            view.draw_card_by_data(item, item_x, draw_y)
            p = price_font.render(f"{card_price} з.", True, _GOLD_COLOR)
            screen.blit(p, (item_x + card_w // 2 - p.get_width() // 2,
                            draw_y + card_h + 10))
        else:
            _draw_sold_slot(screen, rect, text_font)

    sep_y = cards_y + card_h + 70
    pygame.draw.line(screen, _BTN_BORDER,
                     (W // 2 - 460, sep_y), (W // 2 + 460, sep_y), 1)

    # Кнопка «Сжечь карту»
    view.btn_shop_remove_rect = pygame.Rect(W // 2 - 320, sep_y + 24, 640, 72)
    shop.is_remove_hovered = view.btn_shop_remove_rect.collidepoint(mouse_pos)
    col = (80, 35, 25) if shop.is_remove_hovered else (50, 20, 15)
    pygame.draw.rect(screen, col, view.btn_shop_remove_rect, border_radius=12)
    pygame.draw.rect(screen, _RED_COLOR, view.btn_shop_remove_rect, 2, border_radius=12)
    lbl = btn_font.render(
        f"СЖЕЧЬ КАРТУ  ({view.gm.get_removal_price()} з.)", True, _RED_COLOR)
    screen.blit(lbl, (view.btn_shop_remove_rect.centerx - lbl.get_width() // 2,
                      view.btn_shop_remove_rect.centery - lbl.get_height() // 2))

    # Кнопка «Покинуть»
    view.btn_shop_leave_rect = pygame.Rect(W // 2 - 320, sep_y + 116, 640, 72)
    shop.is_leave_hovered = view.btn_shop_leave_rect.collidepoint(mouse_pos)
    col = _BTN_HOVER_COLOR if shop.is_leave_hovered else _BTN_COLOR
    pygame.draw.rect(screen, col, view.btn_shop_leave_rect, border_radius=12)
    pygame.draw.rect(screen, _BTN_BORDER, view.btn_shop_leave_rect, 2, border_radius=12)
    lbl = btn_font.render("ПОКИНУТЬ МАГАЗИН", True, (255, 255, 255))
    screen.blit(lbl, (view.btn_shop_leave_rect.centerx - lbl.get_width() // 2,
                      view.btn_shop_leave_rect.centery - lbl.get_height() // 2))

    # Тултип карты -- последним, поверх всего
    if hovered_card_data:
        card, rect = hovered_card_data
        from ui.cards import CardRenderer
        CardRenderer.draw_card_keyword_tooltip(
            screen, view.card_font, view.card_desc_font, card, rect
        )
