# ui/hub/achievements_view.py
# Экран КАТАЛОГА ДОСТИЖЕНИЙ + лестницы Грейда (С70 Этап 4-полировка). Игрок видит:
#   • все 6 ачивок MVP — выполнено/заперто, условие, награда (что откроется);
#   • сводку X/6;
#   • лестницу Грейда L0..L4 с прогресс-баром накопления и бонусом следующей ступени.
# Это «карта целей» петли мета-прогрессии: дофамин = ВИДНО, что чейзить.
#
# Состояние gm.current_state == "ACHIEVEMENTS". Регистрируется в DRAW_HANDLERS /
# клик-роутинге (MainMenu/GameView). Только UI: данные тянет из core.achievements +
# core.meta_currency, мету не мутирует.
#
# Пур-хелперы catalog_rows()/progress_summary() отделены от pygame-отрисовки —
# тестируются без боя (tests/test_achievements_view.py).

import pygame

from core import achievements, meta_currency
from ui.hub.data import (
    SCREEN_W,
    _BG_COLOR, _PANEL_COLOR, _BTN_BORDER, _TITLE_COLOR, _TEXT_COLOR,
    _MUTED_COLOR, _GOLD_COLOR,
)


# Названия и бонусы 5 ступеней Грейда (индекс = ступень). Бонусы — для подсказки
# «к чему ты лезешь». Источник имён — единый с casino_view/HubView (держим в синхроне).
_GRADE_LABELS = (
    "L0 Onboarding",
    "L1 Первый PR",
    "L2 On-call",
    "L3 Архитектор",
    "L4 CTO",
)
_GRADE_BONUSES = (
    "доступ в казино",
    "keepsake + бесплатная крутка",
    "+1 перманент-бан казино",
    "хардкор-режим + бан тега в забеге",
    "маяк Демиурга",
)


# ─── Пур-хелперы (без pygame — тестируемы) ────────────────────────────────────

def catalog_rows(meta) -> list:
    """Строки каталога: по одной на каждую ачивку реестра, в порядке ACHIEVEMENTS.

    Каждая строка — dict {id, title, description, reward, kind, done}. `done`
    читается из meta['achievements'] (выполненные id). meta=None/пустой → всё
    заперто. Чистая функция: мету не мутирует, pygame не трогает."""
    done = set((meta or {}).get("achievements", []))
    rows = []
    for a in achievements.ACHIEVEMENTS:
        rows.append({
            "id":          a.id,
            "title":       a.title,
            "description": a.description,
            "reward":      a.grant_id,
            "kind":        a.grant_kind,        # 'card' | 'relic'
            "done":        a.id in done,
        })
    return rows


def progress_summary(meta):
    """Сводка прогресса ачивок: (выполнено, всего). Чистая функция."""
    rows = catalog_rows(meta)
    return sum(1 for r in rows if r["done"]), len(rows)


