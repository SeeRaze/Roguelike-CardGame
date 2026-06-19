# ui/hub/casino_view.py
# Экран казино мета-прогрессии (С70 Этап 4). Простой MVP: баланс Опыта и Грейда
# + большая кнопка «Крутить» + поле результата последней крутки + список
# выкрученного (история сессии) + кнопка «Назад». Полировка/анимации позже.
#
# Состояние gm.current_state == "CASINO". Регистрируется в DRAW_HANDLERS / клик-
# диспетчере (GameView.py). Только UI — вся логика крутки в core/casino.py.

import pygame

from core import casino, meta_currency
from ui.hub.data import (
    SCREEN_W,
    _BG_COLOR, _PANEL_COLOR, _BTN_BORDER, _TITLE_COLOR, _TEXT_COLOR,
    _MUTED_COLOR, _GOLD_COLOR, _START_COLOR, _START_HOVER,
)


_GRADE_LABELS = (
    "L0 Onboarding",
    "L1 Первый PR в прод",
    "L2 On-call дежурный",
    "L3 Архитектор",
    "L4 CTO",
)


class CasinoView:
    """Экран казино: крутка, баланс, последняя выдача, история сессии."""

    def __init__(self):
        self.last_result: dict | None = None       # последний try_spin результат
        self.session_log: list = []                # ['card:steel_barricade', ...]
        self.spin_button: pygame.Rect | None = None
        self.back_button: pygame.Rect | None = None

    def reset(self):
        self.last_result = None
        self.session_log = []

    def draw(self, view):
        screen = view.screen
        gm     = view.gm
        meta   = getattr(gm, "meta", None) or {}
        mouse  = pygame.mouse.get_pos()

        screen.fill(_BG_COLOR)

        f_title = pygame.font.SysFont("Arial", 44, bold=True)
        f_hdr   = pygame.font.SysFont("Arial", 24, bold=True)
        f_txt   = pygame.font.SysFont("Arial", 20)
        f_small = pygame.font.SysFont("Arial", 17)

        # Заголовок
        t = f_title.render("=== КАЗИНО ===", True, _TITLE_COLOR)
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 60))

        sub = f_small.render(
            "Опыт за забеги — рандом-крутка залоченного контента. Без дублей.",
            True, _MUTED_COLOR)
        screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 110))

        # Панель баланса
        bal_panel = pygame.Rect(SCREEN_W // 2 - 380, 150, 760, 110)
        pygame.draw.rect(screen, _PANEL_COLOR, bal_panel, border_radius=10)
        pygame.draw.rect(screen, _BTN_BORDER,  bal_panel, 2, border_radius=10)

        xp        = int(meta.get("xp", 0))
        grade_xp  = int(meta.get("grade_xp", 0))
        grade     = meta_currency.current_grade(meta)
        nxt       = meta_currency.next_threshold(meta)
        to_next   = meta_currency.xp_to_next(meta)
        grade_lbl = _GRADE_LABELS[grade] if grade < len(_GRADE_LABELS) else "L?"

        screen.blit(f_hdr.render(f"Опыт: {xp}", True, _GOLD_COLOR),
                    (bal_panel.x + 20, bal_panel.y + 14))
        screen.blit(f_hdr.render(f"Грейд: {grade_lbl}", True, _TEXT_COLOR),
                    (bal_panel.x + 220, bal_panel.y + 14))

        if nxt is None:
            grade_line = "До следующего грейда: —  (потолок CTO)"
        else:
            grade_line = (f"Накоплено Грейд-Опыта: {grade_xp} / {nxt}  "
                          f"(до следующей ступени: {to_next})")
        screen.blit(f_txt.render(grade_line, True, _MUTED_COLOR),
                    (bal_panel.x + 20, bal_panel.y + 54))

        # Размер пула / бан-капасити
        pool_size = len(casino.available_pool(meta))
        bans_used = len(meta.get("casino_bans", []))
        bans_cap  = casino.bans_capacity(meta)
        info_line = (f"В пуле осталось предметов: {pool_size}  •  "
                     f"Перманент-баны: {bans_used}/{bans_cap}")
        screen.blit(f_small.render(info_line, True, _MUTED_COLOR),
                    (bal_panel.x + 20, bal_panel.y + 80))

        # Большая кнопка крутки
        spin_w, spin_h = 360, 80
        spin_rect = pygame.Rect(SCREEN_W // 2 - spin_w // 2, 300, spin_w, spin_h)
        can_spin  = xp >= meta_currency.CASINO_SPIN_COST and pool_size > 0
        hovered   = spin_rect.collidepoint(mouse)
        if not can_spin:
            colour = (60, 60, 70)
        elif hovered:
            colour = _START_HOVER
        else:
            colour = _START_COLOR
        pygame.draw.rect(screen, colour, spin_rect, border_radius=14)
        pygame.draw.rect(screen, (100, 220, 100) if can_spin else _BTN_BORDER,
                         spin_rect, 2, border_radius=14)
        cost = meta_currency.CASINO_SPIN_COST
        lbl = f"КРУТИТЬ ({cost} Опыта)" if can_spin else "КРУТИТЬ — недоступно"
        rl = pygame.font.SysFont("Arial", 28, bold=True).render(
            lbl, True, (255, 255, 255))
        screen.blit(rl, (spin_rect.centerx - rl.get_width() // 2,
                         spin_rect.centery - rl.get_height() // 2))
        self.spin_button = spin_rect

        # Подсказка под кнопкой
        if not can_spin:
            if pool_size == 0:
                reason = "Пул выкручен полностью — больше нечего открывать."
            else:
                reason = f"Нужно ещё {cost - xp} Опыта на одну крутку."
            hint = f_small.render(reason, True, _MUTED_COLOR)
            screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2,
                               spin_rect.bottom + 8))

        # Последний результат
        res_panel = pygame.Rect(SCREEN_W // 2 - 380, 430, 760, 90)
        pygame.draw.rect(screen, _PANEL_COLOR, res_panel, border_radius=10)
        pygame.draw.rect(screen, _BTN_BORDER,  res_panel, 2, border_radius=10)
        screen.blit(f_hdr.render("Последний выигрыш:", True, _TEXT_COLOR),
                    (res_panel.x + 20, res_panel.y + 12))
        if self.last_result and self.last_result.get("ok"):
            kind = self.last_result["kind"]
            item = self.last_result["id"]
            kind_ru = "Карта" if kind == "card" else "Реликвия"
            line = f"{kind_ru}: {item}"
            screen.blit(f_hdr.render(line, True, _GOLD_COLOR),
                        (res_panel.x + 20, res_panel.y + 46))
        elif self.last_result and self.last_result.get("reason"):
            reasons = {
                "not_enough_xp": "Недостаточно Опыта.",
                "pool_empty":    "Пул казино пуст.",
                "no_meta":       "Нет меты сейва.",
            }
            r = reasons.get(self.last_result["reason"], "—")
            screen.blit(f_txt.render(r, True, (220, 110, 110)),
                        (res_panel.x + 20, res_panel.y + 48))
        else:
            screen.blit(f_txt.render("—", True, _MUTED_COLOR),
                        (res_panel.x + 20, res_panel.y + 48))

        # История сессии (последние 10)
        log_panel = pygame.Rect(SCREEN_W // 2 - 380, 540, 760, 220)
        pygame.draw.rect(screen, _PANEL_COLOR, log_panel, border_radius=10)
        pygame.draw.rect(screen, _BTN_BORDER,  log_panel, 2, border_radius=10)
        screen.blit(f_hdr.render("История сессии:", True, _TEXT_COLOR),
                    (log_panel.x + 20, log_panel.y + 12))
        if not self.session_log:
            screen.blit(f_txt.render("Ещё ничего не крутили в этой сессии.",
                                     True, _MUTED_COLOR),
                        (log_panel.x + 20, log_panel.y + 48))
        else:
            for i, line in enumerate(self.session_log[-9:]):
                screen.blit(f_small.render(line, True, _TEXT_COLOR),
                            (log_panel.x + 20, log_panel.y + 48 + i * 19))

        # Кнопка «Назад»
        back_rect = pygame.Rect(24, 20, 220, 40)
        bhover = back_rect.collidepoint(mouse)
        pygame.draw.rect(screen, (55, 55, 80) if bhover else (38, 38, 58),
                         back_rect, border_radius=8)
        pygame.draw.rect(screen, _BTN_BORDER, back_rect, 2, border_radius=8)
        bl = pygame.font.SysFont("Arial", 18, bold=True).render(
            "← НАЗАД В ЛАГЕРЬ", True, _TEXT_COLOR)
        screen.blit(bl, (back_rect.centerx - bl.get_width() // 2,
                         back_rect.centery - bl.get_height() // 2))
        self.back_button = back_rect

    def handle_click(self, view, mouse_pos):
        gm = view.gm
        if self.back_button and self.back_button.collidepoint(mouse_pos):
            gm.current_state = "HUB"
            return
        if self.spin_button and self.spin_button.collidepoint(mouse_pos):
            res = casino.try_spin(gm.meta)
            self.last_result = res
            if res.get("ok"):
                kind_ru = "Карта" if res["kind"] == "card" else "Реликвия"
                self.session_log.append(f"{kind_ru}: {res['id']}")
                # Сразу на диск (как DEV-тоггл): крутка ценная, не теряем при крэше.
                from managers import SaveManager
                SaveManager.save()
            return
