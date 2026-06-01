import pygame
import sys
from managers.GameManager import GameManager
from ui.MainMenu import MainMenu
from ui.CombatInterface import CombatInterface
from ui.InputHandler import InputHandler
from ui.Campfire import Campfire
from ui.Shop import Shop
from ui.MapView import MapView

class GameView:
    """Системный движок, переведенный на Full HD (1920x1080)."""
    def __init__(self):
        pygame.init()
        
        # --- НАСТРОЙКА FULL HD ---
        self.screen_width = 1920
        self.screen_height = 1080
        # Создаем окно 1920x1080 (можно добавить pygame.FULLSCREEN, но для тестов в окне лучше так)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Roguelike Card Game - FULL HD EDITION")
        
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.is_running = True
        
        # Крупные боярские шрифты под Full HD
        self.main_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.ui_font = pygame.font.SysFont("Courier New", 24)
        self.card_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.card_desc_font = pygame.font.SysFont("Arial", 16)
        
        # Новые Full HD координаты
        self.scroll_y = 0
        self.base_y = 760  # Сдвинули карты ниже, так как высота экрана теперь 1080
        self.card_width = 180
        self.card_height = 250
        
        # Кнопка Конца Хода теперь справа
        self.end_turn_rect = pygame.Rect(1600, 500, 220, 60)
        
        self.hovered_card_index = -1
        self.is_end_turn_hovered = False
        
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
                if event.button == 1: # ЛКМ
                    InputHandler.process_mouse_clicks(self, event.pos)
                elif event.button in [4, 5]: # Колесико
                    InputHandler.process_scroll(self, event.button)
                if event.button == 1: # ЛКМ
                    # --- ОБРАБОТКА КЛИКОВ МЕНЮ И ХАБА ---
                    if self.gm.current_state in ["MAIN_MENU", "HUB"]:
                        MainMenu.handle_clicks(self, mouse_pos)
                        continue
                    
                    # Весь остальной твой код (if self.gm.current_state == "COMBAT" и т.д.) идет ниже без изменений!


    def calculate_card_x(self, index, total_cards):
        """Динамический расчет X координаты для центрирования любого количества карт"""
        card_step = 200  # Стандартный шаг (ширина + зазор)
        total_width = total_cards * card_step
        
        # Если карт слишком много и они не влезают, начинаем их плотно сжимать!
        max_allowed_width = self.screen_width - 400
        if total_width > max_allowed_width:
            card_step = max_allowed_width / total_cards
            total_width = max_allowed_width
            
        start_x = (self.screen_width - total_width) / 2
        return int(start_x + index * card_step)

    def update(self):
        """Обсчет динамического ховера карт"""
        self.hovered_card_index = -1
        if self.gm.current_state == "COMBAT" and self.gm.active_combat:
            mouse_pos = pygame.mouse.get_pos()
            hand_size = len(self.gm.active_combat.deck_manager.hand)
            
            for index in range(hand_size):
                card_x = self.calculate_card_x(index, hand_size)
                card_rect = pygame.Rect(card_x, self.base_y, self.card_width, self.card_height)
                if card_rect.collidepoint(mouse_pos):
                    self.hovered_card_index = index
                    break

    def draw_text(self, text, font, color, x, y):
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def draw_card_by_data(self, card, x, y):
        """Универсальный отрисовщик карт под увеличенный Full HD размер 180х250"""
        rect = pygame.Rect(x, y, self.card_width, self.card_height)
        is_hovered = y < self.base_y
        bg_color = (55, 55, 55) if is_hovered else (45, 45, 45)
        border_color = (240, 70, 70) if card.card_type == "attack" else (70, 160, 240)
        if card.upgraded: border_color = (70, 240, 70)
        border_thickness = 5 if is_hovered else 3
        
        pygame.draw.rect(self.screen, bg_color, rect)
        pygame.draw.rect(self.screen, border_color, rect, border_thickness)
        self.draw_text(f"[{card.cost}]", self.card_font, (240, 240, 70), rect.x + 15, rect.y + 15)
        self.draw_text(card.name, self.card_font, (255, 255, 255), rect.x + 55, rect.y + 15)
        self.draw_text(card.description, self.card_desc_font, (200, 200, 200), rect.x + 15, rect.y + 70)

    def draw(self):
        if self.gm.current_state == "MAIN_MENU":
            MainMenu.draw_menu(self)
        elif self.gm.current_state == "HUB":
            MainMenu.draw_hub(self)
        # --- НОВОЕ: ОТРИСОВКА ПРОЦЕДУРНОЙ КАРТЫ ---
        elif self.gm.current_state == "MAP":
            MapView.draw_map(self)
        elif self.gm.current_state == "COMBAT":
            CombatInterface.draw_combat_screen(self)
        elif self.gm.current_state == "CAMPFIRE":
            Campfire.draw_screen(self)
        elif self.gm.current_state == "SHOP":
            Shop.draw_screen(self)
        pygame.display.flip()

