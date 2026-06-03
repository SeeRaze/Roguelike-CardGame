import pygame
from ui.CardRenderer import CardRenderer

# ──────────────────────────────────────────────
#  Палитра (единый стиль с MainMenu)
# ──────────────────────────────────────────────
_BG_COLOR        = (10,  10,  20)
_PANEL_COLOR     = (20,  20,  40)
_BTN_COLOR       = (40,  40,  75)
_BTN_HOVER_COLOR = (70,  70, 120)
_BTN_BORDER      = (160, 160, 255)
_TITLE_COLOR     = (255, 220,  60)
_TEXT_COLOR      = (200, 200, 220)
_MUTED_COLOR     = (110, 110, 140)
_GOLD_COLOR      = (255, 215,   0)
_START_COLOR     = (30,  110,  30)
_START_HOVER     = (50,  160,  50)

# ──────────────────────────────────────────────
#  Описания классов
# ──────────────────────────────────────────────
CLASS_INFO = {
    "Warrior": {
        "label": "ВОИН",
        "color": (200, 80, 80),
        "stats": "HP: 80  |  Энергия: 3",
        "lines": [
            "Щиты, шипы, тяжёлый урон.",
            "",
            "Пассив:",
            "30% щита переносится",
            "на следующий ход.",
            "",
            "Активная:",
            "Щитовой удар —",
            "урон = 50% щита.",
        ],
    },
    "Rogue": {
        "label": "РАЗБОЙНИК",
        "color": (160, 100, 220),
        "stats": "HP: 65  |  Энергия: 4",
        "lines": [
            "Серии быстрых ударов,",
            "кровотечение.",
            "",
            "Пассив:",
            "Каждый ход 1 карта",
            "в руке стоит на 1 дешевле.",
            "",
            "Активная:",
            "Вскрытие —",
            "удвоить bleed врага.",
        ],
    },
    "Mage": {
        "label": "МАГ",
        "color": (80, 160, 220),
        "stats": "HP: 55  |  Энергия: 3",
        "lines": [
            "Стихийные комбо:",
            "огонь + вода.",
            "",
            "Пассив:",
            "Комбо Пар —",
            "добрать 1 карту.",
            "",
            "Активная:",
            "Стихийный барьер —",
            "блок стихий + щит.",
        ],
    },
    "Druid": {
        "label": "ДРУИД",
        "color": (60, 180, 80),
        "stats": "HP: 70  |  Энергия: 3",
        "lines": [
            "Реген, хил,",
            "медленный яд.",
            "",
            "Пассив:",
            "Каждый хил —",
            "яд на врага.",
            "",
            "Активная:",
            "Токсичный взрыв —",
            "весь яд врага разом.",
        ],
    },
    "Berserker": {
        "label": "БЕРСЕРК",
        "color": (220, 60, 40),
        "stats": "HP: 60  |  Энергия: 3",
        "lines": [
            "Чем меньше HP —",
            "тем больше урон.",
            "",
            "Пассив:",
            "Ярость крови от",
            "недостатка HP.",
            "",
            "Активная:",
            "Кровавая ярость —",
            "-10% HP, +Ярость x2.",
        ],
    },
}

ANIM_SPEED     = 3.0
CARD_SPREAD    = 160
CARD_W, CARD_H = 180, 250
SCREEN_W       = 1920
SCREEN_H       = 1080

# Геометрия карточек классов
_CLS_W    = 300    # ширина карточки класса
_CLS_H    = 260    # высота карточки класса
_CLS_GAP  = 24     # зазор между карточками
_CLS_Y    = 160    # Y верхнего края карточек
# Суммарная ширина 5 карточек: 5*300 + 4*24 = 1596
_CLS_TOTAL = 5 * _CLS_W + 4 * _CLS_GAP
_CLS_X0    = (SCREEN_W - _CLS_TOTAL) // 2   # = 162