class AchievementsView:
    """Экран каталога достижений + лестница Грейда. Кнопка «Назад» в Лагерь."""

    def __init__(self):
        self.back_button: pygame.Rect | None = None

    def reset(self):
        self.back_button = None

    def draw(self, view):
        screen = view.screen
        gm     = view.gm
        meta   = getattr(gm, "meta", None) or {}
        mouse  = pygame.mouse.get_pos()

        screen.fill(_BG_COLOR)

        f_title = pygame.font.SysFont("Arial", 44, bold=True)
        f_hdr   = pygame.font.SysFont("Arial", 22, bold=True)
        f_txt   = pygame.font.SysFont("Arial", 19)
        f_small = pygame.font.SysFont("Arial", 16)

        # Заголовок + сводка X/6
        done_n, total_n = progress_summary(meta)
        t = f_title.render("=== ДОСТИЖЕНИЯ ===", True, _TITLE_COLOR)
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 50))
        sub = f_small.render(
            f"Выполняй условия — открывай контент под конкретный билд.   "
            f"Выполнено: {done_n} / {total_n}",
            True, _MUTED_COLOR)
        screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 104))

        self._draw_grade_ladder(screen, meta, f_hdr, f_txt, f_small)
        self._draw_achievements(screen, meta, f_hdr, f_txt, f_small)
        self._draw_back_button(screen, mouse)

    # --- Лестница Грейда с прогресс-баром ---

    def _draw_grade_ladder(self, screen, meta, f_hdr, f_txt, f_small):
        panel = pygame.Rect(SCREEN_W // 2 - 560, 140, 1120, 150)
        pygame.draw.rect(screen, _PANEL_COLOR, panel, border_radius=10)
        pygame.draw.rect(screen, _BTN_BORDER,  panel, 2, border_radius=10)

        grade   = meta_currency.current_grade(meta)
        gx      = int(meta.get("grade_xp", 0))
        nxt     = meta_currency.next_threshold(meta)
        to_next = meta_currency.xp_to_next(meta)

        screen.blit(f_hdr.render("ЛЕСТНИЦА ГРЕЙДА", True, _TEXT_COLOR),
                    (panel.x + 20, panel.y + 12))

        # Ряд из 5 ступеней-ячеек: достигнутые подсвечены, текущая — золотом.
        n     = len(_GRADE_LABELS)
        gap   = 12
        cell_w = (panel.width - 40 - gap * (n - 1)) // n
        cell_h = 46
        cy     = panel.y + 46
        for i, label in enumerate(_GRADE_LABELS):
            cx = panel.x + 20 + i * (cell_w + gap)
            cell = pygame.Rect(cx, cy, cell_w, cell_h)
            if i == grade:
                bg, border = (70, 60, 20), _GOLD_COLOR
            elif i < grade:
                bg, border = (30, 55, 30), (110, 200, 110)
            else:
                bg, border = (30, 30, 45), _BTN_BORDER
            pygame.draw.rect(screen, bg, cell, border_radius=8)
            pygame.draw.rect(screen, border, cell, 2, border_radius=8)
            col = _GOLD_COLOR if i == grade else _TEXT_COLOR if i < grade else _MUTED_COLOR
            ll = f_small.render(label, True, col)
            screen.blit(ll, (cell.centerx - ll.get_width() // 2,
                             cell.centery - ll.get_height() // 2))

        # Прогресс-бар накопления к следующей ступени.
        bar = pygame.Rect(panel.x + 20, panel.y + 104, panel.width - 40, 18)
        pygame.draw.rect(screen, (25, 25, 38), bar, border_radius=6)
        pygame.draw.rect(screen, _BTN_BORDER, bar, 1, border_radius=6)
        if nxt is None:
            # Потолок CTO: бар залит полностью.
            fill = pygame.Rect(bar.x, bar.y, bar.width, bar.height)
            pygame.draw.rect(screen, (110, 200, 110), fill, border_radius=6)
            line = "Достигнут потолок: L4 CTO — маяк Демиурга."
        else:
            cur_floor = meta_currency.GRADE_THRESHOLDS[grade]
            span      = max(1, nxt - cur_floor)
            frac      = max(0.0, min(1.0, (gx - cur_floor) / span))
            fill_w    = int(bar.width * frac)
            if fill_w > 0:
                fill = pygame.Rect(bar.x, bar.y, fill_w, bar.height)
                pygame.draw.rect(screen, _GOLD_COLOR, fill, border_radius=6)
            nxt_bonus = _GRADE_BONUSES[grade + 1] if grade + 1 < len(_GRADE_BONUSES) else "—"
            line = (f"Грейд-Опыт: {gx} / {nxt}   (до ступени {_GRADE_LABELS[grade + 1]}: "
                    f"{to_next})   •   Откроет: {nxt_bonus}")
        screen.blit(f_small.render(line, True, _MUTED_COLOR),
                    (panel.x + 20, panel.y + 126))

    # --- Список ачивок ---

    def _draw_achievements(self, screen, meta, f_hdr, f_txt, f_small):
        rows = catalog_rows(meta)
        top   = 312
        row_h = 96
        gap   = 12
        x     = SCREEN_W // 2 - 560
        w     = 1120
        for i, r in enumerate(rows):
            ry = top + i * (row_h + gap)
            rect = pygame.Rect(x, ry, w, row_h)
            done = r["done"]
            bg     = (28, 48, 30) if done else (24, 24, 40)
            border = (110, 200, 110) if done else _BTN_BORDER
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            pygame.draw.rect(screen, border, rect, 2, border_radius=10)

            # Бейдж статуса слева.
            badge_w = 150
            badge = pygame.Rect(rect.x + 16, rect.y + 28, badge_w, 40)
            if done:
                pygame.draw.rect(screen, (40, 90, 40), badge, border_radius=8)
                pygame.draw.rect(screen, (130, 230, 130), badge, 2, border_radius=8)
                bt = f_small.render("✓ ОТКРЫТО", True, (180, 255, 180))
            else:
                pygame.draw.rect(screen, (45, 40, 30), badge, border_radius=8)
                pygame.draw.rect(screen, _BTN_BORDER, badge, 2, border_radius=8)
                bt = f_small.render("ЗАПЕРТО", True, _MUTED_COLOR)
            screen.blit(bt, (badge.centerx - bt.get_width() // 2,
                             badge.centery - bt.get_height() // 2))

            tx = rect.x + 16 + badge_w + 20
            title_col = (235, 255, 235) if done else _TEXT_COLOR
            screen.blit(f_hdr.render(r["title"], True, title_col), (tx, rect.y + 12))
            screen.blit(f_txt.render(r["description"], True, _MUTED_COLOR),
                        (tx, rect.y + 44))

            kind_ru = "Карта" if r["kind"] == "card" else "Реликвия"
            rew = f_small.render(f"Награда: {kind_ru} «{r['reward']}»",
                                 True, _GOLD_COLOR)
            screen.blit(rew, (tx, rect.y + 70))

    # --- Назад ---

    def _draw_back_button(self, screen, mouse):
        rect = pygame.Rect(24, 20, 220, 40)
        hovered = rect.collidepoint(mouse)
        pygame.draw.rect(screen, (55, 55, 80) if hovered else (38, 38, 58),
                         rect, border_radius=8)
        pygame.draw.rect(screen, _BTN_BORDER, rect, 2, border_radius=8)
        bl = pygame.font.SysFont("Arial", 18, bold=True).render(
            "← НАЗАД В ЛАГЕРЬ", True, _TEXT_COLOR)
        screen.blit(bl, (rect.centerx - bl.get_width() // 2,
                         rect.centery - bl.get_height() // 2))
        self.back_button = rect

    def handle_click(self, view, mouse_pos):
        gm = view.gm
        if self.back_button and self.back_button.collidepoint(mouse_pos):
            gm.current_state = "HUB"
            return
