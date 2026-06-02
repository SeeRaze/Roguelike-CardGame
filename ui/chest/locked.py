import pygame
from ui.chest.shared import (
    draw_card_row, draw_take_skip_buttons,
    draw_continue_button, draw_leave_button,
)

CARD_W = 180
CARD_H = 250

_TEXT_COLOR = (200, 200, 200)
_GOLD_COLOR = (255, 210,  50)


def draw_locked(view, screen, sub_font, card_font, desc_font, small_font):
    gm      = view.gm
    has_key = getattr(gm, "player_keys", 0) > 0
    cards   = getattr(gm, "chest_cards", [])

    key_text  = f"[КЛЮЧ x{gm.player_keys}]" if has_key else "[НЕТ КЛЮЧА]"
    key_color = (255, 215, 0) if has_key else (160, 80, 80)
    ks = sub_font.render(key_text, True, key_color)
    screen.blit(ks, (960 - ks.get_width() // 2, 115))

    if not has_key and not gm.chest_opened:
        msg = sub_font.render(
            "Для открытия нужен ключ. Ключи выпадают с боссов.",
            True, _TEXT_COLOR
        )
        screen.blit(msg, (960 - msg.get_width() // 2, 320))
        draw_leave_button(view, screen, card_font)
        return

    hint = "Выбери одну карту (4 на выбор):" if not gm.chest_opened else "Карта добавлена в колоду!"
    h = sub_font.render(hint, True, _TEXT_COLOR)
    screen.blit(h, (960 - h.get_width() // 2, 160))

    if not gm.chest_opened and getattr(gm, "chest_gold", 0) > 0:
        g = sub_font.render(
            f"+ {gm.chest_gold} золота (при взятии карты)",
            True, _GOLD_COLOR
        )
        screen.blit(g, (960 - g.get_width() // 2, 200))

    draw_card_row(view, screen, cards, card_font, desc_font, cy=270)

    if not gm.chest_opened:
        draw_take_skip_buttons(view, screen, card_font)
    else:
        draw_continue_button(view, screen, card_font)


def clicks_locked(view, mouse_pos):
    gm      = view.gm
    has_key = getattr(gm, "player_keys", 0) > 0

    if not has_key and not gm.chest_opened:
        if pygame.Rect(760, 500, 400, 60).collidepoint(mouse_pos):
            gm.current_floor += 1
            gm.setup_next_floor()
        return

    if gm.chest_opened:
        if pygame.Rect(760, 700, 400, 60).collidepoint(mouse_pos):
            gm.current_floor += 1
            gm.setup_next_floor()
        return

    cards   = getattr(gm, "chest_cards", [])
    count   = len(cards)
    spacing = 220
    total_w = count * spacing
    start_x = 960 - total_w // 2 + spacing // 2 - CARD_W // 2

    for i in range(count):
        rect = pygame.Rect(start_x + i * spacing, 270, CARD_W, CARD_H)
        if rect.collidepoint(mouse_pos):
            gm.chest_selected = i
            return

    if pygame.Rect(760, 620, 200, 60).collidepoint(mouse_pos) and gm.chest_selected is not None:
        gm.add_card(gm.chest_cards[gm.chest_selected])
        gm.player_gold  += getattr(gm, "chest_gold", 0)
        gm.player_keys  -= 1
        gm.chest_opened  = True
        return

    if pygame.Rect(980, 620, 200, 60).collidepoint(mouse_pos):
        gm.current_floor += 1
        gm.setup_next_floor()