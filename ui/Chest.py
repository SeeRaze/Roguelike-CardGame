import pygame
import random
from ui.CardRenderer import CardRenderer
from core.cards.basic import create_strike, create_defend, create_heavy_blade, create_iron_wall
from core.cards.fire import create_ignite, create_fire_breath
from core.cards.poison import create_poison_stab, create_toxic_cloud, create_acid_shield
from core.cards.buff.strength import create_flex, create_battle_cry
from core.cards.buff.thorns import create_thorn_armor
from core.cards.debuff.vulnerable import create_bash
from core.cards.debuff.weak import create_neutralize, create_intimidate


# Пул фабричных функций для наград из сундука
CHEST_CARD_POOL = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_ignite, create_fire_breath,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
    create_flex, create_battle_cry,
    create_thorn_armor,
    create_bash,
    create_neutralize, create_intimidate,
]

CHEST_TYPES = ["common", "rare", "trap"]
CHEST_WEIGHTS = [55, 25, 20]


def pick_chest_type():
    return random.choices(CHEST_TYPES, weights=CHEST_WEIGHTS, k=1)[0]


def generate_chest_cards(count=2):
    """Случайные карты из пула (без повторов)."""
    factories = random.sample(CHEST_CARD_POOL, min(count, len(CHEST_CARD_POOL)))
    return [factory() for factory in factories]  # <-- вызываем фабрику, не конструктор


