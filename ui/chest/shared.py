import pygame


# ─── Цвета (импортируются из base через параметры, либо дублируем минимум) ───
_BTN_COLOR   = (40,  40,  60)
_BTN_HOVER   = (70,  70, 100)
_BTN_BORDER  = (255, 255, 255)
_SKIP_COLOR  = (120, 120, 140)

CARD_W = 180
CARD_H = 250


def draw_card_row(view, screen, cards, card_font, desc_font, cy=300):
    from ui.CardRenderer import CardRenderer
    gm      = view.gm
    count   = len(cards)
    if count == 0:
        return
    spacing = 220
    total_w = count * spacing
    start_x = 960 - total_w // 2 + spacing // 2 - CARD_W // 2
    mouse   = pygame.mouse.get_pos()

    for i, card in enumerate(cards):
        cx   = start_x + i * spacing
        rect = pygame.Rect(cx, cy, CARD_W, CARD_H)
        is_hovered  = rect.collidepoint(mouse) if not gm.chest_opened else False
        is_selected = (gm.chest_selected == i)

        if not gm.chest_opened and is_selected:
            pygame.draw.rect(
                screen, (255, 220, 50),
                pygame.Rect(cx - 4, cy - 4, CARD_W + 8, CARD_H + 8), 3
            )
        CardRenderer.draw(
            screen, card, cx, cy,
            card_font, desc_font,
            is_hovered,
            player=gm.player,
            enemy=None,
        )


def draw_take_skip_buttons(view, screen, card_font):
    gm    = view.gm
    mouse = pygame.mouse.get_pos()

    take_rect = pygame.Rect(760, 620, 200, 60)
    can_take  = gm.chest_selected is not None
    take_col  = _BTN_HOVER if (take_rect.collidepoint(mouse) and can_take) else _BTN_COLOR
    take_brd  = (100, 220, 100) if can_take else (80, 80, 80)
    pygame.draw.rect(screen, take_col,  take_rect)
    pygame.draw.rect(screen, take_brd,  take_rect, 2)
    lbl = card_font.render(
        "Взять", True,
        (200, 255, 200) if can_take else (100, 100, 100)
    )
    screen.blit(lbl, (take_rect.centerx - lbl.get_width() // 2,
                      take_rect.centery - lbl.get_height() // 2))

    skip_rect = pygame.Rect(980, 620, 200, 60)
    skip_col  = _BTN_HOVER if skip_rect.collidepoint(mouse) else _BTN_COLOR
    pygame.draw.rect(screen, skip_col,   skip_rect)
    pygame.draw.rect(screen, _SKIP_COLOR, skip_rect, 2)
    slbl = card_font.render("Пропустить", True, _SKIP_COLOR)
    screen.blit(slbl, (skip_rect.centerx - slbl.get_width() // 2,
                       skip_rect.centery - slbl.get_height() // 2))


def draw_leave_button(view, screen, card_font, y=500):
    mouse = pygame.mouse.get_pos()
    btn   = pygame.Rect(760, y, 400, 60)
    col   = _BTN_HOVER if btn.collidepoint(mouse) else _BTN_COLOR
    pygame.draw.rect(screen, col,        btn)
    pygame.draw.rect(screen, _SKIP_COLOR, btn, 2)
    lbl = card_font.render("Уйти", True, _SKIP_COLOR)
    screen.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                      btn.centery - lbl.get_height() // 2))


def draw_continue_button(view, screen, font):
    mouse = pygame.mouse.get_pos()
    btn   = pygame.Rect(760, 700, 400, 60)
    col   = _BTN_HOVER if btn.collidepoint(mouse) else _BTN_COLOR
    pygame.draw.rect(screen, col,       btn)
    pygame.draw.rect(screen, _BTN_BORDER, btn, 2)
    lbl = font.render("Продолжить ->", True, (255, 255, 255))
    screen.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                      btn.centery - lbl.get_height() // 2))