import pygame
import sys

class MainMenu:
    """Отрисовщик Главного меню и Мета-Хаба с ховер-подсветкой кнопок."""
    
    # Флаги ховеров для кнопок
    is_play_hovered = False
    is_exit_hovered = False
    is_start_run_hovered = False

    @staticmethod
    def draw_menu(view):
        """Рисует самое первое Главное меню при запуске игры"""
        view.screen.fill((15, 15, 20)) # Угольно-черный фон заставки
        mouse_pos = pygame.mouse.get_pos()
        
        # Заголовок игры
        view.draw_text("ROGUELIKE CARD GAME", view.main_font, (240, 240, 70), 100, 200)
        view.draw_text("Pre-Alpha Edition v0.3", view.card_desc_font, (150, 150, 150), 100, 250)
        
        # Кнопка "ИГРАТЬ" (Вход в Хаб)
        view.btn_menu_play = pygame.Rect(100, 350, 350, 70)
        MainMenu.is_play_hovered = view.btn_menu_play.collidepoint(mouse_pos)
        play_color = (90, 90, 95) if MainMenu.is_play_hovered else (60, 60, 60)
        pygame.draw.rect(view.screen, play_color, view.btn_menu_play)
        pygame.draw.rect(view.screen, (255, 255, 255), view.btn_menu_play, 2)
        view.draw_text("ВОЙТИ В ЛАГЕРЬ", view.card_font, (255, 255, 255), 170, 372)
        
        # Кнопка "ВЫХОД"
        view.btn_menu_exit = pygame.Rect(100, 450, 350, 70)
        MainMenu.is_exit_hovered = view.btn_menu_exit.collidepoint(mouse_pos)
        exit_color = (90, 60, 60) if MainMenu.is_exit_hovered else (60, 40, 40)
        pygame.draw.rect(view.screen, exit_color, view.btn_menu_exit)
        pygame.draw.rect(view.screen, (255, 255, 255), view.btn_menu_exit, 2)
        view.draw_text("ВЫХОД", view.card_font, (255, 255, 255), 230, 472)

    @staticmethod
    def draw_hub(view):
        """Рисует Мета-Хаб (Лагерь) перед вылазкой в башню"""
        view.screen.fill((25, 25, 30)) # Спокойный серый фон лагеря
        mouse_pos = pygame.mouse.get_pos()
        
        view.draw_text("=== ВАШ ЛАГЕРЬ И КУЗНИЦА ===", view.main_font, (255, 255, 255), 100, 50)
        view.draw_text(f"Текущие сбережения: {view.gm.player_gold} золотых монет", view.ui_font, (240, 240, 70), 100, 110)
        
        # Выводим стартовую колоду для ознакомления
        view.draw_text("Стартовая колода для забега:", view.ui_font, (150, 150, 150), 100, 180)
        for index, card in enumerate(view.gm.current_deck):
            # Рисуем первые 8 карт колоды в аккуратный горизонтальный ряд мини-версий
            card_x = 100 + index * 140
            card_y = 230
            mini_rect = pygame.Rect(card_x, card_y, 120, 160)
            pygame.draw.rect(view.screen, (45, 45, 45), mini_rect)
            pygame.draw.rect(view.screen, (70, 160, 240), mini_rect, 2)
            view.draw_text(card.name, view.card_desc_font, (255, 255, 255), card_x + 10, card_y + 20)
            view.draw_text(f"Кост: {card.cost}", view.card_desc_font, (240, 240, 70), card_x + 10, card_y + 50)

        # Огромная кнопка "В БОЙ! НАЧАТЬ ЗАБЕГ"
        view.btn_start_run = pygame.Rect(100, 500, 450, 90)
        MainMenu.is_start_run_hovered = view.btn_start_run.collidepoint(mouse_pos)
        btn_color = (70, 180, 70) if MainMenu.is_start_run_hovered else (40, 130, 40)
        pygame.draw.rect(view.screen, btn_color, view.btn_start_run)
        pygame.draw.rect(view.screen, (255, 255, 255), view.btn_start_run, 3)
        view.draw_text("ПОДНЯТЬСЯ В БАШНЮ [В БОЙ]", view.card_font, (255, 255, 255), 160, 532)

    @staticmethod
    def handle_clicks(view, mouse_pos):
        """Обрабатывает клики в Меню и Хабе"""
        if view.gm.current_state == "MAIN_MENU":
            if hasattr(view, 'btn_menu_play') and view.btn_menu_play.collidepoint(mouse_pos):
                view.gm.current_state = "HUB" # Переходим в Лагерь
            elif hasattr(view, 'btn_menu_exit') and view.btn_menu_exit.collidepoint(mouse_pos):
                pygame.quit()
                sys.exit()
                
        elif view.gm.current_state == "HUB":
            if hasattr(view, 'btn_start_run') and view.btn_start_run.collidepoint(mouse_pos):
                print(" >>> СТАРТ НОВОГО ЗАБЕГА ИЗ ХАБА! <<<")
                # Полностью обнуляем параметры под свежий ран
                view.gm.current_floor = 1
                view.gm.player.hp = view.gm.player.max_hp
                view.gm.setup_next_floor() # Генерирует первый этаж боя