class Chest:
    """Экран сундука: три типа -- обычный, редкий, ловушка."""

    BG_COLOR      = (15, 12, 25)
    TITLE_COMMON  = (200, 170, 80)
    TITLE_RARE    = (140, 80, 220)
    TITLE_TRAP    = (200, 60, 60)
    TEXT_COLOR    = (200, 200, 200)
    BTN_COLOR     = (40, 40, 60)
    BTN_BORDER    = (255, 255, 255)
    BTN_HOVER     = (70, 70, 100)
    GOLD_COLOR    = (255, 210, 50)
    HP_COLOR      = (220, 80, 80)
    SKIP_COLOR    = (120, 120, 140)

    CARD_W = 180
    CARD_H = 250

    @staticmethod
    def init_chest(view):
        """Вызывается при входе в комнату CHEST. Генерирует содержимое."""
        gm = view.gm
        chest_type = pick_chest_type()
        gm.chest_type = chest_type

        if chest_type == "common":
            gm.chest_cards   = generate_chest_cards(2)
            gm.chest_gold    = 0
            gm.chest_hp_loss = 0

        elif chest_type == "rare":
            gm.chest_cards   = generate_chest_cards(3)
            gm.chest_gold    = random.randint(15, 30)
            gm.chest_hp_loss = 0

        elif chest_type == "trap":
            gm.chest_cards   = []
            gm.chest_gold    = random.randint(20, 40)
            gm.chest_hp_loss = random.randint(15, 25)
            gm.player.hp     = max(1, gm.player.hp - gm.chest_hp_loss)
            gm.player_gold  += gm.chest_gold

        gm.chest_selected = None
        gm.chest_opened   = False

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

        chest_type = getattr(gm, "chest_type", "common")

        titles = {
            "common": ("Обычный сундук", Chest.TITLE_COMMON),
            "rare":   ("Редкий сундук",  Chest.TITLE_RARE),
            "trap":   ("Сундук-ловушка", Chest.TITLE_TRAP),
        }
        title_text, title_color = titles[chest_type]
        t = main_font.render(title_text, True, title_color)
        screen.blit(t, (960 - t.get_width() // 2, 60))

        if chest_type == "trap":
            Chest._draw_trap_screen(view, screen, sub_font, small_font)
            return

        cards = getattr(gm, "chest_cards", [])
        count = len(cards)

        hint = "Выбери одну карту:" if not gm.chest_opened else "Карта добавлена в колоду!"
        h = sub_font.render(hint, True, Chest.TEXT_COLOR)
        screen.blit(h, (960 - h.get_width() // 2, 130))

        if chest_type == "rare" and gm.chest_gold > 0:
            gold_text = f"+ {gm.chest_gold} золота (при взятии карты)"
            g = sub_font.render(gold_text, True, Chest.GOLD_COLOR)
            screen.blit(g, (960 - g.get_width() // 2, 170))

        spacing = 220
        total_w = count * spacing
        start_x = 960 - total_w // 2 + spacing // 2 - Chest.CARD_W // 2

        for i, card in enumerate(cards):
            cx = start_x + i * spacing
            cy = 300
            is_selected = (gm.chest_selected == i)

            mouse = pygame.mouse.get_pos()
            rect  = pygame.Rect(cx, cy, Chest.CARD_W, Chest.CARD_H)
            is_hovered = rect.collidepoint(mouse) if not gm.chest_opened else False

            if not gm.chest_opened and is_selected:
                pygame.draw.rect(screen, (255, 220, 50),
                                 pygame.Rect(cx - 4, cy - 4,
                                             Chest.CARD_W + 8, Chest.CARD_H + 8), 3)

            CardRenderer.draw(
                screen, card, cx, cy,
                card_font, desc_font,
                is_hovered,
                player=gm.player,
                enemy=None,
            )

        if not gm.chest_opened:
            Chest._draw_buttons(view, screen, card_font, small_font)
        else:
            Chest._draw_continue_button(view, screen, card_font)

    @staticmethod
    def _draw_trap_screen(view, screen, sub_font, small_font):
        gm      = view.gm
        hp_loss = getattr(gm, "chest_hp_loss", 0)
        gold    = getattr(gm, "chest_gold", 0)

        lines = [
            (f"Ловушка сработала! Вы потеряли {hp_loss} HP.", Chest.HP_COLOR),
            (f"Но нашли {gold} золота в качестве компенсации.", Chest.GOLD_COLOR),
            (f"Текущее HP: {gm.player.hp} / {gm.player.max_hp}", Chest.TEXT_COLOR),
        ]
        for i, (text, color) in enumerate(lines):
            s = sub_font.render(text, True, color)
            screen.blit(s, (960 - s.get_width() // 2, 250 + i * 60))

        Chest._draw_continue_button(view, screen, small_font)

    @staticmethod
    def _draw_buttons(view, screen, card_font, small_font):
        gm    = view.gm
        mouse = pygame.mouse.get_pos()

        take_rect  = pygame.Rect(760, 620, 200, 60)
        can_take   = gm.chest_selected is not None
        take_col   = Chest.BTN_HOVER if (take_rect.collidepoint(mouse) and can_take) else Chest.BTN_COLOR
        take_border = (100, 220, 100) if can_take else (80, 80, 80)
        pygame.draw.rect(screen, take_col, take_rect)
        pygame.draw.rect(screen, take_border, take_rect, 2)
        take_label = card_font.render("Взять", True,
                                      (200, 255, 200) if can_take else (100, 100, 100))
        screen.blit(take_label, (take_rect.centerx - take_label.get_width() // 2,
                                 take_rect.centery - take_label.get_height() // 2))

        skip_rect = pygame.Rect(980, 620, 200, 60)
        skip_col  = Chest.BTN_HOVER if skip_rect.collidepoint(mouse) else Chest.BTN_COLOR
        pygame.draw.rect(screen, skip_col, skip_rect)
        pygame.draw.rect(screen, Chest.SKIP_COLOR, skip_rect, 2)
        skip_label = card_font.render("Пропустить", True, Chest.SKIP_COLOR)
        screen.blit(skip_label, (skip_rect.centerx - skip_label.get_width() // 2,
                                 skip_rect.centery - skip_label.get_height() // 2))

    @staticmethod
    def _draw_continue_button(view, screen, font):
        mouse = pygame.mouse.get_pos()
        btn   = pygame.Rect(760, 700, 400, 60)
        col   = Chest.BTN_HOVER if btn.collidepoint(mouse) else Chest.BTN_COLOR
        pygame.draw.rect(screen, col, btn)
        pygame.draw.rect(screen, Chest.BTN_BORDER, btn, 2)
        label = font.render("Продолжить ->", True, (255, 255, 255))
        screen.blit(label, (btn.centerx - label.get_width() // 2,
                            btn.centery - label.get_height() // 2))

    @staticmethod
    def handle_clicks(view, mouse_pos):
        gm         = view.gm
        chest_type = getattr(gm, "chest_type", "common")

        if chest_type == "trap" or gm.chest_opened:
            btn = pygame.Rect(760, 700, 400, 60)
            if btn.collidepoint(mouse_pos):
                gm.current_floor += 1
                gm.setup_next_floor()
            return

        cards   = getattr(gm, "chest_cards", [])
        count   = len(cards)
        spacing = 220
        total_w = count * spacing
        start_x = 960 - total_w // 2 + spacing // 2 - Chest.CARD_W // 2

        for i in range(count):
            cx   = start_x + i * spacing
            rect = pygame.Rect(cx, 300, Chest.CARD_W, Chest.CARD_H)
            if rect.collidepoint(mouse_pos):
                gm.chest_selected = i
                return

        take_rect = pygame.Rect(760, 620, 200, 60)
        if take_rect.collidepoint(mouse_pos) and gm.chest_selected is not None:
            chosen_card = cards[gm.chest_selected]
            gm.add_card(chosen_card)
            if chest_type == "rare" and gm.chest_gold > 0:
                gm.player_gold += gm.chest_gold
            gm.chest_opened = True
            return

        skip_rect = pygame.Rect(980, 620, 200, 60)
        if skip_rect.collidepoint(mouse_pos):
            gm.current_floor += 1
            gm.setup_next_floor()