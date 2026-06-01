import pygame
import random
from core.Card import create_strike, create_defend, create_splash, create_ignite, create_bash, create_neutralize

class Shop:
    """Графический экран Магазина Торговца под Full HD с ховерами и просторной сеткой."""
    sub_state = "MAIN"
    item_1 = None
    item_2 = None
    card_price = 40
    showcase_generated = False
    
    is_remove_hovered = False
    is_leave_hovered = False

    @staticmethod
    def generate_showcase():
        """Генерирует две уникальные случайные карты для витрины"""
        all_cards_pool = [create_strike, create_defend, create_splash, create_ignite, create_bash, create_neutralize]
        
        # Получаем список из двух случайных ФУНКЦИЙ-генераторов
        showcase_classes = random.sample(all_cards_pool, 2)
        
        # ИСПРАВЛЕНИЕ: Сначала достаем функцию из списка по индексу, а уже ПОТОМ вызываем её скобками ()!
        Shop.item_1 = showcase_classes[0]()
        Shop.item_2 = showcase_classes[1]()
        Shop.showcase_generated = True

    @staticmethod
    def draw_screen(view):
        WHITE = (255, 255, 255)
        YELLOW = (240, 240, 70)
        GRAY = (150, 150, 150)
        RED = (240, 70, 70)
        
        view.screen.fill((20, 20, 25))  # Холодный фон лавки
        mouse_pos = pygame.mouse.get_pos()
        
        if not Shop.showcase_generated:
            Shop.generate_showcase()
            
        # ==============================================================
        # 1. ГЛАВНАЯ ВИТРИНА МАГАЗИНА
        # ==============================================================
        if Shop.sub_state == "MAIN":
            view.draw_text(f"=== ЭТАЖ {view.gm.current_floor}: ЛАВКА ТОРГОВЦА ===", view.main_font, WHITE, 100, 50)
            view.draw_text(f"Ваше золото: {view.gm.player_gold} монет", view.main_font, YELLOW, 100, 100)
            view.draw_text("Кликните по карте, чтобы купить её:", view.ui_font, GRAY, 100, 150)
            
            # --- ТОВАР №1 (С ХОВЕРОМ!) ---
            view.shop_item_1_rect = pygame.Rect(100, 220, view.card_width, view.card_height)
            if Shop.item_1:
                is_item1_hovered = view.shop_item_1_rect.collidepoint(mouse_pos)
                draw_y1 = view.shop_item_1_rect.y - 20 if is_item1_hovered else view.shop_item_1_rect.y
                view.draw_card_by_data(Shop.item_1, view.shop_item_1_rect.x, draw_y1)
                view.draw_text(f"{Shop.card_price} з.", view.card_font, YELLOW, view.shop_item_1_rect.x + 55, draw_y1 + view.card_height - 35)
            else:
                pygame.draw.rect(view.screen, (30, 30, 35), view.shop_item_1_rect)
                view.draw_text("[ПРОДАНО]", view.card_font, GRAY, view.shop_item_1_rect.x + 35, view.shop_item_1_rect.y + 110)

            # --- ТОВАР №2 (С ХОВЕРОМ!) ---
            view.shop_item_2_rect = pygame.Rect(320, 220, view.card_width, view.card_height)
            if Shop.item_2:
                is_item2_hovered = view.shop_item_2_rect.collidepoint(mouse_pos)
                draw_y2 = view.shop_item_2_rect.y - 20 if is_item2_hovered else view.shop_item_2_rect.y
                view.draw_card_by_data(Shop.item_2, view.shop_item_2_rect.x, draw_y2)
                view.draw_text(f"{Shop.card_price} з.", view.card_font, YELLOW, view.shop_item_2_rect.x + 55, draw_y2 + view.card_height - 35)
            else:
                pygame.draw.rect(view.screen, (30, 30, 35), view.shop_item_2_rect)
                view.draw_text("[ПРОДАНО]", view.card_font, GRAY, view.shop_item_2_rect.x + 35, view.shop_item_2_rect.y + 110)

            # Кнопка сжигания
            view.btn_shop_remove_rect = pygame.Rect(100, 520, 400, 70)
            Shop.is_remove_hovered = view.btn_shop_remove_rect.collidepoint(mouse_pos)
            remove_btn_color = (90, 90, 95) if Shop.is_remove_hovered else (60, 60, 60)
            pygame.draw.rect(view.screen, remove_btn_color, view.btn_shop_remove_rect)
            pygame.draw.rect(view.screen, WHITE, view.btn_shop_remove_rect, 2)
            view.draw_text(f"СЖЕЧЬ КАРТУ (Цена: {view.gm.removal_price} з.)", view.card_font, RED, view.btn_shop_remove_rect.x + 25, view.btn_shop_remove_rect.y + 22)

            # Кнопка выхода
            view.btn_shop_leave_rect = pygame.Rect(100, 610, 400, 70)
            Shop.is_leave_hovered = view.btn_shop_leave_rect.collidepoint(mouse_pos)
            leave_btn_color = (65, 65, 70) if Shop.is_leave_hovered else (40, 40, 45)
            pygame.draw.rect(view.screen, leave_btn_color, view.btn_shop_leave_rect)
            pygame.draw.rect(view.screen, WHITE, view.btn_shop_leave_rect, 2)
            view.draw_text("ПОКИНУТЬ МАГАЗИН", view.card_font, WHITE, view.btn_shop_leave_rect.x + 100, view.btn_shop_leave_rect.y + 22)

        # ==============================================================
        # 2. ЭКРАН УТИЛИЗАЦИИ КАРТ (ПРОСТОРНАЯ FULL HD СЕТКА)
        # ==============================================================
        elif Shop.sub_state == "REMOVE":
            view.draw_text("=== УТИЛИЗАЦИЯ: ВЫБЕРИТЕ КАРТУ ДЛЯ УНИЧТОЖЕНИЯ ===", view.main_font, RED, 100, 50)
            view.draw_text("Крутите колесико мыши для прокрутки колоды Торговца:", view.ui_font, WHITE, 100, 95)
            
            clip_rect = pygame.Rect(50, 150, 1820, 850)
            view.screen.set_clip(clip_rect)
            
            view.shop_remove_card_rects = []
            cards_per_row = 4
            
            for index, card in enumerate(view.gm.current_deck):
                row = index // cards_per_row
                col = index % cards_per_row
                
                # Применяем просторную Full HD сетку, как на костре!
                card_x = 100 + col * 220
                card_y = 170 + row * 280 - view.scroll_y
                
                card_rect = pygame.Rect(card_x, card_y, view.card_width, view.card_height)
                view.shop_remove_card_rects.append((card_rect, index))
                
                # Ховер-эффект в утилизаторе Торговца
                is_card_hovered = card_rect.collidepoint(mouse_pos)
                draw_y = card_y - 10 if is_card_hovered else card_y
                
                view.draw_card_by_data(card, card_x, draw_y)
                
            view.screen.set_clip(None)

    @staticmethod
    def handle_clicks(view, mouse_pos):
        if Shop.sub_state == "MAIN":
            if Shop.item_1 and hasattr(view, 'shop_item_1_rect') and view.shop_item_1_rect.collidepoint(mouse_pos):
                if view.gm.player_gold >= Shop.card_price:
                    view.gm.player_gold -= Shop.card_price
                    view.gm.current_deck.append(Shop.item_1)
                    print(f"Куплена карта: {Shop.item_1.name}")
                    Shop.item_1 = None
                else: print("[!] Не хватает золота!")

            elif Shop.item_2 and hasattr(view, 'shop_item_2_rect') and view.shop_item_2_rect.collidepoint(mouse_pos):
                if view.gm.player_gold >= Shop.card_price:
                    view.gm.player_gold -= Shop.card_price
                    view.gm.current_deck.append(Shop.item_2)
                    print(f"Куплена карта: {Shop.item_2.name}")
                    Shop.item_2 = None
                else: print("[!] Не хватает золота!")

            elif hasattr(view, 'btn_shop_remove_rect') and view.btn_shop_remove_rect.collidepoint(mouse_pos):
                if view.gm.player_gold >= view.gm.removal_price:
                    view.scroll_y = 0
                    Shop.sub_state = "REMOVE"
                else: print("[!] Не хватает золота на чистку колоды!")

            elif hasattr(view, 'btn_shop_leave_rect') and view.btn_shop_leave_rect.collidepoint(mouse_pos):
                Shop.item_1 = None
                Shop.item_2 = None
                Shop.showcase_generated = False
                view.gm.current_floor += 1
                view.gm.setup_next_floor()

        elif Shop.sub_state == "REMOVE":
            if hasattr(view, 'shop_remove_card_rects'):
                for card_rect, index in view.shop_remove_card_rects:
                    if card_rect.collidepoint(mouse_pos):
                        removed = view.gm.current_deck.pop(index)
                        print(f"Карта {removed.name} сожжена!")
                        view.gm.player_gold -= view.gm.removal_price
                        view.gm.removal_price += 25
                        Shop.sub_state = "MAIN"
                        break
