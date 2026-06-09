# ui/relic_library/base.py
# Библиотека артефактов: весь пул в ОДИН скроллящийся экран, сгруппированный по
# действию (без вкладок). Для ревизии контента — видно имя, редкость, класс, эффект.
import pygame
from core.rarity import RARITY_COLORS
from ui.relic_library.data import grouped_relics, total_count

_START_Y = 110          # верх области списка (под шапкой)
_X0      = 60           # левый отступ строки
_X_TEXT  = _X0 + 30     # текст после ромба-редкости
_MAX_W   = 1820         # ширина под перенос описания
_CAT_COL = (150, 185, 240)


def _wrap(text, font, max_w):
    """Перенос по словам с учётом явных переводов строки в описании ('\\n')."""
    lines = []
    for seg in text.split("\n"):
        cur = ""
        for w in seg.split(" "):
            t = (cur + " " + w).strip()
            if font.size(t)[0] <= max_w or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


class RelicLibraryView:
    _scroll_y   = 0
    _content_h  = 0
    _btn_back   = pygame.Rect(30, 20, 160, 50)
    _groups     = None       # кэш сгруппированного пула (строится один раз)

    @classmethod
    def reset(cls):
        cls._scroll_y = 0

    @classmethod
    def _get_groups(cls):
        if cls._groups is None:
            cls._groups = grouped_relics()
        return cls._groups

    @classmethod
    def draw_screen(cls, view):
        screen = view.screen
        screen.fill((12, 12, 18))
        mouse = pygame.mouse.get_pos()

        font_cat  = pygame.font.SysFont("Arial", 22, bold=True)
        font_name = pygame.font.SysFont("Arial", 20, bold=True)
        font_desc = pygame.font.SysFont("Arial", 16)
        font_tag  = pygame.font.SysFont("Arial", 14, bold=True)

        # Шапка
        view.draw_text("БИБЛИОТЕКА АРТЕФАКТОВ", view.main_font, (240, 200, 60), 700, 24)
        view.draw_text(f"Всего: {total_count()}", font_desc, (140, 140, 140), 1800, 34)

        back_col = (80, 80, 90) if cls._btn_back.collidepoint(mouse) else (50, 50, 60)
        pygame.draw.rect(screen, back_col, cls._btn_back, border_radius=8)
        pygame.draw.rect(screen, (200, 200, 200), cls._btn_back, 2, border_radius=8)
        view.draw_text("<  Назад", view.card_font, (255, 255, 255), 42, 35)
        pygame.draw.line(screen, (60, 60, 80), (0, 80), (1920, 80), 2)

        # Список (клип + скролл)
        clip = pygame.Rect(0, 82, 1920, 1080 - 82)
        screen.set_clip(clip)
        y = _START_Y - cls._scroll_y
        line_h = font_desc.get_linesize()

        for category, relics in cls._get_groups():
            # Заголовок категории
            if -40 <= y <= 1080:
                head = font_cat.render(f"{category}  ({len(relics)})", True, _CAT_COL)
                screen.blit(head, (_X0, y))
                pygame.draw.line(screen, (50, 60, 80),
                                 (_X0, y + 28), (1880, y + 28), 1)
            y += 40

            for relic in relics:
                rcolor = RARITY_COLORS.get(relic.rarity, (150, 150, 150))
                desc_lines = _wrap(relic.description, font_desc, _MAX_W - 30)
                row_h = font_name.get_linesize() + len(desc_lines) * line_h + 10

                # Рисуем только видимые строки (вне области — просто сдвигаем y).
                if y + row_h >= 82 and y <= 1080:
                    # Ромб редкости
                    cy = y + 11
                    r = 7
                    pygame.draw.polygon(screen, rcolor, [
                        (_X0 + 6, cy - r), (_X0 + 6 + r, cy),
                        (_X0 + 6, cy + r), (_X0 + 6 - r, cy)])
                    # Имя (цвет редкости) + класс-тег
                    name_surf = font_name.render(relic.name, True, rcolor)
                    screen.blit(name_surf, (_X_TEXT, y))
                    nx = _X_TEXT + name_surf.get_width() + 10
                    if relic.relic_class:
                        tag = font_tag.render(f"[{relic.relic_class}]", True, (170, 140, 90))
                        screen.blit(tag, (nx, y + 4))
                    # Описание (серый, с переносом)
                    dy = y + font_name.get_linesize()
                    for ln in desc_lines:
                        screen.blit(font_desc.render(ln, True, (175, 175, 185)),
                                    (_X_TEXT, dy))
                        dy += line_h
                y += row_h

            y += 14   # зазор между категориями

        screen.set_clip(None)

        # Полная высота контента (для клампа скролла).
        cls._content_h = y + cls._scroll_y - _START_Y

    @classmethod
    def _max_scroll(cls):
        view_h = 1080 - _START_Y
        return max(0, cls._content_h - view_h + 40)

    @classmethod
    def handle_click(cls, view, mouse_pos):
        if cls._btn_back.collidepoint(mouse_pos):
            view.gm.current_state = "MAIN_MENU"

    @classmethod
    def handle_scroll(cls, direction):
        cls._scroll_y = max(0, min(cls._scroll_y + direction * 60, cls._max_scroll()))
