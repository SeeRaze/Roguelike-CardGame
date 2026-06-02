import pygame
import sys
from dataclasses import dataclass, field
from typing import Optional
from managers.GameManager import GameManager
from ui.MainMenu import MainMenu
from ui.CombatInterface import CombatInterface
from ui.InputHandler import InputHandler
from ui.Campfire import Campfire
from ui.Shop import Shop
from ui.MapView import MapView
from ui.LeaderboardView import LeaderboardView
from ui.CardRenderer import CardRenderer
from ui.chest import Chest
from ui.VictoryScreen import VictoryScreen
from ui.CardLibraryView import CardLibraryView

@dataclass
class HoverState:
    """Всё hover-состояние за один кадр. Сбрасывается в update()."""
    card_index:   int              = -1
    card_rect:    Optional[object] = None
    card_obj:     Optional[object] = None
    status_key:   Optional[str]    = None
    status_val:   int              = 0
    end_turn:     bool             = False
    map_col:      Optional[int]    = None
    relic_obj:    Optional[object] = None  # реликвия под курсором

    def reset(self):
        self.card_index  = -1
        self.card_rect   = None
        self.card_obj    = None
        self.status_key  = None
        self.status_val  = 0
        self.end_turn    = False
        self.map_col     = None
        self.relic_obj   = None


# Диспетчер отрисовки: состояние -> функция.
# Добавить новый экран = один импорт + одна строка здесь.
def _draw_main_menu(view):   MainMenu.draw_menu(view)
def _draw_hub(view):         MainMenu.draw_hub(view)
def _draw_map(view):         MapView.draw_map(view)
def _draw_campfire(view):    Campfire.draw_screen(view)
def _draw_shop(view):        Shop.draw_screen(view)
def _draw_leaderboard(view): LeaderboardView.draw_screen(view)
def _draw_chest(view):       Chest.draw_screen(view)
def _draw_victory(view):     VictoryScreen.draw_screen(view)
def _draw_card_library(view): CardLibraryView.draw_screen(view)

def _draw_event(view):
    from ui.EventView import draw_screen as draw_event
    draw_event(view)

def _draw_combat(view):
    CombatInterface.draw_combat_screen(view)
    if view.hover.card_obj and view.hover.card_rect:
        CardRenderer.draw_card_keyword_tooltip(
            view.screen,
            view.card_font,
            view.card_desc_font,
            view.hover.card_obj,
            view.hover.card_rect,
        )

DRAW_HANDLERS = {
    "MAIN_MENU":   _draw_main_menu,
    "HUB":         _draw_hub,
    "MAP":         _draw_map,
    "COMBAT":      _draw_combat,
    "CAMPFIRE":    _draw_campfire,
    "SHOP":        _draw_shop,
    "LEADERBOARD": _draw_leaderboard,
    "CHEST":       _draw_chest,
    "EVENT":       _draw_event,
    "VICTORY":     _draw_victory,
    "CARD_LIBRARY": _draw_card_library,
}


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

        self.main_font      = pygame.font.SysFont("Arial", 32, bold=True)
        self.ui_font        = pygame.font.SysFont("Courier New", 24)
        self.card_font      = pygame.font.SysFont("Arial", 22, bold=True)
        self.card_desc_font = pygame.font.SysFont("Arial", 16)

        self.scroll_y    = 0
        self.base_y      = 760
        self.card_width  = 180
        self.card_height = 250

        self.end_turn_rect        = pygame.Rect(1600, 500, 220, 60)
        self.btn_back_leaderboard = pygame.Rect(760, 900, 400, 70)

        # Все hover-данные в одном объекте
        self.hover = HoverState()

        # Бейджи статусов и реликвии (заполняются CombatHUD)
        self.enemy_badge_rects  = []
        self.player_badge_rects = []
        self.relic_rects        = []

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
            mouse_pos = pygame.mouse.get_pos()
            dm = self.gm.active_combat.deck_manager
            hand_size = len(dm.hand)

            for index in range(hand_size):
                card_x = self.calculate_card_x(index, hand_size)
                card_rect = pygame.Rect(
                    card_x, self.base_y, self.card_width, self.card_height
                )
                if card_rect.collidepoint(mouse_pos):
                    self.hover.card_index = index
                    self.hover.card_rect  = card_rect
                    self.hover.card_obj   = dm.hand[index]
                    break

            for rect, key, val in self.enemy_badge_rects:
                if rect.collidepoint(mouse_pos):
                    self.hover.status_key = key
                    self.hover.status_val = val
                    break
            if not self.hover.status_key:
                for rect, key, val in self.player_badge_rects:
                    if rect.collidepoint(mouse_pos):
                        self.hover.status_key = key
                        self.hover.status_val = val
                        break

            for rect, relic in self.relic_rects:
                if rect.collidepoint(mouse_pos):
                    self.hover.relic_obj = relic
                    break

        if self.gm.current_state == "HUB":
            dt = self.clock.get_time() / 1000.0
            MainMenu.get_hub().update(dt)

    def draw_card_by_data(self, card, x, y, enemy=None, player=None):
        is_hovered = (
            self.hover.card_index != -1 and y < self.base_y
        )
        return CardRenderer.draw(
            self.screen, card, x, y,
            self.card_font, self.card_desc_font,
            is_hovered, player=player, enemy=enemy,
        )

    def draw_text(self, text, font, color, x, y):
        self.screen.blit(font.render(text, True, color), (x, y))

    def draw(self):
        handler = DRAW_HANDLERS.get(self.gm.current_state)
        if handler:
            handler(self)
        pygame.display.flip()

    def _draw_placeholder(self, state, title, subtitle):
        self.screen.fill((20, 20, 30))
        self.draw_text(title,    self.main_font, (255, 220, 60),  760, 480)
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