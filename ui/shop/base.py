# ui/shop/base.py
# Магазин: состояние-машина (MAIN/REMOVE), диспетчер отрисовки и обработка кликов.
import pygame
from ui.shop.data import _BG_COLOR, get_card_price, pick_two_cards
from ui.shop import main_view, remove_view


class Shop:
    """Экран Магазина. Состояние-машина: MAIN (витрина) / REMOVE (утилизация)."""
    sub_state          = "MAIN"
    item_1             = None
    item_2             = None
    showcase_generated = False
    is_remove_hovered  = False
    is_leave_hovered   = False

    @staticmethod
    def reset():
        Shop.sub_state          = "MAIN"
        Shop.item_1             = None
        Shop.item_2             = None
        Shop.showcase_generated = False
        Shop.is_remove_hovered  = False
        Shop.is_leave_hovered   = False

    @staticmethod
    def generate_showcase():
        Shop.item_1, Shop.item_2 = pick_two_cards()
        Shop.showcase_generated  = True

    @staticmethod
    def draw_screen(view):
        screen = view.screen
        screen.fill(_BG_COLOR)

        if not Shop.showcase_generated:
            Shop.generate_showcase()

        fonts = {
            "title": pygame.font.SysFont("Arial", 42, bold=True),
            "text":  pygame.font.SysFont("Arial", 26),
            "btn":   pygame.font.SysFont("Arial", 24, bold=True),
            "price": pygame.font.SysFont("Arial", 22, bold=True),
        }

        if Shop.sub_state == "MAIN":
            main_view.draw_main(Shop, view, screen, fonts)
        elif Shop.sub_state == "REMOVE":
            remove_view.draw_remove(Shop, view, screen, fonts)

    @staticmethod
    def handle_clicks(view, mouse_pos):
        if Shop.sub_state == "MAIN":
            Shop._handle_main(view, mouse_pos)
        elif Shop.sub_state == "REMOVE":
            Shop._handle_remove(view, mouse_pos)

    @staticmethod
    def _handle_main(view, mouse_pos):
        card_price = get_card_price(view.gm.current_floor)

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

    @staticmethod
    def _handle_remove(view, mouse_pos):
        if not hasattr(view, 'shop_remove_card_rects'):
            return
        for card_rect, index in view.shop_remove_card_rects:
            if card_rect.collidepoint(mouse_pos):
                removed = view.gm.current_deck.pop(index)
                view.gm.player_gold -= view.gm.get_removal_price()
                view.gm.removal_count += 1
                print(f"Карта '{removed.name}' сожжена.")
                Shop.sub_state = "MAIN"
                break
