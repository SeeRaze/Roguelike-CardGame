import pygame
import random
from ui.Chest import Chest
from ui.Shop import Shop      # <-- ДОБАВЛЕНО
from ui.Campfire import Campfire  # <-- ДОБАВЛЕНО (для баг #6 -- reset там же)


class InputHandler:
    """Изолированный обработчик мыши и ввода. Никакого визуала, только хитбоксы."""

    @staticmethod
    def process_mouse_clicks(view, mouse_pos):
        """Разбирает клики левой кнопкой мыши в зависимости от экрана"""

        # 1. БОЙ
        if view.gm.current_state == "COMBAT":
            if view.gm.active_combat.enemy.hp <= 0:
                view.gm.distribute_combat_rewards()
                view.gm.current_floor += 1
                view.scroll_y = 0
                view.gm.setup_next_floor()
                return

            if view.end_turn_rect.collidepoint(mouse_pos):
                view.gm.active_combat.end_turn_phase()
                return

            hand_size = len(view.gm.active_combat.deck_manager.hand)
            for index in range(hand_size):
                card_x = view.calculate_card_x(index, hand_size)
                card_rect = pygame.Rect(card_x, view.base_y, view.card_width, view.card_height)
                if card_rect.collidepoint(mouse_pos):
                    view.gm.active_combat.play_card_by_index(index)
                    break

        # 2. КАРТА (legacy, MapView.handle_click перехватывает раньше)
        elif view.gm.current_state == "MAP":
            local_step = (view.gm.current_floor - 1) % 10 + 1
            current_options = view.gm.procedural_map[local_step - 1]

            room_left  = current_options[0][0] if isinstance(current_options[0], list) else current_options[0]
            room_right = current_options[1][0] if isinstance(current_options[1], list) else current_options[1]

            if hasattr(view, 'btn_branch_left') and view.btn_branch_left.collidepoint(mouse_pos):
                view.gm.enter_chosen_room(room_left)
                return
            elif hasattr(view, 'btn_branch_right') and view.btn_branch_right.collidepoint(mouse_pos):
                view.gm.enter_chosen_room(room_right)
                return

        # 3. КОСТЁР
        elif view.gm.current_state == "CAMPFIRE":
            Campfire.handle_clicks(view, mouse_pos)

        # 4. МАГАЗИН
        elif view.gm.current_state == "SHOP":
            Shop.handle_clicks(view, mouse_pos)

        # 5. СУНДУК
        elif view.gm.current_state == "CHEST":
            Chest.handle_clicks(view, mouse_pos)

        # 6. ЛИДЕРБОРД
        elif view.gm.current_state == "LEADERBOARD":
            from ui.LeaderboardView import LeaderboardView
            LeaderboardView.handle_clicks(view, mouse_pos)
            if view.btn_back_leaderboard.collidepoint(mouse_pos):
                from managers.GameManager import GameManager
                Shop.reset()      # <-- ДОБАВЛЕНО: сброс магазина при новом забеге
                Campfire.reset()  # <-- ДОБАВЛЕНО: сброс костра при новом забеге
                view.gm = GameManager()
                view.gm.current_state = "MAIN_MENU"

    @staticmethod
    def process_scroll(view, event_button):
        """Разбирает вращение колесика мыши для прокрутки колод"""
        if view.gm.current_state in ["CAMPFIRE", "SHOP"]:
            if event_button == 4:
                view.scroll_y = max(view.scroll_y - 30, 0)
            elif event_button == 5:
                view.scroll_y = min(view.scroll_y + 30, 600)