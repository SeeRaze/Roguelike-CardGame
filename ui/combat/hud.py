import pygame
import random as _rnd
from core.StatusRegistry import STATUSES
from core.rarity import RARITY_COLORS


class CombatHUD:
    """Вспомогательные методы отрисовки HUD: HP-бары, бейджи статусов, тултипы."""

    @staticmethod
    def draw_hp_bar(screen, x, y, width, height, current_hp, max_hp, shield):
        pygame.draw.rect(screen, (40, 40, 40), (x, y, width, height))
        hp_percent = max(0, min(current_hp / max_hp, 1))
        fill_width = int(width * hp_percent)
        if fill_width > 0:
            pygame.draw.rect(screen, (70, 200, 70), (x, y, fill_width, height))
        if shield > 0:
            shield_percent = min(shield / max_hp, 1)
            shield_width = int(width * shield_percent)
            pygame.draw.rect(screen, (70, 160, 240), (x, y, shield_width, 8))
        pygame.draw.rect(screen, (200, 200, 200), (x, y, width, height), 1)

    @staticmethod
    def get_intent_damage_color(predicted_dmg, player_shield):
        """Красный если пробивает щит, синий если нет."""
        if predicted_dmg > player_shield:
            return (255, 51, 51)
        return (51, 153, 255)

    @staticmethod
    def draw_status_badges(screen, font, creature, x, y):
        """
        Рисует цветные бейджи активных статусов существа начиная с (x, y).
        Возвращает список [(rect, status_key, val)] для hover-проверки.
        Пропускает статусы с нулевым значением.
        """
        badge_rects = []
        cursor_x = x
        pad_x, pad_y = 8, 4
        badge_h = font.get_linesize() + pad_y * 2

        for key, data in STATUSES.items():
            val = getattr(creature, key, 0)
            if val <= 0:
                continue

            abbr     = data["abbr"]
            bg_color = data["badge_bg"]
            fg_color = data["badge_fg"]
            label    = f"{abbr} {val}"

            text_surf = font.render(label, True, fg_color)
            badge_w   = text_surf.get_width() + pad_x * 2

            rect = pygame.Rect(cursor_x, y, badge_w, badge_h)
            pygame.draw.rect(screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(screen, (255, 255, 255), rect, 1, border_radius=5)
            screen.blit(text_surf, (cursor_x + pad_x, y + pad_y))

            badge_rects.append((rect, key, val))
            cursor_x += badge_w + 6

        return badge_rects

    @staticmethod
    def draw_relics(screen, font, relics, x, y):
        """
        Рисует реликвии в ряд начиная с (x, y).
        Каждая реликвия -- прямоугольник с рамкой цвета редкости.
        Возвращает список [(rect, relic)] для hover-проверки.
        """
        relic_rects = []
        cursor_x = x
        pad_x, pad_y = 10, 5
        relic_h = font.get_linesize() + pad_y * 2

        for relic in relics:
            text_surf    = font.render(relic.name, True, (230, 230, 230))
            relic_w      = text_surf.get_width() + pad_x * 2
            rect         = pygame.Rect(cursor_x, y, relic_w, relic_h)
            border_color = RARITY_COLORS.get(relic.rarity, (150, 150, 150))

            pygame.draw.rect(screen, (35, 35, 45), rect, border_radius=5)
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=5)
            screen.blit(text_surf, (cursor_x + pad_x, y + pad_y))

            relic_rects.append((rect, relic))
            cursor_x += relic_w + 8

        return relic_rects

    @staticmethod
    def draw_status_tooltip(screen, font_desc, status_key, status_val, mouse_pos):
        """
        Рисует тултип с описанием статуса рядом с курсором.
        status_val подставляется вместо N в тексте описания.
        Вызывается последним -- поверх всего остального.
        """
        data = STATUSES.get(status_key)
        if not data:
            return

        raw_text = data["tooltip"].replace("N", str(status_val))
        lines    = raw_text.split("\n")

        pad_x, pad_y = 12, 8
        line_h = font_desc.get_linesize() + 2
        max_w  = max(font_desc.size(l)[0] for l in lines)
        box_w  = max_w + pad_x * 2
        box_h  = len(lines) * line_h + pad_y * 2

        tip_x = mouse_pos[0] + 16
        tip_y = mouse_pos[1] + 16

        screen_w, screen_h = screen.get_size()
        if tip_x + box_w > screen_w - 10:
            tip_x = mouse_pos[0] - box_w - 10
        if tip_y + box_h > screen_h - 10:
            tip_y = mouse_pos[1] - box_h - 10

        bg_rect = pygame.Rect(tip_x, tip_y, box_w, box_h)
        pygame.draw.rect(screen, (20, 20, 25), bg_rect, border_radius=6)
        pygame.draw.rect(screen, (200, 200, 200), bg_rect, 1, border_radius=6)

        for i, line in enumerate(lines):
            surf = font_desc.render(line, True, (230, 230, 230))
            screen.blit(surf, (tip_x + pad_x, tip_y + pad_y + i * line_h))

    @staticmethod
    def draw_relic_tooltip(screen, font, relic, mouse_pos):
        """
        Рисует тултип с именем и описанием реликвии рядом с курсором.
        Вызывается последним -- поверх всего остального.
        """
        lines        = relic.description.split("\n")
        border_color = RARITY_COLORS.get(relic.rarity, (150, 150, 150))

        pad_x, pad_y = 12, 8
        line_h = font.get_linesize() + 2
        max_w  = max((font.size(l)[0] for l in lines), default=100)
        max_w  = max(max_w, font.size(relic.name)[0])
        box_w  = max_w + pad_x * 2
        box_h  = len(lines) * line_h + pad_y * 2 + line_h + 4

        tip_x = mouse_pos[0] + 16
        tip_y = mouse_pos[1] + 16

        screen_w, screen_h = screen.get_size()
        if tip_x + box_w > screen_w - 10:
            tip_x = mouse_pos[0] - box_w - 10
        if tip_y + box_h > screen_h - 10:
            tip_y = mouse_pos[1] - box_h - 10

        bg_rect = pygame.Rect(tip_x, tip_y, box_w, box_h)
        pygame.draw.rect(screen, (20, 20, 25), bg_rect, border_radius=6)
        pygame.draw.rect(screen, border_color, bg_rect, 2, border_radius=6)

        name_surf = font.render(relic.name, True, border_color)
        screen.blit(name_surf, (tip_x + pad_x, tip_y + pad_y))

        for i, line in enumerate(lines):
            surf = font.render(line, True, (200, 200, 200))
            screen.blit(surf, (tip_x + pad_x, tip_y + pad_y + line_h + 4 + i * line_h))

    @staticmethod
    def draw_pile_tooltip(screen, font_title, font_desc, cards, title, mouse_pos):
        """
        Рисует тултип со списком карт стопки рядом с курсором.
        cards -- список объектов Card в порядке отображения.
        Вызывается последним -- поверх всего остального.
        """
        if not cards:
            lines = ["(пусто)"]
        else:
            lines = [f"  {c.name}" for c in cards]

        pad_x, pad_y = 12, 8
        line_h  = font_desc.get_linesize() + 2
        title_h = font_title.get_linesize() + 4

        all_widths = [font_desc.size(l)[0] for l in lines]
        all_widths.append(font_title.size(title)[0])
        box_w = max(all_widths) + pad_x * 2
        box_h = title_h + len(lines) * line_h + pad_y * 2

        # Всплывает вверх над стопкой, не перекрывает руку
        tip_x = mouse_pos[0] + 16
        tip_y = mouse_pos[1] - box_h - 10

        screen_w, screen_h = screen.get_size()
        if tip_x + box_w > screen_w - 10:
            tip_x = mouse_pos[0] - box_w - 10
        if tip_y < 10:
            tip_y = mouse_pos[1] + 16

        bg_rect = pygame.Rect(tip_x, tip_y, box_w, box_h)
        pygame.draw.rect(screen, (20, 20, 25), bg_rect, border_radius=6)
        pygame.draw.rect(screen, (180, 180, 180), bg_rect, 1, border_radius=6)

        # Заголовок
        title_surf = font_title.render(title, True, (240, 220, 80))
        screen.blit(title_surf, (tip_x + pad_x, tip_y + pad_y))

        # Список карт
        for i, line in enumerate(lines):
            surf = font_desc.render(line, True, (200, 200, 200))
            screen.blit(surf, (tip_x + pad_x, tip_y + pad_y + title_h + i * line_h))