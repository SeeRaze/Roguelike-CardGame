import pygame

_BG         = (15, 20, 15)
_GOLD_C     = (255, 215, 0)
_WHITE      = (255, 255, 255)
_GREEN      = (80, 220, 100)
_GRAY       = (140, 140, 140)
_BTN_IDLE   = (50, 80, 50)
_BTN_HOV    = (70, 120, 70)
_BTN_DONE   = (40, 40, 40)
_BTN_ALL    = (30, 100, 60)
_BTN_ALL_H  = (50, 150, 90)
_BTN_CONT   = (60, 60, 100)
_BTN_CONT_H = (90, 90, 150)
_BORDER     = (100, 180, 100)
_MODAL_BG   = (20, 25, 20)
_BTN_YES    = (140, 40, 40)
_BTN_YES_H  = (200, 60, 60)
_BTN_NO     = (40, 80, 40)
_BTN_NO_H   = (60, 120, 60)


class VictoryScreen:
    """Статический класс — экран наград после победы в бою."""

    _claim_rects    = []
    _claim_all_rect = None
    _continue_rect  = None

    # Модальное окно подтверждения
    _show_modal  = False
    _modal_yes   = None
    _modal_no    = None

    # ------------------------------------------------------------------ #
    #  ОТРИСОВКА                                                           #
    # ------------------------------------------------------------------ #
    @classmethod
    def draw_screen(cls, view):
        screen  = view.screen
        W, H    = screen.get_size()
        rewards = view.gm.pending_rewards
        mouse   = pygame.mouse.get_pos()

        screen.fill(_BG)

        title_font = view.main_font
        body_font  = view.card_font
        small_font = view.card_desc_font

        # Заголовок
        title_surf = title_font.render("ПОБЕДА!", True, _GOLD_C)
        screen.blit(title_surf, (W // 2 - title_surf.get_width() // 2, 60))

        sub = small_font.render("Выберите награды или заберите все сразу", True, _GRAY)
        screen.blit(sub, (W // 2 - sub.get_width() // 2, 115))

        # Список наград
        cls._claim_rects = []
        panel_w = 700
        panel_x = W // 2 - panel_w // 2
        row_h   = 80
        start_y = 180

        for i, reward in enumerate(rewards):
            row_y    = start_y + i * row_h
            row_rect = pygame.Rect(panel_x, row_y, panel_w, row_h - 8)
            bg_color = (25, 35, 25) if not reward["applied"] else (20, 20, 20)
            pygame.draw.rect(screen, bg_color, row_rect, border_radius=8)
            pygame.draw.rect(screen,
                             _BORDER if not reward["applied"] else _GRAY,
                             row_rect, 1, border_radius=8)

            icon = {"gold": "ЗОЛОТО", "relic": "АРТЕФАКТ", "key": "КЛЮЧ"}.get(
                reward["type"], "НАГРАДА"
            )
            screen.blit(small_font.render(f"[{icon}]", True, _GOLD_C),
                        (panel_x + 16, row_y + row_h // 2 - 20))

            label_color = _WHITE if not reward["applied"] else _GRAY
            screen.blit(body_font.render(reward["label"], True, label_color),
                        (panel_x + 130, row_y + row_h // 2 - 14))

            btn_rect = pygame.Rect(panel_x + panel_w - 160, row_y + 14, 140, 44)
            if reward["applied"]:
                pygame.draw.rect(screen, _BTN_DONE, btn_rect, border_radius=6)
                btn_label = small_font.render("Получено", True, _GRAY)
            else:
                hov = btn_rect.collidepoint(mouse)
                pygame.draw.rect(screen, _BTN_HOV if hov else _BTN_IDLE,
                                 btn_rect, border_radius=6)
                pygame.draw.rect(screen, _GREEN, btn_rect, 1, border_radius=6)
                btn_label = small_font.render("Получить", True, _WHITE)

            screen.blit(btn_label,
                        (btn_rect.centerx - btn_label.get_width() // 2,
                         btn_rect.centery - btn_label.get_height() // 2))
            cls._claim_rects.append((btn_rect, i))

        # Кнопка "Получить все"
        all_y = start_y + len(rewards) * row_h + 20
        cls._claim_all_rect = pygame.Rect(W // 2 - 200, all_y, 400, 55)
        hov_all = cls._claim_all_rect.collidepoint(mouse)
        pygame.draw.rect(screen, _BTN_ALL_H if hov_all else _BTN_ALL,
                         cls._claim_all_rect, border_radius=8)
        pygame.draw.rect(screen, _GREEN, cls._claim_all_rect, 2, border_radius=8)
        all_lbl = body_font.render("Получить все", True, _WHITE)
        screen.blit(all_lbl, (cls._claim_all_rect.centerx - all_lbl.get_width() // 2,
                               cls._claim_all_rect.centery - all_lbl.get_height() // 2))

        # Кнопка "Продолжить"
        cont_y = all_y + 80
        cls._continue_rect = pygame.Rect(W // 2 - 200, cont_y, 400, 60)
        hov_cont = cls._continue_rect.collidepoint(mouse)
        pygame.draw.rect(screen, _BTN_CONT_H if hov_cont else _BTN_CONT,
                         cls._continue_rect, border_radius=8)
        pygame.draw.rect(screen, (150, 150, 220), cls._continue_rect, 2, border_radius=8)
        cont_lbl = body_font.render("Продолжить ->", True, _WHITE)
        screen.blit(cont_lbl, (cls._continue_rect.centerx - cont_lbl.get_width() // 2,
                                cls._continue_rect.centery - cont_lbl.get_height() // 2))

        # Модальное окно поверх всего
        if cls._show_modal:
            cls._draw_modal(screen, W, H, body_font, small_font, mouse)

    @classmethod
    def _draw_modal(cls, screen, W, H, body_font, small_font, mouse):
        # Затемнение фона
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Окно
        mw, mh  = 480, 220
        mx      = W // 2 - mw // 2
        my      = H // 2 - mh // 2
        modal   = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(screen, _MODAL_BG, modal, border_radius=12)
        pygame.draw.rect(screen, (180, 180, 100), modal, 2, border_radius=12)

        # Текст
        q_surf = body_font.render("Пропустить награду?", True, _GOLD_C)
        screen.blit(q_surf, (mx + mw // 2 - q_surf.get_width() // 2, my + 40))

        hint = small_font.render("Неполученные награды будут потеряны", True, _GRAY)
        screen.blit(hint, (mx + mw // 2 - hint.get_width() // 2, my + 85))

        # Кнопка "Да"
        cls._modal_yes = pygame.Rect(mx + 60, my + 135, 160, 50)
        hov_yes = cls._modal_yes.collidepoint(mouse)
        pygame.draw.rect(screen, _BTN_YES_H if hov_yes else _BTN_YES,
                         cls._modal_yes, border_radius=8)
        pygame.draw.rect(screen, (220, 80, 80), cls._modal_yes, 1, border_radius=8)
        yes_lbl = body_font.render("Да", True, _WHITE)
        screen.blit(yes_lbl, (cls._modal_yes.centerx - yes_lbl.get_width() // 2,
                               cls._modal_yes.centery - yes_lbl.get_height() // 2))

        # Кнопка "Нет"
        cls._modal_no = pygame.Rect(mx + 260, my + 135, 160, 50)
        hov_no = cls._modal_no.collidepoint(mouse)
        pygame.draw.rect(screen, _BTN_NO_H if hov_no else _BTN_NO,
                         cls._modal_no, border_radius=8)
        pygame.draw.rect(screen, _GREEN, cls._modal_no, 1, border_radius=8)
        no_lbl = body_font.render("Нет", True, _WHITE)
        screen.blit(no_lbl, (cls._modal_no.centerx - no_lbl.get_width() // 2,
                              cls._modal_no.centery - no_lbl.get_height() // 2))

    # ------------------------------------------------------------------ #
    #  КЛИКИ                                                               #
    # ------------------------------------------------------------------ #
    @classmethod
    def handle_clicks(cls, view, mouse_pos):
        # Если модалка открыта — обрабатываем только её
        if cls._show_modal:
            if cls._modal_yes and cls._modal_yes.collidepoint(mouse_pos):
                cls._show_modal = False
                cls._proceed(view)
            elif cls._modal_no and cls._modal_no.collidepoint(mouse_pos):
                cls._show_modal = False
            return

        rewards = view.gm.pending_rewards

        for rect, idx in cls._claim_rects:
            if rect.collidepoint(mouse_pos) and not rewards[idx]["applied"]:
                cls._apply_reward(view.gm, rewards[idx])
                return

        if cls._claim_all_rect and cls._claim_all_rect.collidepoint(mouse_pos):
            for reward in rewards:
                if not reward["applied"]:
                    cls._apply_reward(view.gm, reward)
            return

        if cls._continue_rect and cls._continue_rect.collidepoint(mouse_pos):
            has_unclaimed = any(not r["applied"] for r in rewards)
            if has_unclaimed:
                cls._show_modal = True   # открываем модалку
            else:
                cls._proceed(view)       # всё забрано — сразу идём дальше

    # ------------------------------------------------------------------ #
    #  ВНУТРЕННИЕ МЕТОДЫ                                                   #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _apply_reward(gm, reward):
        if reward["type"] == "gold":
            gm.player_gold += reward["value"]
        elif reward["type"] == "relic":
            gm.relics.append(reward["value"])
        elif reward["type"] == "key":
            gm.player_keys += reward["value"]
        reward["applied"] = True

    @staticmethod
    def _proceed(view):
        VictoryScreen._show_modal      = False
        view.gm.pending_rewards        = []
        view.gm.current_floor         += 1
        view.scroll_y                  = 0
        view.gm.setup_next_floor()