class HubView:
    """Отрисовка и логика Мета-Хаба: выбор класса + анимированная стопка карт."""

    def __init__(self):
        self.hover_progress:  float = 0.0
        self.is_deck_hovered: bool  = False
        self.class_buttons:   dict  = {}
        self.is_start_hovered: bool = False

    def reset(self):
        self.hover_progress   = 0.0
        self.is_deck_hovered  = False
        self.is_start_hovered = False

    def update(self, dt: float):
        target = 1.0 if self.is_deck_hovered else 0.0
        step   = ANIM_SPEED * dt
        if self.hover_progress < target:
            self.hover_progress = min(self.hover_progress + step, 1.0)
        elif self.hover_progress > target:
            self.hover_progress = max(self.hover_progress - step, 0.0)

    # ──────────────────────────────────────────
    #  DRAW
    # ──────────────────────────────────────────
    def draw(self, view):
        screen    = view.screen
        gm        = view.gm
        mouse_pos = pygame.mouse.get_pos()

        screen.fill(_BG_COLOR)

        # Шрифты
        font_title  = pygame.font.SysFont("Arial", 42, bold=True)
        font_gold   = pygame.font.SysFont("Arial", 26, bold=True)
        font_hint   = pygame.font.SysFont("Arial", 22)

        # Заголовок
        t = font_title.render("=== ВАШ ЛАГЕРЬ ===", True, _TITLE_COLOR)
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 50))

        # Золото
        g = font_gold.render(f"Золото: {gm.player_gold}", True, _GOLD_COLOR)
        screen.blit(g, (SCREEN_W // 2 - g.get_width() // 2, 108))

        # Разделитель под заголовком
        pygame.draw.line(screen, _BTN_BORDER,
                         (SCREEN_W // 2 - 400, 148),
                         (SCREEN_W // 2 + 400, 148), 1)

        self._draw_class_selector(view, screen, gm, mouse_pos)
        self._draw_deck_section(view, screen, gm, mouse_pos, font_hint)
        self._draw_start_button(view, screen, mouse_pos)

    # ──────────────────────────────────────────
    #  ВЫБОР КЛАССА
    # ──────────────────────────────────────────
    def _draw_class_selector(self, view, screen, gm, mouse_pos):
        font_label = pygame.font.SysFont("Arial", 22, bold=True)
        font_stats = pygame.font.SysFont("Arial", 17, bold=True)
        font_desc  = pygame.font.SysFont("Arial", 16)

        selected_name  = type(gm.player).__name__
        self.class_buttons = {}

        for i, (cls_name, info) in enumerate(CLASS_INFO.items()):
            bx   = _CLS_X0 + i * (_CLS_W + _CLS_GAP)
            by   = _CLS_Y
            rect = pygame.Rect(bx, by, _CLS_W, _CLS_H)
            self.class_buttons[cls_name] = rect

            is_selected = (cls_name == selected_name)
            is_hovered  = rect.collidepoint(mouse_pos)

            # Фон карточки
            if is_selected:
                bg = tuple(min(c + 30, 255) for c in info["color"])
                bg = (max(bg[0] - 60, 20), max(bg[1] - 60, 20), max(bg[2] - 60, 20))
                # Тёмный оттенок цвета класса
                bg = (
                    min(info["color"][0] // 3 + 15, 80),
                    min(info["color"][1] // 3 + 15, 80),
                    min(info["color"][2] // 3 + 15, 80),
                )
            elif is_hovered:
                bg = (30, 30, 55)
            else:
                bg = _PANEL_COLOR

            pygame.draw.rect(screen, bg, rect, border_radius=12)

            # Рамка
            if is_selected:
                border_col = info["color"]
                border_w   = 3
            elif is_hovered:
                border_col = _BTN_BORDER
                border_w   = 2
            else:
                border_col = (60, 60, 90)
                border_w   = 1
            pygame.draw.rect(screen, border_col, rect, border_w, border_radius=12)

            # Цветная полоска сверху
            stripe = pygame.Rect(bx + border_w, by + border_w,
                                 _CLS_W - border_w * 2, 6)
            pygame.draw.rect(screen, info["color"], stripe,
                             border_radius=4)

            # Название класса
            lbl = font_label.render(info["label"], True, (255, 255, 255))
            screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, by + 18))

            # Разделитель под названием
            pygame.draw.line(screen, border_col,
                             (bx + 16, by + 46),
                             (bx + _CLS_W - 16, by + 46), 1)

            # Статы (HP / Энергия)
            st = font_stats.render(info["stats"], True,
                                   _TITLE_COLOR if is_selected else _MUTED_COLOR)
            screen.blit(st, (rect.centerx - st.get_width() // 2, by + 54))

            # Описание — строки внутри карточки
            line_h = 20
            text_y = by + 82
            for line in info["lines"]:
                if line == "":
                    text_y += 8
                    continue
                # «Пассив:» выделяем цветом класса
                if line in ("Пассив:", "Активная:"):
                    col = info["color"]
                    fnt = font_stats
                else:
                    col = _TEXT_COLOR if is_selected else _MUTED_COLOR
                    fnt = font_desc
                surf = fnt.render(line, True, col)
                screen.blit(surf, (rect.centerx - surf.get_width() // 2, text_y))
                text_y += line_h

    # ──────────────────────────────────────────
    #  СТОПКА КАРТ
    # ──────────────────────────────────────────
    def _draw_deck_section(self, view, screen, gm, mouse_pos, font_hint):
        deck  = gm.current_deck
        count = len(deck)
        prog  = self.hover_progress

        # Центрируем стопку
        stack_y = _CLS_Y + _CLS_H + 50

        max_spread   = SCREEN_W - CARD_W - 80
        spread_total = min((count - 1) * CARD_SPREAD * prog, max_spread)

        if count > 1 and prog > 0.01:
            card_step = int(spread_total / (count - 1))
        else:
            card_step = CARD_SPREAD

        # Центрируем раскладку
        total_w  = int(spread_total) + CARD_W if prog > 0.01 else CARD_W
        stack_x  = (SCREEN_W - total_w) // 2

        hover_zone = pygame.Rect(
            stack_x - 10, stack_y - 10,
            total_w + 20, CARD_H + 20
        )
        self.is_deck_hovered = hover_zone.collidepoint(mouse_pos)

        if prog < 0.01:
            stack_rect = pygame.Rect(stack_x, stack_y, CARD_W, CARD_H)
            self._draw_card_back(screen, stack_rect)

            font_num  = pygame.font.SysFont("Arial", 36, bold=True)
            font_sub  = pygame.font.SysFont("Arial", 16)
            n = font_num.render(str(count), True, (255, 255, 255))
            screen.blit(n, (stack_rect.centerx - n.get_width() // 2,
                            stack_rect.centery - 24))
            s = font_sub.render("карт в колоде", True, _MUTED_COLOR)
            screen.blit(s, (stack_rect.centerx - s.get_width() // 2,
                            stack_rect.centery + 16))
        else:
            for i, card in enumerate(deck):
                CardRenderer.draw(
                    surface    = screen,
                    card       = card,
                    x          = stack_x + i * card_step,
                    y          = stack_y,
                    font_title = view.card_font,
                    font_desc  = view.card_desc_font,
                    is_hovered = False,
                )

        label = "Наведите для просмотра" if prog < 0.5 else "Стартовая колода"
        lbl   = font_hint.render(label, True, _MUTED_COLOR)
        screen.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2,
                          stack_y + CARD_H + 12))

    @staticmethod
    def _draw_card_back(screen, rect):
        pygame.draw.rect(screen, (25, 25, 45), rect, border_radius=10)
        pygame.draw.rect(screen, _BTN_BORDER,  rect, 2,  border_radius=10)
        inner = rect.inflate(-16, -16)
        pygame.draw.rect(screen, (35, 35, 60), inner, border_radius=6)
        pygame.draw.rect(screen, _BTN_BORDER,  inner, 1, border_radius=6)

    # ──────────────────────────────────────────
    #  КНОПКА СТАРТА
    # ──────────────────────────────────────────
    def _draw_start_button(self, view, screen, mouse_pos):
        btn_w, btn_h = 520, 72
        bx = SCREEN_W // 2 - btn_w // 2
        by = SCREEN_H - 120
        btn = pygame.Rect(bx, by, btn_w, btn_h)
        view.btn_start_run    = btn
        self.is_start_hovered = btn.collidepoint(mouse_pos)

        color = _START_HOVER if self.is_start_hovered else _START_COLOR
        pygame.draw.rect(screen, color,      btn, border_radius=12)
        pygame.draw.rect(screen, (100, 220, 100), btn, 2, border_radius=12)

        font_btn = pygame.font.SysFont("Arial", 26, bold=True)
        lbl = font_btn.render("ПОДНЯТЬСЯ В БАШНЮ  [В БОЙ]", True, (255, 255, 255))
        screen.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                          btn.centery - lbl.get_height() // 2))

    # ──────────────────────────────────────────
    #  HANDLE CLICK
    # ──────────────────────────────────────────
    def handle_click(self, view, mouse_pos):
        gm = view.gm

        for cls_name, rect in self.class_buttons.items():
            if rect.collidepoint(mouse_pos):
                self._select_class(gm, cls_name)
                return

        if hasattr(view, 'btn_start_run') and \
                view.btn_start_run.collidepoint(mouse_pos):
            print(f" >>> СТАРТ ЗАБЕГА | Класс: {type(gm.player).__name__} <<<")
            self.reset()
            gm.current_floor = 1
            gm.player.hp     = gm.player.max_hp
            gm.setup_next_floor()

    @staticmethod
    def _select_class(gm, cls_name: str):
        from core.players import Warrior, Rogue, Mage, Druid, Berserker
        CLASS_MAP = {
            "Warrior":   Warrior,
            "Rogue":     Rogue,
            "Mage":      Mage,
            "Druid":     Druid,
            "Berserker": Berserker,
        }
        if cls_name not in CLASS_MAP:
            return
        if type(gm.player).__name__ == cls_name:
            return
        gm.player       = CLASS_MAP[cls_name]()
        gm.current_deck = gm.player.get_starter_deck()
        print(f"[HubView] Выбран класс: {cls_name}")