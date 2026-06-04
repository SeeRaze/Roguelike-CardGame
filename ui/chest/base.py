import pygame
from ui.chest.data   import pick_chest_type, generate_chest_cards, generate_cursed_buffs
from ui.chest.common import draw_common, clicks_common
from ui.chest.locked import draw_locked, clicks_locked
from ui.chest.cursed import draw_cursed, clicks_cursed
from ui.cards import CardRenderer
import random


class Chest:
    """Экран сундука: обычный / закрытый / проклятый."""

    BG_COLOR   = (15,  12,  25)
    TEXT_COLOR = (200, 200, 200)

    TITLE_COLORS = {
        "common": (200, 170,  80),
        "locked": (100, 160, 255),
        "cursed": (180,  50, 220),
    }
    TITLE_NAMES = {
        "common": "Обычный сундук",
        "locked": "Закрытый сундук",
        "cursed": "Проклятый сундук",
    }

    @staticmethod
    def init_chest(view):
        gm = view.gm
        chest_type        = pick_chest_type()
        gm.chest_type     = chest_type
        gm.chest_selected = None
        gm.chest_opened   = False
        class_name        = type(gm.player).__name__

        if chest_type == "common":
            gm.chest_cards = generate_chest_cards(2, class_name)
            gm.chest_gold  = 0
        elif chest_type == "locked":
            gm.chest_cards = generate_chest_cards(4, class_name)
            gm.chest_gold  = random.randint(30, 60)
        elif chest_type == "cursed":
            gm.chest_cards  = []
            gm.chest_gold   = 0
            gm.cursed_buffs = generate_cursed_buffs(3)
            gm.cursed_taken = set()

    @staticmethod
    def draw_screen(view):
        screen = view.screen
        gm     = view.gm
        screen.fill(Chest.BG_COLOR)

        main_font  = pygame.font.SysFont("Arial", 36, bold=True)
        sub_font   = pygame.font.SysFont("Arial", 24)
        small_font = pygame.font.SysFont("Arial", 20)
        card_font  = pygame.font.SysFont("Arial", 22, bold=True)
        desc_font  = pygame.font.SysFont("Arial", 16)

        chest_type  = getattr(gm, "chest_type", "common")
        title_color = Chest.TITLE_COLORS.get(chest_type, (200, 200, 200))
        title_text  = Chest.TITLE_NAMES.get(chest_type, "Сундук")

        t = main_font.render(title_text, True, title_color)
        screen.blit(t, (960 - t.get_width() // 2, 60))

        # draw_* возвращают (card, rect) если карта под курсором, иначе None
        hovered_card_data = None
        if chest_type == "common":
            hovered_card_data = draw_common(view, screen, sub_font, card_font, desc_font, small_font)
        elif chest_type == "locked":
            hovered_card_data = draw_locked(view, screen, sub_font, card_font, desc_font, small_font)
        elif chest_type == "cursed":
            draw_cursed(view, screen, sub_font, card_font, desc_font)

        # Тултип карты -- самым последним, поверх всего
        if hovered_card_data:
            card, rect = hovered_card_data
            CardRenderer.draw_card_keyword_tooltip(
                screen, card_font, desc_font, card, rect
            )

    @staticmethod
    def handle_clicks(view, mouse_pos):
        chest_type = getattr(view.gm, "chest_type", "common")
        if chest_type == "common":
            clicks_common(view, mouse_pos)
        elif chest_type == "locked":
            clicks_locked(view, mouse_pos)
        elif chest_type == "cursed":
            clicks_cursed(view, mouse_pos)