import pygame


class Campfire:
    """Графический экран Костра под Full HD с просторной сеткой и ховером в Кузнице."""
    sub_state        = "MAIN"
    is_rest_hovered  = False
    is_forge_hovered = False

    @staticmethod
    def reset():
        """Сбрасывает состояние костра. Вызывать при старте нового забега."""
        Campfire.sub_state        = "MAIN"
        Campfire.is_rest_hovered  = False
        Campfire.is_forge_hovered = False

    @staticmethod
    def draw_screen(view):
        WHITE  = (255, 255, 255)
        GREEN  = (70, 240, 70)
        YELLOW = (240, 240, 70)

        view.screen.fill((25, 20, 20))
        mouse_pos = pygame.mouse.get_pos()

        if Campfire.sub_state == "MAIN":
            view.draw_text(f"=== ЭТАЖ {view.gm.current_floor}: У УЮТНОГО КОСТРА ===",
                           view.main_font, WHITE, 100, 100)
            view.draw_text(f"Ваше здоровье: {view.gm.player.hp}/{view.gm.player.max_hp}",
                           view.main_font, GREEN, 100, 160)

            view.btn_rest_rect = pygame.Rect(100, 300, 450, 80)
            Campfire.is_rest_hovered = view.btn_rest_rect.collidepoint(mouse_pos)
            rest_btn_color = (90, 90, 95) if Campfire.is_rest_hovered else (60, 60, 60)
            pygame.draw.rect(view.screen, rest_btn_color, view.btn_rest_rect)
            pygame.draw.rect(view.screen, WHITE, view.btn_rest_rect, 2)
            view.draw_text("1. ОТДОХНУТЬ (+25 HP)", view.card_font, WHITE, 140, 325)

            view.btn_forge_rect = pygame.Rect(100, 420, 450, 80)
            Campfire.is_forge_hovered = view.btn_forge_rect.collidepoint(mouse_pos)
            forge_btn_color = (90, 90, 95) if Campfire.is_forge_hovered else (60, 60, 60)
            pygame.draw.rect(view.screen, forge_btn_color, view.btn_forge_rect)
            pygame.draw.rect(view.screen, WHITE, view.btn_forge_rect, 2)
            view.draw_text("2. КУЗНИЦА (Улучшить карту)", view.card_font, WHITE, 140, 445)

        elif Campfire.sub_state == "FORGE":
            view.draw_text("=== КУЗНИЦА: ВЫБЕРИТЕ КАРТУ ДЛЯ УЛУЧШЕНИЯ ===",
                           view.main_font, YELLOW, 100, 50)
            view.draw_text("Крутите колесико мыши для прокрутки колоды:",
                           view.ui_font, WHITE, 100, 95)

            clip_rect = pygame.Rect(50, 150, 1820, 850)
            view.screen.set_clip(clip_rect)

            view.forge_card_rects = []
            cards_per_row = 4

            for index, card in enumerate(view.gm.current_deck):
                row = index // cards_per_row
                col = index % cards_per_row
                card_x = 100 + col * 220
                card_y = 170 + row * 280 - view.scroll_y
                card_rect = pygame.Rect(card_x, card_y, view.card_width, view.card_height)
                view.forge_card_rects.append((card_rect, index))

                is_card_hovered = card_rect.collidepoint(mouse_pos)
                draw_y = card_y - 10 if is_card_hovered else card_y
                view.draw_card_by_data(card, card_x, draw_y)

                if card.upgraded:
                    view.draw_text("[МАКС]", view.card_desc_font, GREEN,
                                   card_rect.x + 15, draw_y + view.card_height - 35)

            view.screen.set_clip(None)

    @staticmethod
    def handle_clicks(view, mouse_pos):
        if Campfire.sub_state == "MAIN":
            if hasattr(view, 'btn_rest_rect') and view.btn_rest_rect.collidepoint(mouse_pos):
                view.gm.player.hp = min(view.gm.player.hp + 25, view.gm.player.max_hp)
                print("Вы отлично отдохнули у костра!")
                Campfire.sub_state = "MAIN"
                view.gm.current_floor += 1
                view.gm.setup_next_floor()

            elif hasattr(view, 'btn_forge_rect') and view.btn_forge_rect.collidepoint(mouse_pos):
                view.scroll_y = 0
                Campfire.sub_state = "FORGE"

        elif Campfire.sub_state == "FORGE":
            if hasattr(view, 'forge_card_rects'):
                for card_rect, index in view.forge_card_rects:
                    if card_rect.collidepoint(mouse_pos):
                        selected_card = view.gm.current_deck[index]
                        if not selected_card.upgraded:
                            selected_card.upgrade()
                            print(f"Карта {selected_card.name} улучшена!")
                            Campfire.sub_state = "MAIN"
                            view.gm.current_floor += 1
                            view.gm.setup_next_floor()
                            break