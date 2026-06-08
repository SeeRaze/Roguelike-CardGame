# ui/shop/main_view.py
# Главный экран магазина: 5 карт + слот реликвии + покупка ключа +
# кнопки «Сжечь карту» (утилизация) / «Покинуть».
import pygame
from core.rarity import RARITY_COLORS
from core import forge as forge_mod
from ui.combat.hud import CombatHUD
from ui.shop.data import (
    _PANEL_COLOR, _BTN_COLOR, _BTN_HOVER_COLOR, _BTN_BORDER, _TITLE_COLOR,
    _GOLD_COLOR, _RED_COLOR, _GRAY_COLOR, _SOLD_COLOR, _TEXT_COLOR,
    ROB_SUCCESS_CHANCE, get_forged_card_price, get_relic_price, get_key_price,
)

# Цвет Закалки (ось выживаемости / HP) — тёплый зелёный, как HP-бар.
_TEMPER_COLOR = (120, 220, 120)


def _draw_sold_slot(screen, rect, text_font):
    pygame.draw.rect(screen, _SOLD_COLOR, rect, border_radius=8)
    pygame.draw.rect(screen, _GRAY_COLOR, rect, 1, border_radius=8)
    lbl = text_font.render("[ПРОДАНО]", True, _GRAY_COLOR)
    screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                      rect.centery - lbl.get_height() // 2))


def _draw_button(screen, font, rect, label, hovered, border, label_col=None):
    col = _BTN_HOVER_COLOR if hovered else _BTN_COLOR
    pygame.draw.rect(screen, col, rect, border_radius=12)
    pygame.draw.rect(screen, border, rect, 2, border_radius=12)
    lbl = font.render(label, True, label_col or (255, 255, 255))
    screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                      rect.centery - lbl.get_height() // 2))


