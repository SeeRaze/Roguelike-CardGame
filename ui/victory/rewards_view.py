# ui/victory/rewards_view.py
# Отрисовка списка наград + кнопки «Получить все» / «Продолжить».
import pygame
from ui.victory.data import (
    _GOLD_C, _WHITE, _GREEN, _GRAY, _BTN_IDLE, _BTN_HOV, _BTN_DONE,
    _BTN_ALL, _BTN_ALL_H, _BTN_CONT, _BTN_CONT_H, _BORDER,
)


def draw_rewards(vs, view, screen, fonts, mouse, panel_y=0):
    """Рисует заголовок, строки наград и кнопки. Заполняет vs._claim_rects/_hovered_relic/
    _claim_all_rect/_continue_rect. Вся раскладка отсчитывается от panel_y (верх
    модальной панели-оверлея), чтобы содержимое жило внутри окна, а не во весь экран."""
    W, _H = screen.get_size()
    title_font, body_font, small_font = fonts["title"], fonts["body"], fonts["small"]
    rewards = view.gm.pending_rewards

    # Заголовок
    title_surf = title_font.render("ПОБЕДА!", True, _GOLD_C)
    screen.blit(title_surf, (W // 2 - title_surf.get_width() // 2, panel_y + 24))
    sub = small_font.render("Выберите награды или заберите все сразу", True, _GRAY)
    screen.blit(sub, (W // 2 - sub.get_width() // 2, panel_y + 78))

    vs._claim_rects   = []
    vs._hovered_relic = None   # сбрасываем каждый кадр

    panel_w = 700
    panel_x = W // 2 - panel_w // 2
    row_h   = 80
    start_y = panel_y + 130

    # Пустой список наград — легитимный случай (напр. «Марш смерти» убирает золото,
    # а реликвия не выпала / пул исчерпан). Без заглушки окно выглядело бы багнутым-пустым.
    if not rewards:
        empty_rect = pygame.Rect(panel_x, start_y, panel_w, row_h - 8)
        pygame.draw.rect(screen, (25, 25, 30), empty_rect, border_radius=8)
        pygame.draw.rect(screen, _GRAY, empty_rect, 1, border_radius=8)
        msg = body_font.render("Наград нет — победа без трофеев.", True, _GRAY)
        screen.blit(msg, (empty_rect.centerx - msg.get_width() // 2,
                          empty_rect.centery - msg.get_height() // 2))

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
        label_surf  = body_font.render(reward["label"], True, label_color)
        label_x     = panel_x + 130
        label_y     = row_y + row_h // 2 - 14
        screen.blit(label_surf, (label_x, label_y))

        # Сохраняем rect реликвии для тултипа
        if reward["type"] == "relic" and not reward["applied"]:
            relic_rect = pygame.Rect(
                label_x, label_y,
                label_surf.get_width(), label_surf.get_height()
            )
            if relic_rect.collidepoint(mouse):
                vs._hovered_relic = (relic_rect, reward["value"])

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
        vs._claim_rects.append((btn_rect, i))

    # Кнопка "Получить все" — только когда есть что забирать (пустой список → скрыта).
    # Раскладка кнопок отсчитывается минимум от одной строки (заглушка тоже занимает ряд).
    rows_shown = max(len(rewards), 1)
    all_y = start_y + rows_shown * row_h + 20
    if rewards:
        vs._claim_all_rect = pygame.Rect(W // 2 - 200, all_y, 400, 55)
        hov_all = vs._claim_all_rect.collidepoint(mouse)
        pygame.draw.rect(screen, _BTN_ALL_H if hov_all else _BTN_ALL,
                         vs._claim_all_rect, border_radius=8)
        pygame.draw.rect(screen, _GREEN, vs._claim_all_rect, 2, border_radius=8)
        all_lbl = body_font.render("Получить все", True, _WHITE)
        screen.blit(all_lbl, (vs._claim_all_rect.centerx - all_lbl.get_width() // 2,
                              vs._claim_all_rect.centery - all_lbl.get_height() // 2))
    else:
        vs._claim_all_rect = None

    # Кнопка "Продолжить"
    cont_y = all_y + 80
    vs._continue_rect = pygame.Rect(W // 2 - 200, cont_y, 400, 60)
    hov_cont = vs._continue_rect.collidepoint(mouse)
    pygame.draw.rect(screen, _BTN_CONT_H if hov_cont else _BTN_CONT,
                     vs._continue_rect, border_radius=8)
    pygame.draw.rect(screen, (150, 150, 220), vs._continue_rect, 2, border_radius=8)
    cont_lbl = body_font.render("Продолжить ->", True, _WHITE)
    screen.blit(cont_lbl, (vs._continue_rect.centerx - cont_lbl.get_width() // 2,
                           vs._continue_rect.centery - cont_lbl.get_height() // 2))
