import pygame
from managers.network_manager import fetch_top_scores

class LeaderboardView:
    @staticmethod
    def load_data():
        """Пустой метод для совместимости архитектуры."""
        pass

    @staticmethod
    def draw_screen(view):
        WHITE  = (255, 255, 255)
        YELLOW = (241, 196, 15)
        GRAY   = (149, 165, 166)

        view.screen.fill((20, 20, 24))

        title_surf = view.main_font.render("ДОСКА ТРОФЕЕВ (ТОП-10 ИЗ СЕТИ)", True, YELLOW)
        view.screen.blit(title_surf, (960 - title_surf.get_width() // 2, 80))

        scores = fetch_top_scores()

        headers   = ["МЕСТО", "ИГРОК", "МАКС. ЭТАЖ", "УБИЙСТВА", "МАКС. УРОН"]
        columns_x = [350, 550, 900, 1150, 1400]

        for h, x in zip(headers, columns_x):
            h_surf = view.card_font.render(h, True, GRAY)
            view.screen.blit(h_surf, (x, 200))

        pygame.draw.line(view.screen, GRAY, (300, 240), (1620, 240), 2)

        if not scores:
            empty_surf = view.card_font.render(
                "Таблица рекордов пуста. Стань первым!", True, WHITE
            )
            view.screen.blit(empty_surf, (960 - empty_surf.get_width() // 2, 400))
        else:
            y_pos = 280
            for i, record in enumerate(scores):
                if isinstance(record, dict):
                    color = (
                        YELLOW         if i == 0 else
                        (192, 192, 192) if i == 1 else
                        (211, 84, 0)   if i == 2 else
                        WHITE
                    )
                    username = str(record.get("username", "Unknown"))
                    floor    = str(record.get("max_floor", 0))
                    kills    = str(record.get("kills", 0))
                    damage   = str(record.get("max_damage", 0))

                    view.screen.blit(view.card_font.render(f"#{i+1}", True, color),   (350,  y_pos))
                    view.screen.blit(view.card_font.render(username,   True, color),   (550,  y_pos))
                    view.screen.blit(view.card_font.render(floor,      True, color),   (900,  y_pos))
                    view.screen.blit(view.card_font.render(kills,      True, color),   (1150, y_pos))
                    view.screen.blit(view.card_font.render(damage,     True, color),   (1400, y_pos))
                    y_pos += 55

        # Кнопка возврата (хитбокс определён в GameView)
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = view.btn_back_leaderboard.collidepoint(mouse_pos)
        btn_color  = (90, 90, 95) if is_hovered else (50, 50, 50)
        pygame.draw.rect(view.screen, btn_color, view.btn_back_leaderboard)
        pygame.draw.rect(view.screen, WHITE, view.btn_back_leaderboard, 2)
        back_text = view.card_font.render("ВЕРНУТЬСЯ В МЕНЮ", True, WHITE)
        view.screen.blit(back_text, (960 - back_text.get_width() // 2, 922))

    @staticmethod
    def handle_clicks(view, mouse_pos) -> bool:
        """БАГ 1: только проверяет клик, возвращает True если нажата кнопка назад.
        Вся логика рестарта — в InputHandler."""
        if hasattr(view, 'btn_back_leaderboard') and view.btn_back_leaderboard.collidepoint(mouse_pos):
            return True
        return False