def _draw_cards(shop, view, screen, fonts, mouse_pos):
    """5 карт в ряд. Возвращает (hovered_card, rect) или None."""
    W = screen.get_width()
    card_w, card_h = view.card_width, view.card_height
    price_font = fonts["price"]
    n = len(shop.items)
    gap = 22
    total_w = card_w * n + gap * (n - 1)
    start_x = W // 2 - total_w // 2
    cards_y = 210

    hovered = None
    view.shop_card_rects = []
    for idx, item in enumerate(shop.items):
        x = start_x + idx * (card_w + gap)
        rect = pygame.Rect(x, cards_y, card_w, card_h)
        view.shop_card_rects.append((rect, idx))
        if item:
            is_hov = rect.collidepoint(mouse_pos)
            if is_hov:
                hovered = (item, rect)
            draw_y = cards_y - 15 if is_hov else cards_y
            view.draw_card_by_data(item, x, draw_y, player=view.gm.player)
            price = get_forged_card_price(item, view.gm.player, view.gm.current_floor)
            p = price_font.render(f"{price} з.", True, _GOLD_COLOR)
            screen.blit(p, (x + card_w // 2 - p.get_width() // 2, draw_y + card_h + 8))
        else:
            _draw_sold_slot(screen, rect, fonts["text"])
    return hovered


def _draw_relic_slot(shop, view, screen, fonts, mouse_pos):
    """Слот реликвии (слева в нижнем ряду). Возвращает True если под курсором."""
    W = screen.get_width()
    text_font, price_font = fonts["text"], fonts["price"]
    rect = pygame.Rect(W // 2 - 470, 510, 450, 105)
    view.shop_relic_rect = rect

    if not shop.relic_item:
        _draw_sold_slot(screen, rect, text_font)
        return False

    relic   = shop.relic_item
    hovered = rect.collidepoint(mouse_pos)
    rarity_c = RARITY_COLORS.get(relic.rarity, (150, 150, 150))
    bg = (40, 60, 40) if hovered else (24, 36, 24)
    pygame.draw.rect(screen, bg, rect, border_radius=12)
    pygame.draw.rect(screen, rarity_c, rect, 2, border_radius=12)

    badge = pygame.Rect(rect.x + 16, rect.centery - 32, 64, 64)
    CombatHUD.draw_relic_badge(screen, relic, badge)

    name = text_font.render(relic.name, True, rarity_c)
    screen.blit(name, (badge.right + 18, rect.y + 18))
    price = price_font.render(
        f"{get_relic_price(relic, view.gm.current_floor)} з.", True, _GOLD_COLOR)
    screen.blit(price, (badge.right + 18, rect.y + 58))
    return hovered


def _draw_rob_button(shop, view, screen, fonts, mouse_pos):
    """Кнопка «Ограбить» под слотом реликвии — только если реликвия не продана."""
    W = screen.get_width()
    if not shop.relic_item:
        view.btn_shop_rob_rect = None
        return
    rect = pygame.Rect(W // 2 - 470, 623, 450, 48)
    view.btn_shop_rob_rect = rect
    hovered = rect.collidepoint(mouse_pos)
    bg = (70, 25, 60) if hovered else (45, 18, 40)
    pygame.draw.rect(screen, bg, rect, border_radius=10)
    pygame.draw.rect(screen, (200, 90, 180), rect, 2, border_radius=10)
    pct = int(ROB_SUCCESS_CHANCE * 100)
    lbl = fonts["btn"].render(
        f"ОГРАБИТЬ  ({pct}%, провал → элитка)", True, (230, 140, 210))
    screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                      rect.centery - lbl.get_height() // 2))


def _draw_key_slot(shop, view, screen, fonts, mouse_pos):
    W = screen.get_width()
    rect = pygame.Rect(W // 2 + 20, 510, 450, 105)
    view.btn_shop_key_rect = rect
    shop.is_key_hovered = rect.collidepoint(mouse_pos)
    bg = (50, 50, 25) if shop.is_key_hovered else (32, 32, 18)
    pygame.draw.rect(screen, bg, rect, border_radius=12)
    pygame.draw.rect(screen, _GOLD_COLOR, rect, 2, border_radius=12)
    lbl = fonts["btn"].render(f"КУПИТЬ КЛЮЧ  ({get_key_price()} з.)", True, _GOLD_COLOR)
    screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.y + 30))
    cnt = fonts["text"].render(
        f"Ключей: {getattr(view.gm, 'player_keys', 0)}", True, _TEXT_COLOR)
    screen.blit(cnt, (rect.centerx - cnt.get_width() // 2, rect.y + 72))


def _draw_temper_button(shop, view, screen, fonts, mouse_pos):
    """Закалка (С57: сток ЗОЛОТА в Max HP — ось выживаемости, economy-axis-trinity).
    Переехала с костра в магазин: золото покупает ЭКСПОНЕНТУ выживаемости (+%max_hp
    компаунд + полный хил). Гаснет, если не хватает золота."""
    W = screen.get_width()
    cost = forge_mod.TEMPER_GOLD_COST
    pct  = int(forge_mod.TEMPER_HP_PCT * 100)
    affordable = view.gm.player_gold >= cost
    rect = pygame.Rect(W // 2 - 320, 705, 640, 64)
    view.btn_shop_temper_rect = rect
    shop.is_temper_hovered = affordable and rect.collidepoint(mouse_pos)

    if not affordable:
        bg, border, txtc = (30, 40, 30), (70, 90, 70), (120, 140, 120)
    elif shop.is_temper_hovered:
        bg, border, txtc = (40, 75, 40), _TEMPER_COLOR, (255, 255, 255)
    else:
        bg, border, txtc = (26, 50, 26), _TEMPER_COLOR, _TEMPER_COLOR
    pygame.draw.rect(screen, bg, rect, border_radius=12)
    pygame.draw.rect(screen, border, rect, 2, border_radius=12)
    lbl = fonts["btn"].render(
        f"ЗАКАЛКА  (+{pct}% макс.HP + лечение, {cost} з.)", True, txtc)
    screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                      rect.centery - lbl.get_height() // 2))


def draw_main(shop, view, screen, fonts):
    W = screen.get_width()
    mouse_pos = pygame.mouse.get_pos()

    panel = pygame.Rect(W // 2 - 560, 70, 1120, 930)
    pygame.draw.rect(screen, _PANEL_COLOR, panel, border_radius=16)
    pygame.draw.rect(screen, _BTN_BORDER,  panel, 2, border_radius=16)

    title = fonts["title"].render(
        f"ЭТАЖ {view.gm.current_floor}: ЛАВКА ТОРГОВЦА", True, _TITLE_COLOR)
    screen.blit(title, (W // 2 - title.get_width() // 2, 90))
    gold = fonts["text"].render(
        f"Золото: {view.gm.player_gold} монет", True, _GOLD_COLOR)
    screen.blit(gold, (W // 2 - gold.get_width() // 2, 150))

    hovered_card = _draw_cards(shop, view, screen, fonts, mouse_pos)
    relic_hovered = _draw_relic_slot(shop, view, screen, fonts, mouse_pos)
    _draw_key_slot(shop, view, screen, fonts, mouse_pos)
    _draw_rob_button(shop, view, screen, fonts, mouse_pos)

    # Кнопка «Закалка» (ось выживаемости: золото → +%max HP + хил)
    _draw_temper_button(shop, view, screen, fonts, mouse_pos)

    # Кнопка «Сжечь карту» (утилизация)
    view.btn_shop_remove_rect = pygame.Rect(W // 2 - 320, 781, 640, 64)
    shop.is_remove_hovered = view.btn_shop_remove_rect.collidepoint(mouse_pos)
    rcol = (80, 35, 25) if shop.is_remove_hovered else (50, 20, 15)
    pygame.draw.rect(screen, rcol, view.btn_shop_remove_rect, border_radius=12)
    pygame.draw.rect(screen, _RED_COLOR, view.btn_shop_remove_rect, 2, border_radius=12)
    rlbl = fonts["btn"].render(
        f"СЖЕЧЬ КАРТУ  ({view.gm.get_removal_price()} з.)", True, _RED_COLOR)
    screen.blit(rlbl, (view.btn_shop_remove_rect.centerx - rlbl.get_width() // 2,
                       view.btn_shop_remove_rect.centery - rlbl.get_height() // 2))

    # Кнопка «Покинуть»
    view.btn_shop_leave_rect = pygame.Rect(W // 2 - 320, 857, 640, 64)
    shop.is_leave_hovered = view.btn_shop_leave_rect.collidepoint(mouse_pos)
    _draw_button(screen, fonts["btn"], view.btn_shop_leave_rect,
                 "ПОКИНУТЬ МАГАЗИН", shop.is_leave_hovered, _BTN_BORDER)

    # Тултипы поверх всего
    if hovered_card:
        card, rect = hovered_card
        from ui.cards import CardRenderer
        CardRenderer.draw_card_keyword_tooltip(
            screen, view.card_font, view.card_desc_font, card, rect)
    elif relic_hovered and shop.relic_item:
        CombatHUD.draw_relic_tooltip(screen, fonts["text"], shop.relic_item, mouse_pos)
