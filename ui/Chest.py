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


CHEST_CARD_POOL = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_ignite, create_fire_breath,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
    create_flex, create_battle_cry,
    create_thorn_armor,
    create_bash,
    create_neutralize, create_intimidate,
]

# Пул баффов проклятого сундука: (название, описание, цена HP, функция применения)
# Функция принимает (gm) и применяет эффект
CURSED_BUFF_POOL = [
    (
        "+3 Ярости",
        "Постоянный бонус +3 к урону всех атак.",
        15,
        lambda gm: setattr(gm.player, "strength",
                           getattr(gm.player, "strength", 0) + 3),
    ),
    (
        "+5 Шипов",
        "Постоянный бонус: отражать +5 урона атакующему.",
        12,
        lambda gm: setattr(gm.player, "thorns",
                           getattr(gm.player, "thorns", 0) + 5),
    ),
    (
        "+1 Энергия",
        "Максимальная энергия +1 навсегда.",
        20,
        lambda gm: setattr(gm.player, "max_energy", gm.player.max_energy + 1),
    ),
    (
        "+15 Щита",
        "Немедленно получить 15 щита.",
        10,
        lambda gm: gm.player.gain_shield(15),
    ),
    (
        "+25 Золота",
        "Найти 25 монет в тёмных глубинах сундука.",
        8,
        lambda gm: setattr(gm, "player_gold", gm.player_gold + 25),
    ),
    (
        "+1 Карта/ход",
        "Добирать на 1 карту больше в начале каждого боя.",
        18,
        lambda gm: setattr(gm.player, "bonus_draw",
                           getattr(gm.player, "bonus_draw", 0) + 1),
    ),
]


CHEST_TYPES   = ["common", "locked", "cursed"]
CHEST_WEIGHTS = [33, 33, 34]


def pick_chest_type():
    return random.choices(CHEST_TYPES, weights=CHEST_WEIGHTS, k=1)[0]


def generate_chest_cards(count=2):
    factories = random.sample(CHEST_CARD_POOL, min(count, len(CHEST_CARD_POOL)))
    return [factory() for factory in factories]


def generate_cursed_buffs(count=3):
    """Случайные баффы из пула (без повторов)."""
    return random.sample(CURSED_BUFF_POOL, min(count, len(CURSED_BUFF_POOL)))


