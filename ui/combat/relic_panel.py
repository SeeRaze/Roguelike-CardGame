# ui/combat/relic_panel.py
# Оверлей-инвентарь реликвий в бою: сетка всех реликвий (бейдж + название + описание).
# Открывается кликом по «АРТЕФАКТЫ» / «+N». Активную реликвию можно активировать прямо из панели.
import pygame
from core.rarity import RARITY_COLORS
from ui.combat.hud import CombatHUD, _RELIC_BADGE

_PANEL_W   = 1500
_PAD       = 30
_GAP       = 24
_ROW_H     = 86
_COLS      = 2
_TITLE_H   = 56


class RelicPanel:
    """Модальная панель со всеми реликвиями игрока. Работает на всех экранах."""
    _open    = False
    _gm_token = None
    _scroll   = 0          # вертикальное смещение прокрутки (пиксели), 0 = верх
    _max_scroll = 0        # предел прокрутки (считается при отрисовке)

    @classmethod
    def is_open(cls, view) -> bool:
        gm = getattr(view, 'gm', None)
        return cls._open and gm is not None and id(gm) == cls._gm_token

    @classmethod
    def open(cls, view):
        cls._open    = True
        cls._gm_token = id(getattr(view, 'gm', None))
        cls._scroll  = 0          # каждое открытие — с верха списка

    @classmethod
    def close(cls):
        cls._open = False

    @classmethod
    def scroll(cls, direction):
        """Прокрутка колесом (direction: -1 вверх / +1 вниз). Клампится к [0, max]."""
        cls._scroll = max(0, min(cls._max_scroll, cls._scroll + direction * 60))

    @classmethod
    def draw(cls, view, screen):
        relics = getattr(view.gm, 'relics', [])
        sw, sh = screen.get_size()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        rows     = max(1, (len(relics) + _COLS - 1) // _COLS)
        content_h = rows * _ROW_H
        # Панель не выше экрана: высоту контента кэпим, остаток — под прокрутку.
        max_panel_h = sh - 40
        panel_h  = min(_TITLE_H + content_h + _PAD, max_panel_h)
        panel_x  = (sw - _PANEL_W) // 2
        panel_y  = max(20, (sh - panel_h) // 2)
        panel    = pygame.Rect(panel_x, panel_y, _PANEL_W, panel_h)
        view.relic_panel_rect = panel

        pygame.draw.rect(screen, (18, 18, 30), panel, border_radius=14)
        pygame.draw.rect(screen, (160, 160, 255), panel, 2, border_radius=14)

        title = view.main_font.render(f"АРТЕФАКТЫ ({len(relics)})", True, (255, 220, 60))
        screen.blit(title, (panel_x + _PAD, panel_y + 14))

        # Видимая высота области контента (под заголовком) + предел прокрутки.
        view_h = panel_h - _TITLE_H - _PAD
        cls._max_scroll = max(0, content_h - view_h)
        cls._scroll = max(0, min(cls._max_scroll, cls._scroll))

        # Подсказка о прокрутке, если список не влезает целиком.
        if cls._max_scroll > 0:
            hint = view.card_desc_font.render("колесо — прокрутка", True, (140, 140, 170))
            screen.blit(hint, (panel.right - 50 - hint.get_width() - 16, panel_y + 20))

        # Кнопка закрытия
        close_rect = pygame.Rect(panel.right - 50, panel_y + 12, 36, 32)
        hov = close_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, (90, 40, 40) if hov else (50, 30, 30),
                         close_rect, border_radius=6)
        x_lbl = view.card_font.render("X", True, (240, 200, 200))
        screen.blit(x_lbl, (close_rect.centerx - x_lbl.get_width() // 2,
                            close_rect.centery - x_lbl.get_height() // 2))
        view.relic_panel_close_rect = close_rect

        col_w   = (_PANEL_W - _PAD * 2 - _GAP) // _COLS
        cont_y  = panel_y + _TITLE_H
        mouse   = pygame.mouse.get_pos()
        view.relic_panel_cell_rects = []

        # Клип содержимого областью прокрутки: ряды за краями панели не вылезают
        # на заголовок/рамку. Прокрутка сдвигает ряды вверх на _scroll.
        clip = pygame.Rect(panel_x + 2, cont_y, _PANEL_W - 4, panel_y + panel_h - cont_y - 2)
        screen.set_clip(clip)

        for i, relic in enumerate(relics):
            col = i % _COLS
            row = i // _COLS
            cx  = panel_x + _PAD + col * (col_w + _GAP)
            cy  = cont_y + row * _ROW_H - cls._scroll
            # Пропускаем ряды полностью вне видимой области (не кликабельны, не рисуются).
            if cy + _ROW_H < clip.top or cy > clip.bottom:
                continue
            cell = pygame.Rect(cx, cy, col_w, _ROW_H - 8)
            view.relic_panel_cell_rects.append((cell, relic))

            is_active = getattr(relic, 'is_active', False)
            used      = getattr(relic, '_used', False)
            if cell.collidepoint(mouse):
                pygame.draw.rect(screen, (32, 32, 50), cell, border_radius=8)

            CombatHUD.draw_relic_badge(
                screen, relic, pygame.Rect(cx + 4, cy + 4, _RELIC_BADGE, _RELIC_BADGE)
            )

            name_color = RARITY_COLORS.get(relic.rarity, (200, 200, 200))
            nx = cx + _RELIC_BADGE + 16
            name = relic.name + (
                "  ● готова" if (is_active and not used) else
                "  ● использована" if (is_active and used) else ""
            )
            screen.blit(view.card_font.render(name, True, name_color), (nx, cy + 4))

            for li, line in enumerate(relic.description.split("\n")[:2]):
                screen.blit(view.card_desc_font.render(line, True, (200, 200, 200)),
                            (nx, cy + 30 + li * 18))

        screen.set_clip(None)

    @classmethod
    def handle_click(cls, view, mouse_pos) -> bool:
        """True, если клик поглощён открытой панелью."""
        if not cls.is_open(view):
            return False

        if getattr(view, 'relic_panel_close_rect', None) and \
                view.relic_panel_close_rect.collidepoint(mouse_pos):
            cls.close()
            return True

        for rect, relic in getattr(view, 'relic_panel_cell_rects', []):
            if rect.collidepoint(mouse_pos):
                combat = getattr(view.gm, 'active_combat', None)
                if getattr(relic, 'is_active', False) and combat is not None:
                    relic.activate(combat)
                    cls.close()
                return True

        # Клик вне панели -- закрыть
        if getattr(view, 'relic_panel_rect', None) and \
                not view.relic_panel_rect.collidepoint(mouse_pos):
            cls.close()
        return True
