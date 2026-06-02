import pygame
import random

# ─── Пул событий ────────────────────────────────────────────────────────────
# Каждое событие: dict с ключами:
#   title   — заголовок
#   text    — описание ситуации
#   options — список вариантов [{"label": str, "effect": callable(gm)}]

def _make_events():
    from core.cards.basic import create_strike, create_defend, create_heavy_blade, create_iron_wall
    from core.cards.fire import create_ember, create_fireball, create_inferno
    from core.cards.poison import create_poison_dart, create_toxic_cloud
    from core.cards.water import create_water_splash, create_tidal_wave
    from core.relics.starter import LuckyClover, SpikedBracelet, ТочильныйКамень
    from core.relics.elemental import ДревнееОгниво, НамокшаяРукавица

    CARD_FACTORIES = [
        create_strike, create_defend, create_heavy_blade, create_iron_wall,
        create_ember, create_fireball, create_inferno,
        create_poison_dart, create_toxic_cloud,
        create_water_splash, create_tidal_wave,
    ]

    def heal(amount):
        def effect(gm):
            gm.player.hp = min(gm.player.hp + amount, gm.player.max_hp)
            gm.event_result = f"+{amount} HP"
        return effect

    def lose_hp(amount):
        def effect(gm):
            gm.player.hp = max(gm.player.hp - amount, 1)
            gm.event_result = f"-{amount} HP"
        return effect

    def gain_gold(amount):
        def effect(gm):
            gm.player_gold += amount
            gm.event_result = f"+{amount} золота"
        return effect

    def lose_gold(amount):
        def effect(gm):
            gm.player_gold = max(gm.player_gold - amount, 0)
            gm.event_result = f"-{amount} золота"
        return effect

    def gain_card(factory):
        def effect(gm):
            card = factory()
            gm.add_card(card)
            gm.event_result = f"Получена карта: {card.name}"
        return effect

    def gain_random_card():
        def effect(gm):
            card = random.choice(CARD_FACTORIES)()
            gm.add_card(card)
            gm.event_result = f"Получена карта: {card.name}"
        return effect

    def gain_relic(relic_cls):
        def effect(gm):
            r = relic_cls()
            gm.player_relics.append(r)
            gm.event_result = f"Получена реликвия: {r.name}"
        return effect

    def skip():
        def effect(gm):
            gm.event_result = "Вы прошли мимо."
        return effect

    return [
        {
            "title": "Таинственный алтарь",
            "text": (
                "Посреди тропы стоит древний алтарь.\n"
                "Камень покрыт рунами, от него исходит тепло.\n"
                "Что вы сделаете?"
            ),
            "options": [
                {"label": "Принести жертву (-15 HP, +реликвия)", "effect": [lose_hp(15), gain_relic(LuckyClover)]},
                {"label": "Помолиться (+20 HP)",                  "effect": [heal(20)]},
                {"label": "Пройти мимо",                          "effect": [skip()]},
            ],
        },
        {
            "title": "Брошенный лагерь",
            "text": (
                "Вы находите покинутый лагерь.\n"
                "Среди вещей — монеты и старая колода карт.\n"
                "Что возьмёте?"
            ),
            "options": [
                {"label": "Взять золото (+40 монет)",    "effect": [gain_gold(40)]},
                {"label": "Взять карту (случайная)",     "effect": [gain_random_card()]},
                {"label": "Взять и то, и то (-10 HP)",   "effect": [gain_gold(20), gain_random_card(), lose_hp(10)]},
            ],
        },
        {
            "title": "Торговец-призрак",
            "text": (
                "Полупрозрачный торговец предлагает сделку.\n"
                "«Твоя кровь или твоё золото — выбирай.»"
            ),
            "options": [
                {"label": "Заплатить золотом (-30, +карта)", "effect": [lose_gold(30), gain_random_card()]},
                {"label": "Заплатить кровью (-20 HP, +карта)", "effect": [lose_hp(20), gain_random_card()]},
                {"label": "Отказаться",                       "effect": [skip()]},
            ],
        },
        {
            "title": "Раненый путник",
            "text": (
                "На обочине лежит раненый путник.\n"
                "Он просит о помощи. Рядом — его сумка с монетами."
            ),
            "options": [
                {"label": "Помочь (-10 HP, +50 золота)",  "effect": [lose_hp(10), gain_gold(50)]},
                {"label": "Ограбить (+30 золота)",         "effect": [gain_gold(30)]},
                {"label": "Пройти мимо",                   "effect": [skip()]},
            ],
        },
        {
            "title": "Огненный дух",
            "text": (
                "Из трещины в земле вырывается огненный дух.\n"
                "Он предлагает силу в обмен на испытание."
            ),
            "options": [
                {"label": "Принять испытание (-25 HP, +реликвия)", "effect": [lose_hp(25), gain_relic(ДревнееОгниво)]},
                {"label": "Взять огненную карту",                   "effect": [gain_card(create_fireball)]},
                {"label": "Отступить",                              "effect": [skip()]},
            ],
        },
        {
            "title": "Подземный родник",
            "text": (
                "Вы находите чистый подземный родник.\n"
                "Вода светится голубым светом."
            ),
            "options": [
                {"label": "Выпить (+30 HP)",                        "effect": [heal(30)]},
                {"label": "Наполнить флягу (+15 HP, +водная карта)", "effect": [heal(15), gain_card(create_water_splash)]},
                {"label": "Пройти мимо",                            "effect": [skip()]},
            ],
        },
        {
            "title": "Старая библиотека",
            "text": (
                "Заброшенная библиотека. Полки ломятся от книг.\n"
                "Одна из них светится — внутри боевые техники."
            ),
            "options": [
                {"label": "Изучить технику (случайная карта)",  "effect": [gain_random_card()]},
                {"label": "Продать книгу (+35 золота)",          "effect": [gain_gold(35)]},
                {"label": "Взять обе (+карта, +20 золота, -15 HP)", "effect": [gain_random_card(), gain_gold(20), lose_hp(15)]},
            ],
        },
    ]


