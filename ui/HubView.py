import pygame
from ui.CardRenderer import CardRenderer

# ──────────────────────────────────────────────
#  Описания классов для отображения в хабе
# ──────────────────────────────────────────────
CLASS_INFO = {
    "Warrior": {
        "label":  "ВОИН",
        "color":  (200, 80,  80),
        "desc": [
            "HP: 80  |  Энергия: 3",
            "Щиты, шипы, тяжёлый урон.",
            "Стартует с Тяжёлым Клинком.",
        ],
    },
    "Rogue": {
        "label":  "РАЗБОЙНИК",
        "color":  (160, 100, 220),
        "desc": [
            "HP: 65  |  Энергия: 4",
            "Серии быстрых ударов, кровь.",
            "Каждый ход: 1 карта дешевле.",
        ],
    },
    "Mage": {
        "label":  "МАГ",
        "color":  (80,  160, 220),
        "desc": [
            "HP: 55  |  Энергия: 3",
            "Стихийные комбо: огонь+вода.",
            "Стартует с Поджогом и Всплеском.",
        ],
    },
    "Druid": {
        "label":  "ДРУИД",
        "color":  (60,  180, 80),
        "desc": [
            "HP: 70  |  Энергия: 3",
            "Реген, хил и медленный яд.",
            "Стартует с Перевязкой и Регеном.",
        ],
    },
    "Berserker": {
        "label":  "БЕРСЕРК",
        "color":  (220, 60,  40),
        "desc": [
            "HP: 60  |  Энергия: 3",
            "Чем меньше HP -- тем больше урон.",
            "Стартует с Тяжёлым Клинком x2.",
        ],
    },
}

ANIM_SPEED   = 3.0
CARD_SPREAD  = 160
CARD_W, CARD_H = 180, 250
SCREEN_W     = 1920   # для ограничения ширины раскладки


