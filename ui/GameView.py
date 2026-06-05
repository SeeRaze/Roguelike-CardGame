import pygame
import sys
import random as _rnd
from managers.GameManager import GameManager
from ui.MainMenu import MainMenu
from ui.InputHandler import InputHandler
from ui.MapView import MapView
from ui.cards import CardRenderer
from ui.hover_state import HoverState
from ui.draw_dispatchers import DRAW_HANDLERS
from ui.combat.hover import update_combat_hover


class GameView:
    """Системный движок, переведённый на Full HD (1920x1080)."""

    def __init__(self):
        pygame.init()

        self.screen_width  = 1920
        self.screen_height = 1080
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height)
        )
        pygame.display.set_caption("Roguelike Card Game - FULL HD EDITION")

        self.clock      = pygame.time.Clock()
        self.fps        = 60
        self.is_running = True

        self.main_font      = pygame.font.SysFont("Arial", 24, bold=True)
        self.ui_font        = pygame.font.SysFont("Courier New", 24)
        self.card_font      = pygame.font.SysFont("Arial", 18, bold=True)
        self.card_desc_font = pygame.font.SysFont("Arial", 16)

        self.scroll_y    = 0
        self.base_y      = 760
        self.card_width  = 180
        self.card_height = 250

        self.end_turn_rect = pygame.Rect(1680, 900, 220, 52)
        self.btn_back_leaderboard = pygame.Rect(760, 900, 400, 70)

        # Стопки карт (добор слева, сброс справа)
        self.draw_pile_rect    = pygame.Rect(60,  820, 120, 160)
        self.discard_pile_rect = pygame.Rect(1740, 820, 120, 160)

        # Кеш перемешанного порядка добора для отображения в тултипе
        self._draw_pile_display: list = []
        self._draw_pile_ids:     list = []

        # Все hover-данные в одном объекте
        self.hover = HoverState()

        # Бейджи статусов и реликвии (заполняются CombatHUD)
        self.enemy_badge_rects  = []
        self.player_badge_rects = []
        self.relic_rects        = []

        self.gm = GameManager()
        self.gm.start_game()

    def _refresh_draw_pile_display(self, draw_pile):
        """
        Пересчитывает перемешанную копию добора для тултипа.
        Вызывается только когда состав стопки изменился.
        Настоящий порядок draw_pile не трогает.
        """
        self._draw_pile_display = draw_pile.copy()
        _rnd.shuffle(self._draw_pile_display)
        self._draw_pile_ids = [id(c) for c in draw_pile]

    def run(self):
        while self.is_running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.fps)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hover.end_turn = self.end_turn_rect.collidepoint(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.gm.current_state in ["MAIN_MENU", "HUB"]:
                        MainMenu.handle_clicks(self, mouse_pos)
                        continue
                    if self.gm.current_state == "MAP":
                        MapView.handle_click(self, mouse_pos)
                        continue
                    InputHandler.process_mouse_clicks(self, event.pos)

                elif event.button in [4, 5]:
                    InputHandler.process_scroll(self, event.button)

    def calculate_card_x(self, index, total_cards):
        card_step = 200
        total_width = total_cards * card_step
        max_allowed_width = self.screen_width - 400
        if total_width > max_allowed_width:
            card_step = max_allowed_width / total_cards
            total_width = max_allowed_width
        start_x = (self.screen_width - total_width) / 2
        return int(start_x + index * card_step)

    def update(self):
        self.hover.reset()

        if self.gm.current_state == "COMBAT" and self.gm.active_combat:
            update_combat_hover(self)

        if self.gm.current_state == "HUB":
            dt = self.clock.get_time() / 1000.0
            MainMenu.get_hub().update(dt)

    def draw_card_by_data(self, card, x, y, enemy=None, player=None):
        is_hovered = (
            self.hover.card_index != -1 and y < self.base_y
        )
        # Активный бой → renderer считает превью урона (число + чипы реакций).
        combat_manager = self.gm.active_combat if self.gm else None
        return CardRenderer.draw(
            self.screen, card, x, y,
            self.card_font, self.card_desc_font,
            is_hovered, player=player, enemy=enemy,
            combat_manager=combat_manager,
        )

    def draw_text(self, text, font, color, x, y):
        self.screen.blit(font.render(text, True, color), (x, y))

    def draw(self):
        handler = DRAW_HANDLERS.get(self.gm.current_state)
        if handler:
            handler(self)
        # Единая строка ресурсов (HP/Золото/FP) поверх экранов-точек интереса.
        from ui.resource_hud import draw_resource_hud
        draw_resource_hud(self)
        pygame.display.flip()