# ─── Состояние текущего события ─────────────────────────────────────────────
_current_event = None
_result_timer  = 0   # сколько кадров показывать результат


def init_event(gm):
    """Вызывается при входе в EVENT-комнату. Выбирает случайное событие."""
    global _current_event, _result_timer
    events = _make_events()
    _current_event = random.choice(events)
    _result_timer  = 0
    gm.event_result = None


def reset():
    global _current_event, _result_timer
    _current_event = None
    _result_timer  = 0


# ─── Отрисовка ───────────────────────────────────────────────────────────────
_BTN_COLOR        = (50, 50, 80)
_BTN_HOVER_COLOR  = (80, 80, 130)
_BTN_BORDER       = (180, 180, 255)
_RESULT_COLOR     = (100, 220, 100)
_TITLE_COLOR      = (255, 220, 60)
_TEXT_COLOR       = (210, 210, 210)
_BG_COLOR         = (15, 15, 25)
_PANEL_COLOR      = (25, 25, 45)

_option_rects = []   # хранит pygame.Rect кнопок для handle_clicks


def draw_screen(view):
    """Рисует экран события."""
    global _option_rects, _result_timer

    if _current_event is None:
        init_event(view.gm)

    screen = view.screen
    W, H   = screen.get_size()
    mouse  = pygame.mouse.get_pos()

    screen.fill(_BG_COLOR)

    # ── Панель ──────────────────────────────────────────────────────────────
    panel = pygame.Rect(W // 2 - 480, 80, 960, 900)
    pygame.draw.rect(screen, _PANEL_COLOR, panel, border_radius=16)
    pygame.draw.rect(screen, _BTN_BORDER,  panel, 2, border_radius=16)

    # ── Заголовок ───────────────────────────────────────────────────────────
    title_font = pygame.font.SysFont("Arial", 42, bold=True)
    title_surf = title_font.render(_current_event["title"], True, _TITLE_COLOR)
    screen.blit(title_surf, (W // 2 - title_surf.get_width() // 2, 120))

    # ── Текст события ────────────────────────────────────────────────────────
    text_font = pygame.font.SysFont("Arial", 26)
    lines = _current_event["text"].split("\n")
    y_text = 210
    for line in lines:
        surf = text_font.render(line, True, _TEXT_COLOR)
        screen.blit(surf, (W // 2 - surf.get_width() // 2, y_text))
        y_text += 38

    # ── Результат (если уже выбрали) ─────────────────────────────────────────
    if getattr(view.gm, "event_result", None):
        res_font = pygame.font.SysFont("Arial", 32, bold=True)
        res_surf = res_font.render(view.gm.event_result, True, _RESULT_COLOR)
        screen.blit(res_surf, (W // 2 - res_surf.get_width() // 2, y_text + 30))

        # Кнопка "Продолжить"
        cont_rect = pygame.Rect(W // 2 - 160, y_text + 100, 320, 60)
        hover = cont_rect.collidepoint(mouse)
        pygame.draw.rect(screen, _BTN_HOVER_COLOR if hover else _BTN_COLOR, cont_rect, border_radius=10)
        pygame.draw.rect(screen, _BTN_BORDER, cont_rect, 2, border_radius=10)
        btn_font = pygame.font.SysFont("Arial", 28, bold=True)
        lbl = btn_font.render("Продолжить ->", True, (255, 255, 255))
        screen.blit(lbl, (cont_rect.centerx - lbl.get_width() // 2,
                          cont_rect.centery - lbl.get_height() // 2))
        _option_rects.clear()
        _option_rects.append(("continue", cont_rect))
        return

    # ── Кнопки вариантов ─────────────────────────────────────────────────────
    _option_rects.clear()
    btn_font = pygame.font.SysFont("Arial", 24, bold=True)
    y_btn = y_text + 60
    for i, opt in enumerate(_current_event["options"]):
        btn_rect = pygame.Rect(W // 2 - 380, y_btn, 760, 64)
        hover = btn_rect.collidepoint(mouse)
        pygame.draw.rect(screen, _BTN_HOVER_COLOR if hover else _BTN_COLOR, btn_rect, border_radius=10)
        pygame.draw.rect(screen, _BTN_BORDER, btn_rect, 2, border_radius=10)
        lbl = btn_font.render(opt["label"], True, (255, 255, 255))
        screen.blit(lbl, (btn_rect.centerx - lbl.get_width() // 2,
                          btn_rect.centery - lbl.get_height() // 2))
        _option_rects.append((i, btn_rect))
        y_btn += 84


def handle_clicks(view, mouse_pos):
    """Обрабатывает клики на экране события."""
    global _result_timer

    if _current_event is None:
        return

    for tag, rect in _option_rects:
        if rect.collidepoint(mouse_pos):
            if tag == "continue":
                # Переход дальше
                reset()
                view.gm.event_result = None
                view.gm.current_floor += 1
                view.gm.setup_next_floor()
                return

            # Применяем все эффекты варианта
            opt = _current_event["options"][tag]
            for eff in opt["effect"]:
                eff(view.gm)
            return