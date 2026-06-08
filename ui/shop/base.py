# ui/shop/base.py
# Магазин: состояние-машина (MAIN/REMOVE), диспетчер отрисовки и обработка кликов.
# Витрина: 5 карт + слот реликвии + покупка ключа + утилизация (чистка колоды).
import random

import pygame
from ui.shop.data import (
    _BG_COLOR, SHOP_CARD_SLOTS, ROB_SUCCESS_CHANCE,
    get_card_price, get_relic_price, get_key_price, pick_cards, pick_relic,
)
from ui.shop import main_view, remove_view


class Shop:
    """Экран Магазина. Состояние-машина: MAIN (витрина) / REMOVE (утилизация)."""
    sub_state          = "MAIN"
    items              = []      # карты на продажу (None = уже куплена)
    relic_item         = None    # реликвия на продажу (None = куплена/нет)
    showcase_generated = False
    is_remove_hovered  = False
    is_leave_hovered   = False
    is_key_hovered     = False
    is_temper_hovered  = False

    @staticmethod
    def reset():
        Shop.sub_state          = "MAIN"
        Shop.items              = []
        Shop.relic_item         = None
        Shop.showcase_generated = False
        Shop.is_remove_hovered  = False
        Shop.is_leave_hovered   = False
        Shop.is_key_hovered     = False
        Shop.is_temper_hovered  = False

    @staticmethod
    def generate_showcase(gm):
        class_name      = type(gm.player).__name__
        Shop.items      = pick_cards(SHOP_CARD_SLOTS, class_name)
        Shop.relic_item = pick_relic(gm)
        Shop.showcase_generated = True

    @staticmethod
    def draw_screen(view):
        screen = view.screen
        screen.fill(_BG_COLOR)

        if not Shop.showcase_generated:
            Shop.generate_showcase(view.gm)

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
        gm = view.gm

        # --- Покупка карты ---
        card_price = get_card_price(gm.current_floor)
        for rect, idx in getattr(view, 'shop_card_rects', []):
            if Shop.items[idx] and rect.collidepoint(mouse_pos):
                if gm.player_gold >= card_price:
                    gm.player_gold -= card_price
                    gm.add_card(Shop.items[idx])
                    Shop.items[idx] = None
                else:
                    print("[!] Не хватает золота на карту!")
                return

        # --- Покупка реликвии ---
        if Shop.relic_item and hasattr(view, 'shop_relic_rect') \
                and view.shop_relic_rect.collidepoint(mouse_pos):
            price = get_relic_price(Shop.relic_item, gm.current_floor)
            if gm.player_gold >= price:
                gm.player_gold -= price
                gm.relics.append(Shop.relic_item)
                Shop.relic_item = None
            else:
                print("[!] Не хватает золота на реликвию!")
            return

        # --- Покупка ключа (бесконечный запас) ---
        if hasattr(view, 'btn_shop_key_rect') \
                and view.btn_shop_key_rect.collidepoint(mouse_pos):
            if gm.player_gold >= get_key_price():
                gm.player_gold -= get_key_price()
                gm.player_keys += 1
            else:
                print("[!] Не хватает золота на ключ!")
            return

        # --- Закалка (сток ЗОЛОТА в Max HP — ось выживаемости, С57) ---
        if hasattr(view, 'btn_shop_temper_rect') and view.btn_shop_temper_rect \
                and view.btn_shop_temper_rect.collidepoint(mouse_pos):
            from core import forge as forge_mod
            ok, spent = forge_mod.temper(gm.player, gm.player_gold)
            if ok:
                gm.player_gold -= spent
            else:
                print("[!] Не хватает золота на Закалку!")
            return

        # --- Ограбление (украсть реликвию; доступно только при ней) ---
        if Shop.relic_item and hasattr(view, 'btn_shop_rob_rect') \
                and view.btn_shop_rob_rect.collidepoint(mouse_pos):
            Shop._rob(view)
            return

        # --- Утилизация (чистка колоды) ---
        if hasattr(view, 'btn_shop_remove_rect') \
                and view.btn_shop_remove_rect.collidepoint(mouse_pos):
            if gm.player_gold >= gm.get_removal_price():
                view.scroll_y = 0
                Shop.sub_state = "REMOVE"
            else:
                print("[!] Не хватает золота на чистку колоды!")
            return

        # --- Покинуть магазин ---
        if hasattr(view, 'btn_shop_leave_rect') \
                and view.btn_shop_leave_rect.collidepoint(mouse_pos):
            Shop._leave(view)

    @staticmethod
    def _leave(view):
        """Покинуть магазин — закрыть витрину и перейти на следующий этаж."""
        Shop.reset()
        view.gm.current_floor += 1
        view.gm.setup_next_floor()

    @staticmethod
    def _rob(view):
        """«Ограбление»: украсть реликвию из слота. Успех (ROB_SUCCESS_CHANCE) →
        забрать бесплатно и сбежать (покинуть магазин). Провал → витрина
        закрывается, немедленный бой с ЭЛИТКОЙ на текущем этаже (этаж продвинет
        победа боя через VictoryScreen)."""
        gm    = view.gm
        relic = Shop.relic_item
        if random.random() < ROB_SUCCESS_CHANCE:
            if relic is not None:
                gm.relics.append(relic)
            print(f"[ОГРАБЛЕНИЕ] Успех! Украдена реликвия '{getattr(relic, 'name', '?')}'.")
            Shop._leave(view)
        else:
            print("[ОГРАБЛЕНИЕ] Провал! Торговец зовёт элитного стража.")
            Shop.reset()
            gm.current_state = "COMBAT"
            gm.spawn_procedural_enemy(is_elite=True)

    @staticmethod
    def _handle_remove(view, mouse_pos):
        # «Назад» — вернуться в магазин без удаления (золото не тратится).
        if getattr(view, 'shop_remove_back_rect', None) \
                and view.shop_remove_back_rect.collidepoint(mouse_pos):
            Shop.sub_state = "MAIN"
            return
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
