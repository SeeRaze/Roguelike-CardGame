import pygame
from core.cards import (
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_ignite, create_fire_breath, create_splash, create_rain_cloud,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
    create_bash, create_neutralize, create_intimidate,
    create_flex, create_battle_cry, create_thorn_armor,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_drain, create_blood_feast, create_life_tap,
    create_lacerate, create_hemorrhage, create_open_wound,
)
from ui.CardRenderer import CardRenderer

WARRIOR_CARDS = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_flex, create_battle_cry, create_thorn_armor, create_bash,
]

ROGUE_CARDS = [
    create_strike, create_defend,
    create_neutralize, create_intimidate,
    create_lacerate, create_hemorrhage, create_open_wound,
    create_drain, create_blood_feast,
]

MAGE_CARDS = [
    create_strike, create_defend,
    create_ignite, create_fire_breath,
    create_splash, create_rain_cloud,
    create_bash, create_acid_shield,
]

DRUID_CARDS = [
    create_strike, create_defend,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_poison_stab, create_toxic_cloud,
]

BERSERKER_CARDS = [
    create_strike, create_defend,
    create_heavy_blade, create_iron_wall,
    create_flex, create_battle_cry,
    create_life_tap,                    # вампиризм -- балансировать на грани
    create_lacerate,                    # кровь -- давление
]

ALL_CARDS = list({f.__name__: f for f in
    WARRIOR_CARDS + ROGUE_CARDS + MAGE_CARDS +
    DRUID_CARDS + BERSERKER_CARDS}.values())

TABS = [
    ("Все",       ALL_CARDS),
    ("Воин",      WARRIOR_CARDS),
    ("Разбойник", ROGUE_CARDS),
    ("Маг",       MAGE_CARDS),
    ("Друид",     DRUID_CARDS),
    ("Берсерк",   BERSERKER_CARDS),
]

CARD_W, CARD_H = 180, 250
COLS    = 8
GAP_X   = 20
GAP_Y   = 30
START_X = 60
START_Y = 200


class CardLibraryView:
    _active_tab   = 0
    _scroll_y     = 0
    _tab_rects    = []
    _btn_back     = pygame.Rect(30, 20, 160, 50)
    _hovered_card = None

    @classmethod
    def reset(cls):
        cls._active_tab = 0
        cls._scroll_y   = 0

    @classmethod
    def _get_cards(cls):
        return [f() for f in TABS[cls._active_tab][1]]

    @classmethod
    def draw_screen(cls, view):
        view.screen.fill((12, 12, 18))
        mouse = pygame.mouse.get_pos()
        cls._hovered_card = None

        pygame.draw.line(view.screen, (60, 60, 80), (0, 80), (1920, 80), 2)
        view.draw_text("БИБЛИОТЕКА КАРТ", view.main_font, (240, 200, 60), 760, 90)

        # Кнопка Назад
        back_col = (80, 80, 90) if cls._btn_back.collidepoint(mouse) else (50, 50, 60)
        pygame.draw.rect(view.screen, back_col, cls._btn_back, border_radius=8)
        pygame.draw.rect(view.screen, (200, 200, 200), cls._btn_back, 2, border_radius=8)
        view.draw_text("<  Назад", view.card_font, (255, 255, 255), 42, 35)

        # Вкладки -- 6 штук, шаг 155 чтобы влезли
        cls._tab_rects = []
        tx = 220
        for i, (label, _) in enumerate(TABS):
            rect = pygame.Rect(tx, 18, 150, 46)
            cls._tab_rects.append(rect)
            active  = (i == cls._active_tab)
            hovered = rect.collidepoint(mouse)
            bg = (60, 100, 160) if active else ((70, 70, 80) if hovered else (40, 40, 50))
            pygame.draw.rect(view.screen, bg, rect, border_radius=8)
            pygame.draw.rect(view.screen, (200, 200, 200), rect, 2, border_radius=8)
            view.draw_text(label, view.card_font, (255, 255, 255), tx + 15, 30)
            tx += 160

        pygame.draw.line(view.screen, (60, 60, 80), (0, 80), (1920, 80), 2)

        # Карты
        cards = cls._get_cards()
        clip_rect = pygame.Rect(0, 90, 1920, 1080 - 90)
        view.screen.set_clip(clip_rect)

        for i, card in enumerate(cards):
            col = i % COLS
            row = i // COLS
            x = START_X + col * (CARD_W + GAP_X)
            y = START_Y + row * (CARD_H + GAP_Y) - cls._scroll_y
            if y + CARD_H < 90 or y > 1080:
                continue
            card_rect = pygame.Rect(x, y, CARD_W, CARD_H)
            hovered   = card_rect.collidepoint(mouse)
            if hovered:
                cls._hovered_card = (card, card_rect)
            CardRenderer.draw(
                view.screen, card, x, y,
                view.card_font, view.card_desc_font,
                is_hovered=hovered, player=None, enemy=None,
            )

        view.screen.set_clip(None)

        # Тултип поверх клиппинга
        if cls._hovered_card:
            card, rect = cls._hovered_card
            CardRenderer.draw_card_keyword_tooltip(
                view.screen, view.card_font, view.card_desc_font, card, rect,
            )

        view.draw_text(
            f"Карт: {len(cards)}", view.card_desc_font,
            (140, 140, 140), 1800, 30,
        )

    @classmethod
    def handle_click(cls, view, mouse_pos):
        if cls._btn_back.collidepoint(mouse_pos):
            view.gm.current_state = "MAIN_MENU"
            return
        for i, rect in enumerate(cls._tab_rects):
            if rect.collidepoint(mouse_pos):
                cls._active_tab = i
                cls._scroll_y   = 0
                return

    @classmethod
    def handle_scroll(cls, direction, cards_count):
        rows = (cards_count + COLS - 1) // COLS
        max_scroll = max(0, rows * (CARD_H + GAP_Y) - (1080 - START_Y) + GAP_Y)
        cls._scroll_y = max(0, min(cls._scroll_y + direction * 60, max_scroll))