class Chest:
    """Экран сундука: обычный / закрытый / проклятый."""

    BG_COLOR     = (15, 12, 25)
    TEXT_COLOR   = (200, 200, 200)
    BTN_COLOR    = (40, 40, 60)
    BTN_BORDER   = (255, 255, 255)
    BTN_HOVER    = (70, 70, 100)
    GOLD_COLOR   = (255, 210, 50)
    HP_COLOR     = (220, 80, 80)
    SKIP_COLOR   = (120, 120, 140)

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

    CARD_W = 180
    CARD_H = 250

    # ------------------------------------------------------------------ ИНИЦИАЛИЗАЦИЯ

    @staticmethod
    def init_chest(view):
        gm = view.gm
        chest_type = pick_chest_type()
        gm.chest_type     = chest_type
        gm.chest_selected = None
        gm.chest_opened   = False

        if chest_type == "common":
            gm.chest_cards = generate_chest_cards(2)
            gm.chest_gold  = 0

        elif chest_type == "locked":
            gm.chest_cards = generate_chest_cards(4)
            gm.chest_gold  = random.randint(30, 60)

        elif chest_type == "cursed":
            gm.chest_cards        = []
            gm.chest_gold         = 0
            gm.cursed_buffs       = generate_cursed_buffs(3)   # список кортежей
            gm.cursed_taken       = set()                       # индексы взятых баффов

    # ------------------------------------------------------------------ ОТРИСОВКА

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

        if chest_type == "common":
            Chest._draw_common(view, screen, sub_font, card_font, desc_font, small_font)
        elif chest_type == "locked":
            Chest._draw_locked(view, screen, sub_font, card_font, desc_font, small_font)
        elif chest_type == "cursed":
            Chest._draw_cursed(view, screen, sub_font, card_font, desc_font)

    # ------------------------------------------------------------------ ОБЫЧНЫЙ

    @staticmethod
    def _draw_common(view, screen, sub_font, card_font, desc_font, small_font):
        gm    = view.gm
        cards = getattr(gm, "chest_cards", [])

        hint = "Выбери одну карту:" if not gm.chest_opened else "Карта добавлена в колоду!"
        h = sub_font.render(hint, True, Chest.TEXT_COLOR)
        screen.blit(h, (960 - h.get_width() // 2, 130))

        Chest._draw_card_row(view, screen, cards, card_font, desc_font, cy=300)

        if not gm.chest_opened:
            Chest._draw_take_skip_buttons(view, screen, card_font)
        else:
            Chest._draw_continue_button(view, screen, card_font)

    # ------------------------------------------------------------------ ЗАКРЫТЫЙ

    @staticmethod
    def _draw_locked(view, screen, sub_font, card_font, desc_font, small_font):
        gm      = view.gm
        has_key = getattr(gm, "player_keys", 0) > 0
        cards   = getattr(gm, "chest_cards", [])

        key_text  = f"[КЛЮЧ x{gm.player_keys}]" if has_key else "[НЕТ КЛЮЧА]"
        key_color = (255, 215, 0) if has_key else (160, 80, 80)
        ks = sub_font.render(key_text, True, key_color)
        screen.blit(ks, (960 - ks.get_width() // 2, 115))

        if not has_key and not gm.chest_opened:
            msg = sub_font.render(
                "Для открытия нужен ключ. Ключи выпадают с боссов.",
                True, Chest.TEXT_COLOR
            )
            screen.blit(msg, (960 - msg.get_width() // 2, 320))
            Chest._draw_leave_button(view, screen, card_font)
            return

        hint = "Выбери одну карту (4 на выбор):" if not gm.chest_opened else "Карта добавлена в колоду!"
        h = sub_font.render(hint, True, Chest.TEXT_COLOR)
        screen.blit(h, (960 - h.get_width() // 2, 160))

        if not gm.chest_opened and getattr(gm, "chest_gold", 0) > 0:
            g = sub_font.render(
                f"+ {gm.chest_gold} золота (при взятии карты)",
                True, Chest.GOLD_COLOR
            )
            screen.blit(g, (960 - g.get_width() // 2, 200))

        Chest._draw_card_row(view, screen, cards, card_font, desc_font, cy=270)

        if not gm.chest_opened:
            Chest._draw_take_skip_buttons(view, screen, card_font)
        else:
            Chest._draw_continue_button(view, screen, card_font)

    # ------------------------------------------------------------------ ПРОКЛЯТЫЙ

    @staticmethod
    def _draw_cursed(view, screen, sub_font, card_font, desc_font):
        gm     = view.gm
        buffs  = getattr(gm, "cursed_buffs", [])
        taken  = getattr(gm, "cursed_taken", set())
        mouse  = pygame.mouse.get_pos()

        # Подзаголовок
        hint = sub_font.render(
            "Выбери баффы. Каждый стоит HP. Можно взять несколько.",
            True, (200, 160, 255)
        )
        screen.blit(hint, (960 - hint.get_width() // 2, 115))

        # Текущее HP
        hp_surf = sub_font.render(
            f"HP: {gm.player.hp} / {gm.player.max_hp}",
            True, Chest.HP_COLOR
        )
        screen.blit(hp_surf, (960 - hp_surf.get_width() // 2, 155))

        # Карточки баффов
        card_w, card_h = 260, 160
        spacing        = 300
        count          = len(buffs)
        total_w        = count * spacing
        start_x        = 960 - total_w // 2 + spacing // 2 - card_w // 2

        for i, (name, desc, cost, _apply) in enumerate(buffs):
            cx   = start_x + i * spacing
            cy   = 280
            rect = pygame.Rect(cx, cy, card_w, card_h)

            is_taken   = (i in taken)
            is_hovered = rect.collidepoint(mouse) and not is_taken
            can_afford = gm.player.hp - cost >= 1

            # Фон карточки
            if is_taken:
                bg_color     = (25, 40, 25)
                border_color = (60, 120, 60)
                border_w     = 2
            elif is_hovered and can_afford:
                bg_color     = (60, 30, 80)
                border_color = (220, 100, 255)
                border_w     = 3
            elif not can_afford:
                bg_color     = (30, 20, 30)
                border_color = (80, 50, 80)
                border_w     = 1
            else:
                bg_color     = (35, 20, 50)
                border_color = (140, 60, 200)
                border_w     = 2

            pygame.draw.rect(screen, bg_color,     rect, border_radius=8)
            pygame.draw.rect(screen, border_color, rect, border_w, border_radius=8)

            # Название баффа
            name_color = (180, 255, 180) if is_taken else (220, 180, 255)
            n = card_font.render(name, True, name_color)
            screen.blit(n, (rect.centerx - n.get_width() // 2, cy + 14))

            # Описание
            d = desc_font.render(desc, True, (170, 170, 190))
            screen.blit(d, (rect.centerx - d.get_width() // 2, cy + 56))

            # Цена / статус
            if is_taken:
                status_surf = card_font.render("ВЗЯТО", True, (100, 220, 100))
                screen.blit(status_surf,
                            (rect.centerx - status_surf.get_width() // 2, cy + 100))
            else:
                cost_color = (220, 80, 80) if not can_afford else (255, 120, 120)
                cost_surf  = card_font.render(f"-{cost} HP", True, cost_color)
                screen.blit(cost_surf,
                            (rect.centerx - cost_surf.get_width() // 2, cy + 100))

                if not can_afford:
                    warn = desc_font.render("Недостаточно HP", True, (160, 80, 80))
                    screen.blit(warn,
                                (rect.centerx - warn.get_width() // 2, cy + 130))

        # Кнопка "Уйти"
        Chest._draw_leave_button(view, screen, card_font, y=520)

    # ------------------------------------------------------------------ ОБЩИЕ ХЕЛПЕРЫ

    @staticmethod
    def _draw_card_row(view, screen, cards, card_font, desc_font, cy=300):
        gm      = view.gm
        count   = len(cards)
        if count == 0:
            return
        spacing = 220
        total_w = count * spacing
        start_x = 960 - total_w // 2 + spacing // 2 - Chest.CARD_W // 2
        mouse   = pygame.mouse.get_pos()

        for i, card in enumerate(cards):
            cx   = start_x + i * spacing
            rect = pygame.Rect(cx, cy, Chest.CARD_W, Chest.CARD_H)
            is_hovered  = rect.collidepoint(mouse) if not gm.chest_opened else False
            is_selected = (gm.chest_selected == i)

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

    @staticmethod
    def _draw_take_skip_buttons(view, screen, card_font):
        gm    = view.gm
        mouse = pygame.mouse.get_pos()

        take_rect   = pygame.Rect(760, 620, 200, 60)
        can_take    = gm.chest_selected is not None
        take_col    = Chest.BTN_HOVER if (take_rect.collidepoint(mouse) and can_take) else Chest.BTN_COLOR
        take_border = (100, 220, 100) if can_take else (80, 80, 80)
        pygame.draw.rect(screen, take_col, take_rect)
        pygame.draw.rect(screen, take_border, take_rect, 2)
        lbl = card_font.render("Взять", True, (200, 255, 200) if can_take else (100, 100, 100))
        screen.blit(lbl, (take_rect.centerx - lbl.get_width() // 2,
                          take_rect.centery - lbl.get_height() // 2))

        skip_rect = pygame.Rect(980, 620, 200, 60)
        skip_col  = Chest.BTN_HOVER if skip_rect.collidepoint(mouse) else Chest.BTN_COLOR
        pygame.draw.rect(screen, skip_col, skip_rect)
        pygame.draw.rect(screen, Chest.SKIP_COLOR, skip_rect, 2)
        slbl = card_font.render("Пропустить", True, Chest.SKIP_COLOR)
        screen.blit(slbl, (skip_rect.centerx - slbl.get_width() // 2,
                           skip_rect.centery - slbl.get_height() // 2))

    @staticmethod
    def _draw_leave_button(view, screen, card_font, y=500):
        mouse = pygame.mouse.get_pos()
        btn   = pygame.Rect(760, y, 400, 60)
        col   = Chest.BTN_HOVER if btn.collidepoint(mouse) else Chest.BTN_COLOR
        pygame.draw.rect(screen, col, btn)
        pygame.draw.rect(screen, Chest.SKIP_COLOR, btn, 2)
        lbl = card_font.render("Уйти", True, Chest.SKIP_COLOR)
        screen.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                          btn.centery - lbl.get_height() // 2))

    @staticmethod
    def _draw_continue_button(view, screen, font):
        mouse = pygame.mouse.get_pos()
        btn   = pygame.Rect(760, 700, 400, 60)
        col   = Chest.BTN_HOVER if btn.collidepoint(mouse) else Chest.BTN_COLOR
        pygame.draw.rect(screen, col, btn)
        pygame.draw.rect(screen, Chest.BTN_BORDER, btn, 2)
        lbl = font.render("Продолжить ->", True, (255, 255, 255))
        screen.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                          btn.centery - lbl.get_height() // 2))

    # ------------------------------------------------------------------ КЛИКИ

    @staticmethod
    def handle_clicks(view, mouse_pos):
        gm         = view.gm
        chest_type = getattr(gm, "chest_type", "common")

        if chest_type == "common":
            Chest._clicks_common(view, mouse_pos)
        elif chest_type == "locked":
            Chest._clicks_locked(view, mouse_pos)
        elif chest_type == "cursed":
            Chest._clicks_cursed(view, mouse_pos)

    @staticmethod
    def _clicks_common(view, mouse_pos):
        gm = view.gm

        if gm.chest_opened:
            if pygame.Rect(760, 700, 400, 60).collidepoint(mouse_pos):
                gm.current_floor += 1
                gm.setup_next_floor()
            return

        cards   = getattr(gm, "chest_cards", [])
        count   = len(cards)
        spacing = 220
        total_w = count * spacing
        start_x = 960 - total_w // 2 + spacing // 2 - Chest.CARD_W // 2

        for i in range(count):
            rect = pygame.Rect(start_x + i * spacing, 300, Chest.CARD_W, Chest.CARD_H)
            if rect.collidepoint(mouse_pos):
                gm.chest_selected = i
                return

        if pygame.Rect(760, 620, 200, 60).collidepoint(mouse_pos) and gm.chest_selected is not None:
            gm.add_card(gm.chest_cards[gm.chest_selected])
            gm.chest_opened = True
            return

        if pygame.Rect(980, 620, 200, 60).collidepoint(mouse_pos):
            gm.current_floor += 1
            gm.setup_next_floor()

    @staticmethod
    def _clicks_locked(view, mouse_pos):
        gm      = view.gm
        has_key = getattr(gm, "player_keys", 0) > 0

        if not has_key and not gm.chest_opened:
            if pygame.Rect(760, 500, 400, 60).collidepoint(mouse_pos):
                gm.current_floor += 1
                gm.setup_next_floor()
            return

        if gm.chest_opened:
            if pygame.Rect(760, 700, 400, 60).collidepoint(mouse_pos):
                gm.current_floor += 1
                gm.setup_next_floor()
            return

        cards   = getattr(gm, "chest_cards", [])
        count   = len(cards)
        spacing = 220
        total_w = count * spacing
        start_x = 960 - total_w // 2 + spacing // 2 - Chest.CARD_W // 2

        for i in range(count):
            rect = pygame.Rect(start_x + i * spacing, 270, Chest.CARD_W, Chest.CARD_H)
            if rect.collidepoint(mouse_pos):
                gm.chest_selected = i
                return

        if pygame.Rect(760, 620, 200, 60).collidepoint(mouse_pos) and gm.chest_selected is not None:
            gm.add_card(gm.chest_cards[gm.chest_selected])
            gm.player_gold  += getattr(gm, "chest_gold", 0)
            gm.player_keys  -= 1
            gm.chest_opened  = True
            return

        if pygame.Rect(980, 620, 200, 60).collidepoint(mouse_pos):
            gm.current_floor += 1
            gm.setup_next_floor()

    @staticmethod
    def _clicks_cursed(view, mouse_pos):
        gm    = view.gm
        buffs = getattr(gm, "cursed_buffs", [])
        taken = getattr(gm, "cursed_taken", set())

        # Клик по карточке баффа
        card_w, card_h = 260, 160
        spacing        = 300
        count          = len(buffs)
        total_w        = count * spacing
        start_x        = 960 - total_w // 2 + spacing // 2 - card_w // 2

        for i, (name, desc, cost, apply_fn) in enumerate(buffs):
            if i in taken:
                continue
            rect = pygame.Rect(start_x + i * spacing, 280, card_w, card_h)
            if rect.collidepoint(mouse_pos):
                if gm.player.hp - cost >= 1:          # нельзя умереть
                    gm.player.hp -= cost
                    apply_fn(gm)
                    taken.add(i)
                    gm.cursed_taken = taken
                return

        # Кнопка "Уйти"
        if pygame.Rect(760, 520, 400, 60).collidepoint(mouse_pos):
            gm.current_floor += 1
            gm.setup_next_floor()