class HubView:
    """Отрисовка и логика Мета-Хаба: выбор класса + анимированная стопка карт."""

    def __init__(self):
        self.hover_progress: float = 0.0
        self.is_deck_hovered: bool = False
        self.class_buttons: dict = {}
        self.is_start_hovered: bool = False

    # ──────────────────────────────────────────
    #  RESET (БАГ 3: вызывать при старте нового забега)
    # ──────────────────────────────────────────
    def reset(self):
        """Сбрасывает состояние анимации. Вызывать при старте забега."""
        self.hover_progress  = 0.0
        self.is_deck_hovered = False
        self.is_start_hovered = False

    # ──────────────────────────────────────────
    #  UPDATE
    # ──────────────────────────────────────────
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
        screen     = view.screen
        gm         = view.gm
        mouse_pos  = pygame.mouse.get_pos()

        screen.fill((25, 25, 30))

        view.draw_text("=== ВАШ ЛАГЕРЬ ===", view.main_font,
                       (255, 255, 255), 100, 40)
        view.draw_text(f"Золото: {gm.player_gold}",
                       view.ui_font, (240, 240, 70), 100, 95)

        self._draw_class_selector(view, screen, gm, mouse_pos)
        self._draw_deck_stack(view, screen, gm, mouse_pos)
        self._draw_start_button(view, screen, mouse_pos)

    # ──────────────────────────────────────────
    #  ВЫБОР КЛАССА
    # ──────────────────────────────────────────
    def _draw_class_selector(self, view, screen, gm, mouse_pos):
        view.draw_text("Выберите класс:", view.ui_font,
                       (180, 180, 180), 100, 155)

        selected_name = type(gm.player).__name__
        self.class_buttons = {}

        btn_w, btn_h = 220, 70
        start_x      = 100
        gap          = 260

        for i, (cls_name, info) in enumerate(CLASS_INFO.items()):
            bx = start_x + i * gap
            by = 195
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            self.class_buttons[cls_name] = rect

            is_selected = (cls_name == selected_name)
            is_hovered  = rect.collidepoint(mouse_pos)

            if is_selected:
                bg = tuple(min(c + 40, 255) for c in info["color"])
            elif is_hovered:
                bg = tuple(min(c + 20, 255) for c in info["color"])
            else:
                bg = (45, 45, 50)

            pygame.draw.rect(screen, bg, rect, border_radius=8)
            border_col = info["color"] if (is_selected or is_hovered) else (80, 80, 85)
            border_w   = 3 if is_selected else 2
            pygame.draw.rect(screen, border_col, rect, border_w, border_radius=8)

            lbl_surf = view.card_font.render(info["label"], True, (255, 255, 255))
            lx = rect.x + (rect.width - lbl_surf.get_width()) // 2
            screen.blit(lbl_surf, (lx, rect.y + 22))

            for j, line in enumerate(info["desc"]):
                col = (200, 200, 200) if is_selected else (120, 120, 120)
                view.draw_text(line, view.card_desc_font, col, bx, by + btn_h + 10 + j * 20)

    # ──────────────────────────────────────────
    #  СТОПКА КАРТ
    # ──────────────────────────────────────────
    def _draw_deck_stack(self, view, screen, gm, mouse_pos):
        deck   = gm.current_deck
        count  = len(deck)
        prog   = self.hover_progress

        stack_x, stack_y = 100, 430

        # БАГ 4: ограничиваем spread_total шириной экрана
        max_spread   = SCREEN_W - stack_x - CARD_W - 40
        spread_total = min((count - 1) * CARD_SPREAD * prog, max_spread)

        # Адаптивный шаг между картами при большой колоде
        if count > 1:
            card_step = int(spread_total / (count - 1)) if count > 1 else CARD_SPREAD
        else:
            card_step = CARD_SPREAD

        hover_zone = pygame.Rect(
            stack_x - 10,
            stack_y - 10,
            int(spread_total) + CARD_W + 20,
            CARD_H + 20
        )
        self.is_deck_hovered = hover_zone.collidepoint(mouse_pos)

        if prog < 0.01:
            stack_rect = pygame.Rect(stack_x, stack_y, CARD_W, CARD_H)
            self._draw_card_back(screen, stack_rect, view.ui_font)
            count_surf = view.main_font.render(str(count), True, (255, 255, 255))
            cx = stack_rect.x + (CARD_W - count_surf.get_width()) // 2
            screen.blit(count_surf, (cx, stack_rect.y + CARD_H // 2 - 20))
            hint_surf = view.card_desc_font.render("карт в колоде", True, (160, 160, 160))
            hx = stack_rect.x + (CARD_W - hint_surf.get_width()) // 2
            screen.blit(hint_surf, (hx, stack_rect.y + CARD_H // 2 + 20))
        else:
            for i, card in enumerate(deck):
                cur_x = stack_x + int(i * card_step)
                CardRenderer.draw(
                    surface    = screen,
                    card       = card,
                    x          = cur_x,
                    y          = stack_y,
                    font_title = view.card_font,
                    font_desc  = view.card_desc_font,
                    is_hovered = False,
                )

        label = "Наведите для просмотра" if prog < 0.5 else "Стартовая колода"
        view.draw_text(label, view.card_desc_font,
                       (120, 120, 120), stack_x, stack_y + CARD_H + 10)

    @staticmethod
    def _draw_card_back(screen, rect, font):
        pygame.draw.rect(screen, (40, 40, 50), rect, border_radius=10)
        pygame.draw.rect(screen, (70, 100, 160), rect, 3, border_radius=10)
        inner = rect.inflate(-16, -16)
        pygame.draw.rect(screen, (55, 55, 70), inner, border_radius=6)
        pygame.draw.rect(screen, (70, 100, 160), inner, 1, border_radius=6)

    # ──────────────────────────────────────────
    #  КНОПКА СТАРТА
    # ──────────────────────────────────────────
    def _draw_start_button(self, view, screen, mouse_pos):
        btn = pygame.Rect(100, 720, 450, 80)
        view.btn_start_run = btn
        self.is_start_hovered = btn.collidepoint(mouse_pos)
        color = (70, 180, 70) if self.is_start_hovered else (40, 130, 40)
        pygame.draw.rect(screen, color, btn, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), btn, 3, border_radius=8)
        view.draw_text("ПОДНЯТЬСЯ В БАШНЮ [В БОЙ]",
                       view.card_font, (255, 255, 255), 155, 748)

    # ──────────────────────────────────────────
    #  HANDLE CLICK
    # ──────────────────────────────────────────
    def handle_click(self, view, mouse_pos):
        gm = view.gm

        for cls_name, rect in self.class_buttons.items():
            if rect.collidepoint(mouse_pos):
                self._select_class(gm, cls_name)
                return

        if hasattr(view, 'btn_start_run') and view.btn_start_run.collidepoint(mouse_pos):
            print(f" >>> СТАРТ ЗАБЕГА | Класс: {type(gm.player).__name__} <<<")
            self.reset()          # БАГ 3: сбрасываем анимацию перед стартом
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