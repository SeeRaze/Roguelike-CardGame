# ui/hub/base.py
# Оркестратор Мета-Хаба: состояние анимации, отрисовка, обработка кликов.
import pygame
from ui.hub.data import (
    ANIM_SPEED, SCREEN_W, SCREEN_H,
    _BG_COLOR, _TITLE_COLOR, _GOLD_COLOR, _BTN_BORDER, _START_COLOR, _START_HOVER,
    _MUTED_COLOR, _TEXT_COLOR,
)
from ui.hub.selectors import draw_class_selector
from ui.hub.deck import draw_deck_section
from ui.hub.data import CLASS_INFO


class HubView:
    """Отрисовка и логика Мета-Хаба: выбор класса + анимированная стопка карт."""

    def __init__(self):
        self.hover_progress:   float = 0.0
        self.is_deck_hovered:  bool  = False
        self.class_buttons:    dict  = {}
        self.stake_buttons:    dict  = {}
        self.dev_button              = None
        self.casino_button           = None      # С70 Этап 4: вход в казино
        self.ach_button              = None      # С70 полировка: вход в каталог достижений
        self.is_start_hovered: bool  = False

    def reset(self):
        self.hover_progress   = 0.0
        self.is_deck_hovered  = False
        self.is_start_hovered = False

    def update(self, dt: float):
        target = 1.0 if self.is_deck_hovered else 0.0
        step   = ANIM_SPEED * dt
        if self.hover_progress < target:
            self.hover_progress = min(self.hover_progress + step, 1.0)
        elif self.hover_progress > target:
            self.hover_progress = max(self.hover_progress - step, 0.0)

    # --- ОТРИСОВКА ---

    def draw(self, view):
        screen    = view.screen
        gm        = view.gm
        mouse_pos = pygame.mouse.get_pos()

        screen.fill(_BG_COLOR)

        font_title = pygame.font.SysFont("Arial", 42, bold=True)
        font_gold  = pygame.font.SysFont("Arial", 26, bold=True)
        font_hint  = pygame.font.SysFont("Arial", 22)

        # Заголовок
        t = font_title.render("=== ВАШ ЛАГЕРЬ ===", True, _TITLE_COLOR)
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 50))

        # Золото
        g = font_gold.render(f"Золото: {gm.player_gold}", True, _GOLD_COLOR)
        screen.blit(g, (SCREEN_W // 2 - g.get_width() // 2, 108))

        # Разделитель под заголовком
        pygame.draw.line(screen, _BTN_BORDER,
                         (SCREEN_W // 2 - 400, 148),
                         (SCREEN_W // 2 + 400, 148), 1)

        self.class_buttons   = draw_class_selector(screen, gm, mouse_pos)
        self.is_deck_hovered = draw_deck_section(
            view, screen, gm, mouse_pos, font_hint, self.hover_progress
        )
        self._draw_meta_stats(screen, gm)
        self._draw_stake_toggles(screen, gm)
        self._draw_dev_toggle(screen, gm)
        self._draw_casino_button(screen, gm, mouse_pos)
        self._draw_achievements_button(screen, gm, mouse_pos)
        self._draw_grade_panel(screen, gm)
        self._draw_menu_button(screen, mouse_pos)
        self._draw_start_button(view, screen, mouse_pos)

    def _draw_menu_button(self, screen, mouse_pos):
        """Кнопка «В главное меню» (левый верх Хаба). Забег ещё не начат → просто
        смена состояния, ничего сохранять не нужно."""
        font = pygame.font.SysFont("Arial", 18, bold=True)
        rect = pygame.Rect(24, 20, 220, 40)
        hovered = rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (55, 55, 80) if hovered else (38, 38, 58),
                         rect, border_radius=8)
        pygame.draw.rect(screen, _BTN_BORDER, rect, 2, border_radius=8)
        lbl = font.render("← В ГЛАВНОЕ МЕНЮ", True, _TEXT_COLOR)
        screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                          rect.centery - lbl.get_height() // 2))
        self.menu_button = rect

    def _draw_dev_toggle(self, screen, gm):
        """DEV-тоггл «полный доступ»: открывает ВЕСЬ пул карт/артефактов (минуя анлоки)
        для тест-сессий, пока анлок-слой (казино/достижения) не построен. Пишет
        meta['dev_unlock_all'] (персист через SaveManager). Служебная кнопка в углу,
        помечена DEV — НЕ часть игрового цикла; перед релизом скрыть/убрать."""
        meta = getattr(gm, "meta", None)
        if meta is None:
            return
        font = pygame.font.SysFont("Arial", 16, bold=True)
        on = bool(meta.get("dev_unlock_all", False))
        btn_w, btn_h = 240, 34
        rect = pygame.Rect(SCREEN_W - btn_w - 20, 20, btn_w, btn_h)
        pygame.draw.rect(screen, (110, 70, 30) if on else (45, 35, 25),
                         rect, border_radius=6)
        pygame.draw.rect(screen, (220, 160, 60) if on else _BTN_BORDER,
                         rect, 2, border_radius=6)
        mark = "[+]" if on else "[ ]"
        t = font.render(f"{mark} DEV: полный доступ", True, _TEXT_COLOR)
        screen.blit(t, (rect.centerx - t.get_width() // 2,
                        rect.centery - t.get_height() // 2))
        self.dev_button = rect

    def _draw_casino_button(self, screen, gm, mouse_pos):
        """Вход в казино мета-прогрессии (С70 Этап 4). Свободное место — под
        DEV-тогглом в правом верхнем углу. Полировка позиции/стиля позже."""
        from core import meta_currency
        meta = getattr(gm, "meta", None)
        if meta is None:
            return
        font_lbl = pygame.font.SysFont("Arial", 16, bold=True)
        font_sub = pygame.font.SysFont("Arial", 14)
        btn_w, btn_h = 240, 50
        rect = pygame.Rect(SCREEN_W - btn_w - 20, 64, btn_w, btn_h)
        hovered = rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (60, 80, 110) if hovered else (40, 55, 80),
                         rect, border_radius=6)
        pygame.draw.rect(screen, (140, 180, 240), rect, 2, border_radius=6)
        t1 = font_lbl.render("КАЗИНО", True, _TITLE_COLOR)
        screen.blit(t1, (rect.centerx - t1.get_width() // 2, rect.y + 6))
        xp   = int(meta.get("xp", 0))
        cost = meta_currency.CASINO_SPIN_COST
        t2 = font_sub.render(f"Опыт: {xp}  •  Крутка: {cost}", True, _TEXT_COLOR)
        screen.blit(t2, (rect.centerx - t2.get_width() // 2, rect.y + 28))
        self.casino_button = rect

    def _draw_achievements_button(self, screen, gm, mouse_pos):
        """Вход в каталог достижений (С70 полировка). Под кнопкой казино в правом
        верхнем углу. Показывает прогресс X/6 — приманка зайти и посмотреть цели."""
        meta = getattr(gm, "meta", None)
        if meta is None:
            return
        from ui.hub.achievements_view import progress_summary
        done_n, total_n = progress_summary(meta)
        font_lbl = pygame.font.SysFont("Arial", 16, bold=True)
        font_sub = pygame.font.SysFont("Arial", 14)
        btn_w, btn_h = 240, 50
        rect = pygame.Rect(SCREEN_W - btn_w - 20, 122, btn_w, btn_h)
        hovered = rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (60, 90, 60) if hovered else (40, 65, 40),
                         rect, border_radius=6)
        pygame.draw.rect(screen, (150, 220, 150), rect, 2, border_radius=6)
        t1 = font_lbl.render("ДОСТИЖЕНИЯ", True, _TITLE_COLOR)
        screen.blit(t1, (rect.centerx - t1.get_width() // 2, rect.y + 6))
        t2 = font_sub.render(f"Выполнено: {done_n} / {total_n}", True, _TEXT_COLOR)
        screen.blit(t2, (rect.centerx - t2.get_width() // 2, rect.y + 28))
        self.ach_button = rect

    def _draw_grade_panel(self, screen, gm):
        """Компактная панель статуса Грейда у заголовка Хаба — игрок видит
        прогресс лестницы, не заходя в казино. С70 Этап 4."""
        from core import meta_currency
        meta = getattr(gm, "meta", None)
        if meta is None:
            return
        font_h = pygame.font.SysFont("Arial", 18, bold=True)
        font_v = pygame.font.SysFont("Arial", 16)
        grade  = meta_currency.current_grade(meta)
        labels = (
            "L0 Onboarding", "L1 Первый PR", "L2 On-call",
            "L3 Архитектор", "L4 CTO",
        )
        lbl_text = labels[grade] if grade < len(labels) else "L?"
        gx       = int(meta.get("grade_xp", 0))
        nxt      = meta_currency.next_threshold(meta)

        # Слева под «В главное меню» — свободная полоса.
        x, y = 24, 70
        screen.blit(font_h.render(f"Грейд: {lbl_text}", True, _TITLE_COLOR), (x, y))
        if nxt is None:
            line = f"Грейд-Опыт: {gx} (потолок)"
        else:
            line = f"Грейд-Опыт: {gx} / {nxt}"
        screen.blit(font_v.render(line, True, _TEXT_COLOR), (x, y + 24))

    def _draw_stake_toggles(self, screen, gm):
        """Ряд тогглов Ставок (опт-ин сложность поверх RuleStack). Клик переключает
        выбор в gm.pending_stakes; применяются на старте забега. Свободная полоса
        между «Хроникой странника» и кнопкой старта."""
        from core.rules import STAKES
        from core import meta_currency
        self.stake_buttons = {}
        font_lbl = pygame.font.SysFont("Arial", 20, bold=True)
        font_btn = pygame.font.SysFont("Arial", 18, bold=True)

        cx = SCREEN_W // 2
        y  = 866
        btn_w, btn_h, gap = 300, 40, 24

        lbl = font_lbl.render("СТАВКИ (необязательно — риск ради награды):",
                              True, _MUTED_COLOR)
        screen.blit(lbl, (cx - lbl.get_width() // 2, y - 30))

        # Гейт по Грейду: Ставки с min_grade выше текущего Грейда не показываем
        # (Восхождение/хардкор откроется на L3). Остальные — всегда.
        grade = meta_currency.current_grade(getattr(gm, "meta", None))
        items = [st for st in STAKES.values()
                 if getattr(st, "min_grade", 0) <= grade]
        total = len(items) * btn_w + (len(items) - 1) * gap
        x0 = cx - total // 2
        pending = getattr(gm, "pending_stakes", [])
        for i, st in enumerate(items):
            rect = pygame.Rect(x0 + i * (btn_w + gap), y, btn_w, btn_h)
            on = st.id in pending
            pygame.draw.rect(screen, (60, 110, 60) if on else (40, 40, 60),
                             rect, border_radius=8)
            pygame.draw.rect(screen, (120, 220, 120) if on else _BTN_BORDER,
                             rect, 2, border_radius=8)
            mark = "[+]" if on else "[ ]"
            t = font_btn.render(f"{mark} {st.name}", True, _TEXT_COLOR)
            screen.blit(t, (rect.centerx - t.get_width() // 2,
                            rect.centery - t.get_height() // 2))
            self.stake_buttons[st.id] = rect

    def _draw_meta_stats(self, screen, gm):
        """«Игра помнит тебя»: пожизненные статы из меты (Сессия 40). Панель в
        свободной зоне между колодой и кнопкой старта. Инертна без меты."""
        meta = getattr(gm, "meta", None)
        if not meta:
            return
        s = meta.get("stats", {})

        font_h = pygame.font.SysFont("Arial", 22, bold=True)
        font_v = pygame.font.SysFont("Arial", 20)

        # Заголовок-разделитель
        title = font_h.render("— ХРОНИКА СТРАННИКА —", True, _MUTED_COLOR)
        cx = SCREEN_W // 2
        top = 752
        screen.blit(title, (cx - title.get_width() // 2, top))

        # Пожизненные статы одной строкой (компактно, по центру)
        parts = [
            f"Забегов: {s.get('total_runs', 0)}",
            f"Лучший этаж: {s.get('best_floor', 0)}",
            f"Всего убийств: {s.get('total_kills', 0)}",
            f"Боссов: {s.get('total_bosses', 0)}",
            f"Рекорд урона: {s.get('max_damage_ever', 0)}",
        ]
        line = font_v.render("   •   ".join(parts), True, _TEXT_COLOR)
        screen.blit(line, (cx - line.get_width() // 2, top + 34))

        # Лучший результат текущего выбранного класса (если уже играл им)
        cls_name = type(gm.player).__name__
        cb = meta.get("class_best", {}).get(cls_name)
        if cb:
            label = CLASS_INFO.get(cls_name, {}).get("label", cls_name)
            best = font_v.render(
                f"{label}: лучший этаж {cb.get('best_floor', 0)}, "
                f"забегов {cb.get('runs', 0)}",
                True, _TEXT_COLOR,
            )
            screen.blit(best, (cx - best.get_width() // 2, top + 66))

    def _draw_start_button(self, view, screen, mouse_pos):
        btn_w, btn_h = 520, 72
        bx = SCREEN_W // 2 - btn_w // 2
        by = SCREEN_H - 120
        btn = pygame.Rect(bx, by, btn_w, btn_h)
        view.btn_start_run    = btn
        self.is_start_hovered = btn.collidepoint(mouse_pos)

        color = _START_HOVER if self.is_start_hovered else _START_COLOR
        pygame.draw.rect(screen, color,           btn, border_radius=12)
        pygame.draw.rect(screen, (100, 220, 100), btn, 2, border_radius=12)

        font_btn = pygame.font.SysFont("Arial", 26, bold=True)
        lbl = font_btn.render("ПОДНЯТЬСЯ В БАШНЮ  [В БОЙ]", True, (255, 255, 255))
        screen.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                          btn.centery - lbl.get_height() // 2))

    # --- КЛИКИ ---

    def handle_click(self, view, mouse_pos):
        gm = view.gm

        # Кнопка «В главное меню» (забег не начат — просто смена состояния).
        mbtn = getattr(self, "menu_button", None)
        if mbtn is not None and mbtn.collidepoint(mouse_pos):
            gm.current_state = "MAIN_MENU"
            return

        for cls_name, rect in self.class_buttons.items():
            if rect.collidepoint(mouse_pos):
                self._select_class(gm, cls_name)
                return

        # Тогглы Ставок (опт-ин сложность): клик переключает выбор в gm.pending_stakes.
        for stake_id, rect in getattr(self, "stake_buttons", {}).items():
            if rect.collidepoint(mouse_pos):
                if stake_id in gm.pending_stakes:
                    gm.pending_stakes.remove(stake_id)
                else:
                    gm.pending_stakes.append(stake_id)
                return

        # Вход в казино (С70 Этап 4).
        cas_rect = getattr(self, "casino_button", None)
        if cas_rect is not None and cas_rect.collidepoint(mouse_pos):
            gm.current_state = "CASINO"
            return

        # Вход в каталог достижений (С70 полировка).
        ach_rect = getattr(self, "ach_button", None)
        if ach_rect is not None and ach_rect.collidepoint(mouse_pos):
            gm.current_state = "ACHIEVEMENTS"
            return

        # DEV-тоггл полного доступа: переключает meta['dev_unlock_all'] + персист.
        dev_rect = getattr(self, "dev_button", None)
        if dev_rect is not None and dev_rect.collidepoint(mouse_pos):
            meta = getattr(gm, "meta", None)
            if meta is not None:
                meta["dev_unlock_all"] = not meta.get("dev_unlock_all", False)
                from managers import SaveManager
                SaveManager.save()
                print(f"[DEV] Полный доступ: {meta['dev_unlock_all']}")
            return

        if hasattr(view, 'btn_start_run') and \
                view.btn_start_run.collidepoint(mouse_pos):
            print(f" >>> СТАРТ ЗАБЕГА | Класс: {type(gm.player).__name__} <<<")
            # Новый забег обнуляет старый сохранённый снимок.
            from managers import RunSave
            RunSave.clear_run()
            self.reset()
            gm.current_floor = 1
            # Чистим RuleStack от модов прошлого забега ДО активации Ставок —
            # иначе Ставки одной сессии копились бы (двойное применение). clear()
            # для этого и задуман («новый забег / сброс»), просто не был вшит.
            gm.rulestack.clear()
            # Ставки применяются ДО хила — Хрупкость должна успеть урезать макс. HP.
            gm.activate_pending_stakes()
            # keepsake (L1 Грейд): надеть выбранную реликвию в инвентарь забега.
            # Дубль-гард по классу внутри apply_to_run. Эффект сработает на старте боя.
            from core import keepsake
            kid = keepsake.apply_to_run(gm)
            if kid is not None:
                print(f"[keepsake] Надета реликвия: {kid}")
            gm.player.hp     = gm.player.max_hp
            gm.setup_next_floor()

    @staticmethod
    def _select_class(gm, cls_name: str):
        from core.players import (
            Warrior, Mage, Berserker, Chemist,
        )
        CLASS_MAP = {
            "Warrior":   Warrior,
            "Mage":      Mage,
            "Berserker": Berserker,
            "Chemist":   Chemist,
        }
        if cls_name not in CLASS_MAP:
            return
        # Гейт яруса (С50): залоченный класс яруса 2 нельзя выбрать.
        from core import progression
        if not progression.is_unlocked(getattr(gm, "meta", None), cls_name):
            print(f"[HubView] Класс {cls_name} заблокирован — нужен анлок")
            return
        if type(gm.player).__name__ == cls_name:
            return
        gm.player       = CLASS_MAP[cls_name]()
        gm.current_deck = gm.player.get_starter_deck()
        # Паспорт ковки: новый игрок/колода создаются МИНУЯ GameManager.__init__,
        # поэтому штампуем uid здесь — иначе ковка на костре молча не сработает
        # (forge_card_one_level подстрахован ленивой штамповкой, но держим uid
        # стабильными сразу, как при старте). 39.5 хотфикс.
        from core.forge import assign_forge_uid
        for card in gm.current_deck:
            assign_forge_uid(gm.player, card)
        print(f"[HubView] Выбран класс: {cls_name}")
