import pygame
import sys
from ui.HubView import HubView

class MainMenu:
    """Главное меню и делегирование в HubView."""

    is_play_hovered = False
    is_exit_hovered = False

    _hub: HubView = None

    @classmethod
    def get_hub(cls) -> HubView:
        if cls._hub is None:
            cls._hub = HubView()
        return cls._hub

    @classmethod
    def reset(cls):
        """БАГ 1: сбрасывает синглтон HubView при рестарте забега."""
        cls._hub = None

    @staticmethod
    def draw_menu(view):
        view.screen.fill((15, 15, 20))
        mouse_pos = pygame.mouse.get_pos()

        view.draw_text("ROGUELIKE CARD GAME", view.main_font,
                       (240, 240, 70), 100, 200)
        view.draw_text("Pre-Alpha Edition v0.3", view.card_desc_font,
                       (150, 150, 150), 100, 250)

        view.btn_menu_play = pygame.Rect(100, 350, 350, 70)
        MainMenu.is_play_hovered = view.btn_menu_play.collidepoint(mouse_pos)
        play_color = (90, 90, 95) if MainMenu.is_play_hovered else (60, 60, 60)
        pygame.draw.rect(view.screen, play_color, view.btn_menu_play)
        pygame.draw.rect(view.screen, (255, 255, 255), view.btn_menu_play, 2)
        view.draw_text("ВОЙТИ В ЛАГЕРЬ", view.card_font,
                       (255, 255, 255), 170, 372)

        view.btn_menu_exit = pygame.Rect(100, 450, 350, 70)
        MainMenu.is_exit_hovered = view.btn_menu_exit.collidepoint(mouse_pos)
        exit_color = (90, 60, 60) if MainMenu.is_exit_hovered else (60, 40, 40)
        pygame.draw.rect(view.screen, exit_color, view.btn_menu_exit)
        pygame.draw.rect(view.screen, (255, 255, 255), view.btn_menu_exit, 2)
        view.draw_text("ВЫХОД", view.card_font, (255, 255, 255), 230, 472)

    @staticmethod
    def draw_hub(view):
        MainMenu.get_hub().draw(view)

    @staticmethod
    def handle_clicks(view, mouse_pos):
        if view.gm.current_state == "MAIN_MENU":
            if hasattr(view, 'btn_menu_play') and view.btn_menu_play.collidepoint(mouse_pos):
                view.gm.current_state = "HUB"
            elif hasattr(view, 'btn_menu_exit') and view.btn_menu_exit.collidepoint(mouse_pos):
                pygame.quit()
                sys.exit()

        elif view.gm.current_state == "HUB":
            MainMenu.get_hub().handle_click(view, mouse_pos)