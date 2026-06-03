import pygame


class Campfire:
    """Экран Костра -- тёплая тема, стиль EventView."""
    sub_state        = "MAIN"
    is_rest_hovered  = False
    is_forge_hovered = False

    _BG_COLOR        = (15,  10,  10)
    _PANEL_COLOR     = (35,  20,  15)
    _BTN_COLOR       = (70,  40,  20)
    _BTN_HOVER_COLOR = (120, 70,  30)
    _BTN_BORDER      = (220, 140, 60)
    _TITLE_COLOR     = (255, 180, 60)
    _TEXT_COLOR      = (210, 200, 185)
    _HP_COLOR        = (100, 220, 100)

    @staticmethod
    def reset():
        Campfire.sub_state        = "MAIN"
        Campfire.is_rest_hovered  = False
        Campfire.is_forge_hovered = False

    @staticmethod
    def draw_screen(view):
        C         = Campfire
        screen    = view.screen
        W, H      = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(C._BG_COLOR)
        _hovered_card_data = None

        title_font = pygame.font.SysFont("Arial", 42, bold=True)
        text_font  = pygame.font.SysFont("Arial", 28)
        btn_font   = pygame.font.SysFont("Arial", 26, bold=True)
        small_font = pygame.font.SysFont("Arial", 18, bold=True)

        if Campfire.sub_state == "MAIN":
            # Центральная панель (компактная для главного экрана)
            panel = pygame.Rect(W // 2 - 480, 60, 960, 600)
            pygame.draw.rect(screen, C._PANEL_COLOR, panel, border_radius=16)
            pygame.draw.rect(screen, C._BTN_BORDER,  panel, 2, border_radius=16)

            title = title_font.render(
                f"ЭТАЖ {view.gm.current_floor}: У КОСТРА", True, C._TITLE_COLOR)
            screen.blit(title, (W // 2 - title.get_width() // 2, 110))

            hp_surf = text_font.render(
                f"Здоровье: {view.gm.player.hp} / {view.gm.player.max_hp}",
                True, C._HP_COLOR)
            screen.blit(hp_surf, (W // 2 - hp_surf.get_width() // 2, 185))

            view.btn_rest_rect = pygame.Rect(W // 2 - 300, 300, 600, 80)
            Campfire.is_rest_hovered = view.btn_rest_rect.collidepoint(mouse_pos)
            col = C._BTN_HOVER_COLOR if Campfire.is_rest_hovered else C._BTN_COLOR
            pygame.draw.rect(screen, col, view.btn_rest_rect, border_radius=12)
            pygame.draw.rect(screen, C._BTN_BORDER, view.btn_rest_rect, 2, border_radius=12)
            lbl = btn_font.render("ОТДОХНУТЬ  (+25 HP)", True, (255, 255, 255))
            screen.blit(lbl, (view.btn_rest_rect.centerx - lbl.get_width() // 2,
                               view.btn_rest_rect.centery - lbl.get_height() // 2))

            view.btn_forge_rect = pygame.Rect(W // 2 - 300, 420, 600, 80)
            Campfire.is_forge_hovered = view.btn_forge_rect.collidepoint(mouse_pos)
            col = C._BTN_HOVER_COLOR if Campfire.is_forge_hovered else C._BTN_COLOR
            pygame.draw.rect(screen, col, view.btn_forge_rect, border_radius=12)
            pygame.draw.rect(screen, C._BTN_BORDER, view.btn_forge_rect, 2, border_radius=12)
            lbl = btn_font.render("КУЗНИЦА  (Улучшить карту)", True, (255, 255, 255))
            screen.blit(lbl, (view.btn_forge_rect.centerx - lbl.get_width() // 2,
                               view.btn_forge_rect.centery - lbl.get_height() // 2))

        elif Campfire.sub_state == "FORGE":
            panel = pygame.Rect(40, 20, W - 80, H - 40)
            pygame.draw.rect(screen, C._PANEL_COLOR, panel, border_radius=16)
            pygame.draw.rect(screen, C._BTN_BORDER,  panel, 2, border_radius=16)

            title = title_font.render("КУЗНИЦА: ВЫБЕРИТЕ КАРТУ", True, C._TITLE_COLOR)
            screen.blit(title, (W // 2 - title.get_width() // 2, 45))

            hint = text_font.render(
                "Кликните по карте для улучшения  |  Колесо мыши -- прокрутка",
                True, C._TEXT_COLOR)
            screen.blit(hint, (W // 2 - hint.get_width() // 2, 110))

            cards_per_row = 7
            card_w    = view.card_width
            card_h    = view.card_height
            spacing_x = card_w + 24
            spacing_y = card_h + 36
            total_w   = cards_per_row * spacing_x - 24
            start_x   = W // 2 - total_w // 2
            start_y   = 165

            clip_rect = pygame.Rect(60, start_y, W - 120, H - start_y - 30)
            screen.set_clip(clip_rect)

            _hovered_card_data = None
            view.forge_card_rects = []

            for index, card in enumerate(view.gm.current_deck):
                row    = index // cards_per_row
                col    = index % cards_per_row
                card_x = start_x + col * spacing_x
                card_y = start_y + 10 + row * spacing_y - view.scroll_y
                card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
                view.forge_card_rects.append((card_rect, index))

                is_hov = card_rect.collidepoint(mouse_pos)
                if is_hov:
                    _hovered_card_data = (card, card_rect)
                draw_y = card_y - 10 if is_hov else card_y
                view.draw_card_by_data(card, card_x, draw_y)

                if card.upgraded:
                    lbl = small_font.render("[МАКС]", True, C._HP_COLOR)
                    screen.blit(lbl, (card_x + 8, draw_y + card_h - 26))

            screen.set_clip(None)

            # Тултип поверх clip -- последним
            if _hovered_card_data:
                card, rect = _hovered_card_data
                from ui.CardRenderer import CardRenderer
                CardRenderer.draw_card_keyword_tooltip(
                    screen, view.card_font, view.card_desc_font, card, rect
                )

    @staticmethod
    def handle_clicks(view, mouse_pos):
        if Campfire.sub_state == "MAIN":
            if hasattr(view, 'btn_rest_rect') and view.btn_rest_rect.collidepoint(mouse_pos):
                view.gm.player.hp = min(view.gm.player.hp + 25, view.gm.player.max_hp)
                view.gm.current_floor += 1
                view.gm.setup_next_floor()

            elif hasattr(view, 'btn_forge_rect') and view.btn_forge_rect.collidepoint(mouse_pos):
                view.scroll_y = 0
                Campfire.sub_state = "FORGE"

        elif Campfire.sub_state == "FORGE":
            if hasattr(view, 'forge_card_rects'):
                for card_rect, index in view.forge_card_rects:
                    if card_rect.collidepoint(mouse_pos):
                        card = view.gm.current_deck[index]
                        if not card.upgraded:
                            card.upgrade()
                            Campfire.sub_state = "MAIN"
                            view.gm.current_floor += 1
                            view.gm.setup_next_floor()
                        break