import pygame
import random
from ui.Chest import Chest
from ui.Shop import Shop
from ui.Campfire import Campfire


class InputHandler:
    """Изолированный обработчик мыши и ввода. Никакого визуала, только хитбоксы."""

    @staticmethod
    def process_mouse_clicks(view, mouse_pos):
        """Разбирает клики левой кнопкой мыши в зависимости от экрана."""

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

        # 2. КОСТЁР
        elif view.gm.current_state == "CAMPFIRE":
            Campfire.handle_clicks(view, mouse_pos)

        # 3. МАГАЗИН
        elif view.gm.current_state == "SHOP":
            Shop.handle_clicks(view, mouse_pos)

        # 4. СУНДУК
        elif view.gm.current_state == "CHEST":
            Chest.handle_clicks(view, mouse_pos)

        # 5. СОБЫТИЕ
        elif view.gm.current_state == "EVENT":
            from ui.EventView import handle_clicks as event_clicks
            event_clicks(view, mouse_pos)

        # 6. ЛИДЕРБОРД
        elif view.gm.current_state == "LEADERBOARD":
            from ui.LeaderboardView import LeaderboardView
            from ui.MainMenu import MainMenu
            from ui.EventView import reset as event_reset
            from managers.GameManager import GameManager

            # БАГ 1: handle_clicks теперь только возвращает True/False
            if LeaderboardView.handle_clicks(view, mouse_pos):
                # БАГ 3: сбрасываем ВСЕ статические состояния в одном месте
                Shop.reset()
                Campfire.reset()
                MainMenu.reset()
                event_reset()
                view.gm = GameManager()
                view.gm.current_state = "MAIN_MENU"
                print("[СИСТЕМА] Рестарт завершён. Возврат в главное меню.")

    @staticmethod
    def process_scroll(view, event_button):
        """Разбирает вращение колесика мыши для прокрутки колод."""
        if view.gm.current_state in ["CAMPFIRE", "SHOP"]:
            if event_button == 4:
                view.scroll_y = max(view.scroll_y - 30, 0)
            elif event_button == 5:
                view.scroll_y = min(view.scroll_y + 30, 600)