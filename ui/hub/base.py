# ui/hub/base.py
# Оркестратор Мета-Хаба: состояние анимации, отрисовка, обработка кликов.
import pygame
from ui.hub.data import (
    ANIM_SPEED, SCREEN_W, SCREEN_H,
    _BG_COLOR, _TITLE_COLOR, _GOLD_COLOR, _BTN_BORDER, _START_COLOR, _START_HOVER,
)
from ui.hub.selectors import draw_class_selector
from ui.hub.deck import draw_deck_section


class HubView:
    """Отрисовка и логика Мета-Хаба: выбор класса + анимированная стопка карт."""

    def __init__(self):
        self.hover_progress:   float = 0.0
        self.is_deck_hovered:  bool  = False
        self.class_buttons:    dict  = {}
        self.is_start_hovered: bool  = False

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

    # --- ОТРИСОВКА ---

    def draw(self, view):
        screen    = view.screen
        gm        = view.gm
        mouse_pos = pygame.mouse.get_pos()

        screen.fill(_BG_COLOR)

        font_title = pygame.font.SysFont("Arial", 42, bold=True)
        font_gold  = pygame.font.SysFont("Arial", 26, bold=True)
        font_hint  = pygame.font.SysFont("Arial", 22)

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

        self.class_buttons   = draw_class_selector(screen, gm, mouse_pos)
        self.is_deck_hovered = draw_deck_section(
            view, screen, gm, mouse_pos, font_hint, self.hover_progress
        )
        self._draw_start_button(view, screen, mouse_pos)

    def _draw_start_button(self, view, screen, mouse_pos):
        btn_w, btn_h = 520, 72
        bx = SCREEN_W // 2 - btn_w // 2
        by = SCREEN_H - 120
        btn = pygame.Rect(bx, by, btn_w, btn_h)
        view.btn_start_run    = btn
        self.is_start_hovered = btn.collidepoint(mouse_pos)

        color = _START_HOVER if self.is_start_hovered else _START_COLOR
        pygame.draw.rect(screen, color,           btn, border_radius=12)
        pygame.draw.rect(screen, (100, 220, 100), btn, 2, border_radius=12)

        font_btn = pygame.font.SysFont("Arial", 26, bold=True)
        lbl = font_btn.render("ПОДНЯТЬСЯ В БАШНЮ  [В БОЙ]", True, (255, 255, 255))
        screen.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                          btn.centery - lbl.get_height() // 2))

    # --- КЛИКИ ---

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
        from core.players import Warrior, Rogue, Mage, Druid, Berserker, Summoner
        CLASS_MAP = {
            "Warrior":   Warrior,
            "Rogue":     Rogue,
            "Mage":      Mage,
            "Druid":     Druid,
            "Berserker": Berserker,
            "Summoner":  Summoner,
        }
        if cls_name not in CLASS_MAP:
            return
        if type(gm.player).__name__ == cls_name:
            return
        gm.player       = CLASS_MAP[cls_name]()
        gm.current_deck = gm.player.get_starter_deck()
        # Паспорт ковки: новый игрок/колода создаются МИНУЯ GameManager.__init__,
        # поэтому штампуем uid здесь — иначе ковка на костре молча не сработает
        # (forge_card_one_level подстрахован ленивой штамповкой, но держим uid
        # стабильными сразу, как при старте). 39.5 хотфикс.
        from core.forge import assign_forge_uid
        for card in gm.current_deck:
            assign_forge_uid(gm.player, card)
        print(f"[HubView] Выбран класс: {cls_name}")
