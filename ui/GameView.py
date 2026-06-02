import pygame
import sys
from managers.GameManager import GameManager
from ui.MainMenu import MainMenu
from ui.CombatInterface import CombatInterface
from ui.InputHandler import InputHandler
from ui.Campfire import Campfire
from ui.Shop import Shop
from ui.MapView import MapView
from ui.LeaderboardView import LeaderboardView
from ui.CardRenderer import CardRenderer
from ui.Chest import Chest


class GameView:
    """Системный движок, переведённый на Full HD (1920x1080)."""
    def __init__(self):
        pygame.init()

        self.screen_width  = 1920
        self.screen_height = 1080
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Roguelike Card Game - FULL HD EDITION")

        self.clock = pygame.time.Clock()
        self.fps   = 60
        self.is_running = True

        self.main_font      = pygame.font.SysFont("Arial", 32, bold=True)
        self.ui_font        = pygame.font.SysFont("Courier New", 24)
        self.card_font      = pygame.font.SysFont("Arial", 22, bold=True)
        self.card_desc_font = pygame.font.SysFont("Arial", 16)

        self.scroll_y = 0
        self.base_y   = 760
        self.card_width  = 180
        self.card_height = 250

        self.end_turn_rect        = pygame.Rect(1600, 500, 220, 60)
        self.btn_back_leaderboard = pygame.Rect(760, 900, 400, 70)

        self.hovered_card_index  = -1
        self.is_end_turn_hovered = False
        self._map_hovered_col    = None

        # Hover-состояние для тултипов статусов на существах
        self.hovered_status_key  = None
        self.hovered_status_val  = 0
        self.enemy_badge_rects   = []
        self.player_badge_rects  = []

        # Hover-состояние для тултипа ключевых слов карты
        self.hovered_card_rect   = None   # pygame.Rect карты под курсором
        self.hovered_card_obj    = None   # сам объект Card

        self.gm = GameManager()
        self.gm.start_game()

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
        self.is_end_turn_hovered = self.end_turn_rect.collidepoint(mouse_pos)

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
        self.hovered_status_val  = 0
        self.hovered_card_index = -1
        self.hovered_status_key = None
        self.hovered_card_rect  = None
        self.hovered_card_obj   = None

        if self.gm.current_state == "COMBAT" and self.gm.active_combat:
            mouse_pos = pygame.mouse.get_pos()
            dm = self.gm.active_combat.deck_manager
            hand_size = len(dm.hand)

            # Hover карт в руке
            for index in range(hand_size):
                card_x = self.calculate_card_x(index, hand_size)
                card_rect = pygame.Rect(
                    card_x, self.base_y, self.card_width, self.card_height
                )
                if card_rect.collidepoint(mouse_pos):
                    self.hovered_card_index = index
                    self.hovered_card_rect  = card_rect
                    self.hovered_card_obj   = dm.hand[index]
                    break

            # Hover бейджей статусов
            for rect, key, val in self.enemy_badge_rects:
                if rect.collidepoint(mouse_pos):
                    self.hovered_status_key = key
                    self.hovered_status_val = val
                    break
            if not self.hovered_status_key:
                for rect, key, val in self.player_badge_rects:
                    if rect.collidepoint(mouse_pos):
                        self.hovered_status_key = key
                        self.hovered_status_val = val
                        break

        if self.gm.current_state == "HUB":
            from ui.MainMenu import MainMenu
            dt = self.clock.get_time() / 1000.0
            MainMenu.get_hub().update(dt)

    def draw_card_by_data(self, card, x, y, enemy=None, player=None):
        is_hovered = False
        if hasattr(self, 'hovered_card_index') and self.hovered_card_index != -1:
            if y < self.base_y:
                is_hovered = True
        return CardRenderer.draw(
            self.screen, card, x, y,
            self.card_font, self.card_desc_font,
            is_hovered, player=player, enemy=enemy
        )

    def draw_text(self, text, font, color, x, y):
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def draw(self):
        if self.gm.current_state == "MAIN_MENU":
            MainMenu.draw_menu(self)
        elif self.gm.current_state == "HUB":
            MainMenu.draw_hub(self)
        elif self.gm.current_state == "MAP":
            MapView.draw_map(self)
        elif self.gm.current_state == "COMBAT":
            CombatInterface.draw_combat_screen(self)
            # Тултип ключевых слов карты -- поверх всего боевого экрана
            if self.hovered_card_obj and self.hovered_card_rect:
                CardRenderer.draw_card_keyword_tooltip(
                    self.screen,
                    self.card_font,
                    self.card_desc_font,
                    self.hovered_card_obj,
                    self.hovered_card_rect
                )
        elif self.gm.current_state == "CAMPFIRE":
            Campfire.draw_screen(self)
        elif self.gm.current_state == "SHOP":
            Shop.draw_screen(self)
        elif self.gm.current_state == "LEADERBOARD":
            LeaderboardView.draw_screen(self)
        elif self.gm.current_state == "CHEST":
            Chest.draw_screen(self)
        elif self.gm.current_state == "EVENT":
            from ui.EventView import draw_screen as draw_event
            draw_event(self)

        pygame.display.flip()

    def _draw_placeholder(self, state, title, subtitle):
        self.screen.fill((20, 20, 30))
        self.draw_text(title,    self.main_font, (255, 220, 60), 760, 480)
        self.draw_text(subtitle, self.ui_font,   (180, 180, 180), 820, 530)
        btn = pygame.Rect(760, 620, 400, 70)
        pygame.draw.rect(self.screen, (60, 60, 80), btn)
        pygame.draw.rect(self.screen, (255, 255, 255), btn, 2)
        self.draw_text("Продолжить ->", self.card_font, (255, 255, 255), 870, 643)
        mouse = pygame.mouse.get_pos()
        if btn.collidepoint(mouse):
            for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
                if event.button == 1:
                    self.gm.current_floor += 1
                    self.gm.setup_next_floor()