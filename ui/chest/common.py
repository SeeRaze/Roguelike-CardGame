import pygame
from ui.chest.shared import draw_card_row, draw_take_skip_buttons, draw_continue_button

CARD_W = 180
CARD_H = 250

_TEXT_COLOR = (200, 200, 200)


def draw_common(view, screen, sub_font, card_font, desc_font, small_font):
    gm    = view.gm
    cards = getattr(gm, "chest_cards", [])

    hint = "Выбери одну карту:" if not gm.chest_opened else "Карта добавлена в колоду!"
    h = sub_font.render(hint, True, _TEXT_COLOR)
    screen.blit(h, (960 - h.get_width() // 2, 130))

    draw_card_row(view, screen, cards, card_font, desc_font, cy=300)

    if not gm.chest_opened:
        draw_take_skip_buttons(view, screen, card_font)
    else:
        draw_continue_button(view, screen, card_font)


def clicks_common(view, mouse_pos):
    gm = view.gm

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
        rect = pygame.Rect(start_x + i * spacing, 300, CARD_W, CARD_H)
        if rect.collidepoint(mouse_pos):
            gm.chest_selected = i
            return

    if pygame.Rect(760, 620, 200, 60).collidepoint(mouse_pos) \
            and gm.chest_selected is not None:
        gm.add_card(gm.chest_cards[gm.chest_selected])
        gm.chest_opened = True
        # Хук on_chest_opened — реликвии реагируют на открытие сундука
        for relic in gm.relics:
            relic.on_chest_opened("common", gm)
        return

    if pygame.Rect(980, 620, 200, 60).collidepoint(mouse_pos):
        gm.current_floor += 1
        gm.setup_next_floor()