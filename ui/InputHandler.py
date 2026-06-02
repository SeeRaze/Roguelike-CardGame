import pygame
import random

class InputHandler:
    """Изолированный обработчик мыши и ввода. Никакого визуала, только хитбоксы."""
    
    @staticmethod
    def process_mouse_clicks(view, mouse_pos):
        """Разбирает клики левой кнопкой мыши в зависимости от экрана"""
        
        # 1. ОБРАБОТКА КЛИКОВ В БОЮ
        if view.gm.current_state == "COMBAT":
            # Если враг мертв, клик переключает этаж
            if view.gm.active_combat.enemy.hp <= 0:
                view.gm.distribute_combat_rewards()
                view.gm.current_floor += 1
                view.scroll_y = 0
                view.gm.setup_next_floor()
                return

            # Конец хода
            if view.end_turn_rect.collidepoint(mouse_pos):
                view.gm.active_combat.end_turn_phase()
                return

            # Клики по картам в живой руке
            hand_size = len(view.gm.active_combat.deck_manager.hand)
            for index in range(hand_size):
                card_x = view.calculate_card_x(index, hand_size)
                card_rect = pygame.Rect(card_x, view.base_y, view.card_width, view.card_height)
                if card_rect.collidepoint(mouse_pos):
                    view.gm.active_combat.play_card_by_index(index)
                    break
        # --- ОБРАБОТКА КЛИКОВ НА ЭКРАНЕ КАРТЫ (ЧИСТЫЙ РАЗДЕЛЬНЫЙ ВЫБОР) ---
        elif view.gm.current_state == "MAP":
            local_step = (view.gm.current_floor - 1) % 10 + 1
            current_options = view.gm.procedural_map[local_step - 1]
            
            # Извлекаем чистые строки типов комнат из списков
            room_left = current_options[0][0] if isinstance(current_options[0], list) else current_options[0]
            room_right = current_options[1][0] if isinstance(current_options[1], list) else current_options[1]
            
            # Клик по Ветви А (левая кнопка ведет в левую комнату)
            if hasattr(view, 'btn_branch_left') and view.btn_branch_left.collidepoint(mouse_pos):
                print(f"Игрок выбрал левый путь: {room_left}")
                view.gm.enter_chosen_room(room_left)
                return
                
            # Клик по Ветви Б (правая кнопка ведет в правую комнату)
            elif hasattr(view, 'btn_branch_right') and view.btn_branch_right.collidepoint(mouse_pos):
                print(f"Игрок выбрал правый путь: {room_right}")
                view.gm.enter_chosen_room(room_right)
                return
            elif view.gm.current_state == "LEADERBOARD":
                # Проверяем клик по кнопке, которую ты только что добавил в GameView
                if view.btn_back_leaderboard.collidepoint(mouse_pos):
                    print("[СИСТЕМА] Нажата кнопка возврата. Перезапускаем менеджер игры...")
            
            # Полностью обновляем мозг игры, чтобы сбросить старые ХП и этажи для новой катки
                    from managers.GameManager import GameManager
                    view.gm = GameManager() 
                    view.gm.current_state = "MAIN_MENU"

                    
        # 2. КЛИКИ НА ЭКРАНЕ КОСТРА
        elif view.gm.current_state == "CAMPFIRE":
            # Импортируем локально, чтобы избежать кольцевых связей
            from ui.Campfire import Campfire
            Campfire.handle_clicks(view, mouse_pos)
                
        # 3. КЛИКИ НА ЭКРАНЕ МАГАЗИНА
        elif view.gm.current_state == "SHOP":
            from ui.Shop import Shop
            Shop.handle_clicks(view, mouse_pos)
        elif view.gm.current_state == "LEADERBOARD":
            from ui.LeaderboardView import LeaderboardView
            LeaderboardView.handle_clicks(view, mouse_pos)

    @staticmethod
    def process_scroll(view, event_button):
        """Разбирает вращение колесика мыши для прокрутки колод"""
        if view.gm.current_state in ["CAMPFIRE", "SHOP"]:
            if event_button == 4:    # Колесико вверх
                view.scroll_y = max(view.scroll_y - 30, 0)
            elif event_button == 5:  # Колесико вниз
                view.scroll_y = min(view.scroll_y + 30, 600)
