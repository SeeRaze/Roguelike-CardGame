# ui/combat/hover.py
# Расчёт hover-состояния боевого экрана (карты руки, бейджи статусов, реликвии, стопки).
import pygame


def update_combat_hover(view):
    """Заполняет view.hover по позиции мыши для экрана боя."""
    mouse_pos = pygame.mouse.get_pos()
    dm = view.gm.active_combat.deck_manager
    hand_size = len(dm.hand)

    # Hover по картам в руке
    for index in range(hand_size):
        card_x = view.calculate_card_x(index, hand_size)
        card_rect = pygame.Rect(
            card_x, view.base_y, view.card_width, view.card_height
        )
        if card_rect.collidepoint(mouse_pos):
            view.hover.card_index = index
            view.hover.card_rect  = card_rect
            view.hover.card_obj   = dm.hand[index]
            break

    # Hover по бейджам статусов (враг, затем игрок)
    for rect, key, val in view.enemy_badge_rects:
        if rect.collidepoint(mouse_pos):
            view.hover.status_key = key
            view.hover.status_val = val
            break
    if not view.hover.status_key:
        for rect, key, val in view.player_badge_rects:
            if rect.collidepoint(mouse_pos):
                view.hover.status_key = key
                view.hover.status_val = val
                break

    # Hover по реликвиям
    for rect, relic in view.relic_rects:
        if rect.collidepoint(mouse_pos):
            view.hover.relic_obj = relic
            break

    # Обновляем кеш добора если состав изменился
    current_ids = [id(c) for c in dm.draw_pile]
    if current_ids != view._draw_pile_ids:
        view._refresh_draw_pile_display(dm.draw_pile)

    # Hover по стопкам
    if view.draw_pile_rect.collidepoint(mouse_pos):
        view.hover.pile_type = "draw"
    elif view.discard_pile_rect.collidepoint(mouse_pos):
        view.hover.pile_type = "discard"
