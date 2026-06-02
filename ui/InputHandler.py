import pygame
import random
from ui.Chest import Chest
from ui.Shop import Shop
from ui.Campfire import Campfire


def _handle_combat(view, mouse_pos):
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
        card_rect = pygame.Rect(
            card_x, view.base_y, view.card_width, view.card_height
        )
        if card_rect.collidepoint(mouse_pos):
            view.gm.active_combat.play_card_by_index(index)
            break


def _handle_campfire(view, mouse_pos):
    Campfire.handle_clicks(view, mouse_pos)


def _handle_shop(view, mouse_pos):
    Shop.handle_clicks(view, mouse_pos)


def _handle_chest(view, mouse_pos):
    Chest.handle_clicks(view, mouse_pos)


def _handle_event(view, mouse_pos):
    from ui.EventView import handle_clicks as event_clicks
    event_clicks(view, mouse_pos)


def _handle_leaderboard(view, mouse_pos):
    from ui.LeaderboardView import LeaderboardView
    from ui.MainMenu import MainMenu
    from ui.EventView import reset as event_reset
    from managers.GameManager import GameManager

    if LeaderboardView.handle_clicks(view, mouse_pos):
        Shop.reset()
        Campfire.reset()
        MainMenu.reset()
        event_reset()
        view.gm = GameManager()
        view.gm.current_state = "MAIN_MENU"
        print("[СИСТЕМА] Рестарт завершён. Возврат в главное меню.")


# Диспетчер: состояние -> обработчик.
# Добавить новый экран = одна строка здесь.
STATE_HANDLERS = {
    "COMBAT":      _handle_combat,
    "CAMPFIRE":    _handle_campfire,
    "SHOP":        _handle_shop,
    "CHEST":       _handle_chest,
    "EVENT":       _handle_event,
    "LEADERBOARD": _handle_leaderboard,
}


class InputHandler:
    """Изолированный обработчик мыши и ввода. Никакого визуала, только хитбоксы."""

    @staticmethod
    def process_mouse_clicks(view, mouse_pos):
        handler = STATE_HANDLERS.get(view.gm.current_state)
        if handler:
            handler(view, mouse_pos)

    @staticmethod
    def process_scroll(view, event_button):
        if view.gm.current_state in ["CAMPFIRE", "SHOP"]:
            if event_button == 4:
                view.scroll_y = max(view.scroll_y - 30, 0)
            elif event_button == 5:
                view.scroll_y = min(view.scroll_y + 30, 600)