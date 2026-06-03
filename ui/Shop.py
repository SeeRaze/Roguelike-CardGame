import pygame
import random
from core.cards import (create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_bash, create_neutralize, create_intimidate,
    create_ignite, create_fire_breath,
    create_splash, create_rain_cloud,
    create_poison_stab, create_toxic_cloud, create_acid_shield)
from core.cards.heal import create_bandage, create_second_wind, create_elixir
from core.cards.buff.regen import create_regenerate, create_vitality, create_triage
from core.cards.buff.vampirism import create_drain, create_blood_feast, create_life_tap
from core.cards.debuff.bleed import create_lacerate, create_hemorrhage, create_open_wound


class Shop:
    """Экран Магазина -- тёмно-зелёная/золотая тема, стиль EventView."""
    sub_state          = "MAIN"
    item_1             = None
    item_2             = None
    showcase_generated = False
    is_remove_hovered  = False
    is_leave_hovered   = False

    _BG_COLOR        = (10,  15,  10)
    _PANEL_COLOR     = (18,  28,  18)
    _BTN_COLOR       = (30,  55,  30)
    _BTN_HOVER_COLOR = (55,  100, 55)
    _BTN_BORDER      = (140, 200, 100)
    _TITLE_COLOR     = (255, 220, 60)
    _TEXT_COLOR      = (200, 210, 190)
    _GOLD_COLOR      = (255, 215, 0)
    _RED_COLOR       = (220, 80,  60)
    _GRAY_COLOR      = (120, 120, 120)
    _SOLD_COLOR      = (40,  50,  40)

    @staticmethod
    def reset():
        Shop.sub_state          = "MAIN"
        Shop.item_1             = None
        Shop.item_2             = None
        Shop.showcase_generated = False
        Shop.is_remove_hovered  = False
        Shop.is_leave_hovered   = False

    @staticmethod
    def get_card_price(floor: int) -> int:
        return 35 + floor * 3

    @staticmethod
    def generate_showcase():
        all_cards_pool = [
            create_strike, create_defend, create_heavy_blade, create_iron_wall,
            create_bash, create_neutralize, create_intimidate,
            create_ignite, create_fire_breath,
            create_splash, create_rain_cloud,
            create_poison_stab, create_toxic_cloud, create_acid_shield,
            create_bandage, create_second_wind, create_elixir,
            create_regenerate, create_vitality, create_triage,
            create_drain, create_blood_feast, create_life_tap,
            create_lacerate, create_hemorrhage, create_open_wound,
        ]
        picks = random.sample(all_cards_pool, 2)
        Shop.item_1 = picks[0]()
        Shop.item_2 = picks[1]()
        Shop.showcase_generated = True

    @staticmethod
    def draw_screen(view):
        S         = Shop
        screen    = view.screen
        W, H      = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(S._BG_COLOR)

        if not Shop.showcase_generated:
            Shop.generate_showcase()

        title_font = pygame.font.SysFont("Arial", 42, bold=True)
        text_font  = pygame.font.SysFont("Arial", 26)
        btn_font   = pygame.font.SysFont("Arial", 24, bold=True)
        price_font = pygame.font.SysFont("Arial", 22, bold=True)

        if Shop.sub_state == "MAIN":
            panel = pygame.Rect(W // 2 - 560, 40, 1120, 960)
            pygame.draw.rect(screen, S._PANEL_COLOR, panel, border_radius=16)
            pygame.draw.rect(screen, S._BTN_BORDER,  panel, 2, border_radius=16)

            title = title_font.render(
                f"ЭТАЖ {view.gm.current_floor}: ЛАВКА ТОРГОВЦА", True, S._TITLE_COLOR)
            screen.blit(title, (W // 2 - title.get_width() // 2, 70))

            gold_surf = text_font.render(
                f"Золото: {view.gm.player_gold} монет", True, S._GOLD_COLOR)
            screen.blit(gold_surf, (W // 2 - gold_surf.get_width() // 2, 135))

            card_price = Shop.get_card_price(view.gm.current_floor)
            card_w = view.card_width
            card_h = view.card_height
            gap    = 80
            total_cards_w = card_w * 2 + gap
            card1_x = W // 2 - total_cards_w // 2
            card2_x = card1_x + card_w + gap
            cards_y = 210

            _hovered_card_data = None

            # Карта 1
            view.shop_item_1_rect = pygame.Rect(card1_x, cards_y, card_w, card_h)
            if Shop.item_1:
                is_hov = view.shop_item_1_rect.collidepoint(mouse_pos)
                if is_hov:
                    _hovered_card_data = (Shop.item_1, view.shop_item_1_rect)
                draw_y = cards_y - 15 if is_hov else cards_y
                view.draw_card_by_data(Shop.item_1, card1_x, draw_y)
                p = price_font.render(f"{card_price} з.", True, S._GOLD_COLOR)
                screen.blit(p, (card1_x + card_w // 2 - p.get_width() // 2,
                                draw_y + card_h + 10))
            else:
                r = pygame.Rect(card1_x, cards_y, card_w, card_h)
                pygame.draw.rect(screen, S._SOLD_COLOR, r, border_radius=8)
                pygame.draw.rect(screen, S._GRAY_COLOR, r, 1, border_radius=8)
                lbl = text_font.render("[ПРОДАНО]", True, S._GRAY_COLOR)
                screen.blit(lbl, (r.centerx - lbl.get_width() // 2,
                                r.centery - lbl.get_height() // 2))

            # Карта 2
            view.shop_item_2_rect = pygame.Rect(card2_x, cards_y, card_w, card_h)
            if Shop.item_2:
                is_hov = view.shop_item_2_rect.collidepoint(mouse_pos)
                if is_hov:
                    _hovered_card_data = (Shop.item_2, view.shop_item_2_rect)
                draw_y = cards_y - 15 if is_hov else cards_y
                view.draw_card_by_data(Shop.item_2, card2_x, draw_y)
                p = price_font.render(f"{card_price} з.", True, S._GOLD_COLOR)
                screen.blit(p, (card2_x + card_w // 2 - p.get_width() // 2,
                                draw_y + card_h + 10))
            else:
                r = pygame.Rect(card2_x, cards_y, card_w, card_h)
                pygame.draw.rect(screen, S._SOLD_COLOR, r, border_radius=8)
                pygame.draw.rect(screen, S._GRAY_COLOR, r, 1, border_radius=8)
                lbl = text_font.render("[ПРОДАНО]", True, S._GRAY_COLOR)
                screen.blit(lbl, (r.centerx - lbl.get_width() // 2,
                                r.centery - lbl.get_height() // 2))

            sep_y = cards_y + card_h + 70
            pygame.draw.line(screen, S._BTN_BORDER,
                            (W // 2 - 460, sep_y), (W // 2 + 460, sep_y), 1)

            view.btn_shop_remove_rect = pygame.Rect(W // 2 - 320, sep_y + 24, 640, 72)
            Shop.is_remove_hovered = view.btn_shop_remove_rect.collidepoint(mouse_pos)
            col = (80, 35, 25) if Shop.is_remove_hovered else (50, 20, 15)
            pygame.draw.rect(screen, col, view.btn_shop_remove_rect, border_radius=12)
            pygame.draw.rect(screen, S._RED_COLOR, view.btn_shop_remove_rect, 2, border_radius=12)
            lbl = btn_font.render(
                f"СЖЕЧЬ КАРТУ  ({view.gm.get_removal_price()} з.)", True, S._RED_COLOR)
            screen.blit(lbl, (view.btn_shop_remove_rect.centerx - lbl.get_width() // 2,
                            view.btn_shop_remove_rect.centery - lbl.get_height() // 2))

            view.btn_shop_leave_rect = pygame.Rect(W // 2 - 320, sep_y + 116, 640, 72)
            Shop.is_leave_hovered = view.btn_shop_leave_rect.collidepoint(mouse_pos)
            col = S._BTN_HOVER_COLOR if Shop.is_leave_hovered else S._BTN_COLOR
            pygame.draw.rect(screen, col, view.btn_shop_leave_rect, border_radius=12)
            pygame.draw.rect(screen, S._BTN_BORDER, view.btn_shop_leave_rect, 2, border_radius=12)
            lbl = btn_font.render("ПОКИНУТЬ МАГАЗИН", True, (255, 255, 255))
            screen.blit(lbl, (view.btn_shop_leave_rect.centerx - lbl.get_width() // 2,
                            view.btn_shop_leave_rect.centery - lbl.get_height() // 2))

            # Тултип карты -- последним, поверх всего
            if _hovered_card_data:
                card, rect = _hovered_card_data
                from ui.cards import CardRenderer
                CardRenderer.draw_card_keyword_tooltip(
                    screen, view.card_font, view.card_desc_font, card, rect
                )

        elif Shop.sub_state == "REMOVE":
            panel = pygame.Rect(40, 20, W - 80, H - 40)
            pygame.draw.rect(screen, S._PANEL_COLOR, panel, border_radius=16)
            pygame.draw.rect(screen, S._BTN_BORDER,  panel, 2, border_radius=16)

            title = title_font.render("УТИЛИЗАЦИЯ: ВЫБЕРИТЕ КАРТУ", True, S._RED_COLOR)
            screen.blit(title, (W // 2 - title.get_width() // 2, 45))

            hint = text_font.render(
                "Кликните по карте для уничтожения  |  Колесо мыши -- прокрутка",
                True, S._TEXT_COLOR)
            screen.blit(hint, (W // 2 - hint.get_width() // 2, 110))

            cards_per_row = 7
            card_w    = view.card_width
            card_h    = view.card_height
            spacing_x = card_w + 24
            spacing_y = card_h + 36
            total_w   = cards_per_row * spacing_x - 24
            start_x   = W // 2 - total_w // 2
            start_y   = 165

            clip_rect = pygame.Rect(60, start_y, W - 120, H - start_y - 30)
            screen.set_clip(clip_rect)

            _hovered_card_data = None
            view.shop_remove_card_rects = []

            for index, card in enumerate(view.gm.current_deck):
                row    = index // cards_per_row
                col    = index % cards_per_row
                card_x = start_x + col * spacing_x
                card_y = start_y + 10 + row * spacing_y - view.scroll_y
                card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
                view.shop_remove_card_rects.append((card_rect, index))
                is_hov = card_rect.collidepoint(mouse_pos)
                if is_hov:
                    _hovered_card_data = (card, card_rect)
                draw_y = card_y - 10 if is_hov else card_y
                view.draw_card_by_data(card, card_x, draw_y)

            screen.set_clip(None)

            # Тултип поверх clip -- последним
            if _hovered_card_data:
                card, rect = _hovered_card_data
                from ui.cards import CardRenderer
                CardRenderer.draw_card_keyword_tooltip(
                    screen, view.card_font, view.card_desc_font, card, rect
                )

    @staticmethod
    def handle_clicks(view, mouse_pos):
        if Shop.sub_state == "MAIN":
            card_price = Shop.get_card_price(view.gm.current_floor)

            if Shop.item_1 and hasattr(view, 'shop_item_1_rect') \
                    and view.shop_item_1_rect.collidepoint(mouse_pos):
                if view.gm.player_gold >= card_price:
                    view.gm.player_gold -= card_price
                    view.gm.add_card(Shop.item_1)
                    Shop.item_1 = None
                else:
                    print("[!] Не хватает золота!")

            elif Shop.item_2 and hasattr(view, 'shop_item_2_rect') \
                    and view.shop_item_2_rect.collidepoint(mouse_pos):
                if view.gm.player_gold >= card_price:
                    view.gm.player_gold -= card_price
                    view.gm.add_card(Shop.item_2)
                    Shop.item_2 = None
                else:
                    print("[!] Не хватает золота!")

            elif hasattr(view, 'btn_shop_remove_rect') \
                    and view.btn_shop_remove_rect.collidepoint(mouse_pos):
                if view.gm.player_gold >= view.gm.get_removal_price():
                    view.scroll_y = 0
                    Shop.sub_state = "REMOVE"
                else:
                    print("[!] Не хватает золота на чистку колоды!")

            elif hasattr(view, 'btn_shop_leave_rect') \
                    and view.btn_shop_leave_rect.collidepoint(mouse_pos):
                Shop.item_1 = None
                Shop.item_2 = None
                Shop.showcase_generated = False
                view.gm.current_floor += 1
                view.gm.setup_next_floor()

        elif Shop.sub_state == "REMOVE":
            if hasattr(view, 'shop_remove_card_rects'):
                for card_rect, index in view.shop_remove_card_rects:
                    if card_rect.collidepoint(mouse_pos):
                        removed = view.gm.current_deck.pop(index)
                        view.gm.player_gold -= view.gm.get_removal_price()
                        view.gm.removal_count += 1
                        print(f"Карта '{removed.name}' сожжена.")
                        Shop.sub_state = "MAIN"
                        break