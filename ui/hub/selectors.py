# ui/hub/selectors.py
# Отрисовка селектора классов. Возвращает кликабельные прямоугольники.
# Залоченные классы (ярус 2 без анлока) НЕ показываются совсем — экран чистый,
# карточки открытых классов паркуются слева и центрируются по их числу.
import pygame
from core import progression
from ui.hub.data import (
    CLASS_INFO, _PANEL_COLOR, _BTN_BORDER, _TITLE_COLOR, _TEXT_COLOR,
    _MUTED_COLOR, _CLS_W, _CLS_H, _CLS_GAP, _CLS_Y, SCREEN_W,
)


def draw_class_selector(screen, gm, mouse_pos) -> dict:
    """Нарисовать карточки ДОСТУПНЫХ классов. Возвращает {имя_класса: Rect} для кликов.
    Залоченные (ярус 2 без анлока) на экран не выводятся; видимые центрируются по их числу.
    Dev-флаг «полный доступ» (meta['dev_unlock_all']/env) возвращает все классы."""
    font_label = pygame.font.SysFont("Arial", 22, bold=True)
    font_stats = pygame.font.SysFont("Arial", 17, bold=True)
    font_desc  = pygame.font.SysFont("Arial", 16)

    meta = getattr(gm, "meta", None)
    selected_name = type(gm.player).__name__
    class_buttons = {}

    # Только разблокированные классы попадают на экран; раскладка пересчитывается
    # под их число (центрирование по фактической ширине ряда, без дыр).
    visible = [(name, info) for name, info in CLASS_INFO.items()
               if progression.is_unlocked(meta, name)]
    count = len(visible)
    row_w = count * _CLS_W + max(count - 1, 0) * _CLS_GAP
    x0 = (SCREEN_W - row_w) // 2

    for i, (cls_name, info) in enumerate(visible):
        bx   = x0 + i * (_CLS_W + _CLS_GAP)
        by   = _CLS_Y
        rect = pygame.Rect(bx, by, _CLS_W, _CLS_H)
        class_buttons[cls_name] = rect

        is_selected = cls_name == selected_name
        is_hovered  = rect.collidepoint(mouse_pos)

        # Фон карточки
        if is_selected:
            # Тёмный оттенок цвета класса
            bg = (
                min(info["color"][0] // 3 + 15, 80),
                min(info["color"][1] // 3 + 15, 80),
                min(info["color"][2] // 3 + 15, 80),
            )
        elif is_hovered:
            bg = (30, 30, 55)
        else:
            bg = _PANEL_COLOR

        pygame.draw.rect(screen, bg, rect, border_radius=12)

        # Рамка
        if is_selected:
            border_col = info["color"]
            border_w   = 3
        elif is_hovered:
            border_col = _BTN_BORDER
            border_w   = 2
        else:
            border_col = (60, 60, 90)
            border_w   = 1
        pygame.draw.rect(screen, border_col, rect, border_w, border_radius=12)

        # Цветная полоска сверху
        stripe = pygame.Rect(bx + border_w, by + border_w,
                             _CLS_W - border_w * 2, 6)
        pygame.draw.rect(screen, info["color"], stripe, border_radius=4)

        # Название класса
        lbl = font_label.render(info["label"], True, (255, 255, 255))
        screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, by + 18))

        # Разделитель под названием
        pygame.draw.line(screen, border_col,
                         (bx + 16, by + 46),
                         (bx + _CLS_W - 16, by + 46), 1)

        # Статы (HP / Энергия)
        st = font_stats.render(info["stats"], True,
                               _TITLE_COLOR if is_selected else _MUTED_COLOR)
        screen.blit(st, (rect.centerx - st.get_width() // 2, by + 54))

        # Описание — строки внутри карточки
        line_h = 20
        text_y = by + 82
        for line in info["lines"]:
            if line == "":
                text_y += 8
                continue
            # «Пассив:»/«Активная:» выделяем цветом класса
            if line in ("Пассив:", "Активная:"):
                col = info["color"]
                fnt = font_stats
            else:
                col = _TEXT_COLOR if is_selected else _MUTED_COLOR
                fnt = font_desc
            surf = fnt.render(line, True, col)
            screen.blit(surf, (rect.centerx - surf.get_width() // 2, text_y))
            text_y += line_h

    return class_buttons
