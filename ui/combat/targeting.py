# ui/combat/targeting.py
# Клик-таргетинг врагов: выбор цели для карт и способностей.
# Вместо авто-таргетинга (первый живой) игрок может кликнуть по вражеской панели.
import pygame
from ui.combat.layout import _GOLD


class TargetingSystem:
    """Хранит выбранную цель и отрисовывает индикатор."""

    @staticmethod
    def get_current_target(combat):
        """Выбранная цель или первый живой враг (авто-таргетинг)."""
        enemies = combat.enemies
        # Ищем выбранную цель (хранится в combat или view)
        target_idx = getattr(combat, '_target_index', 0)
        if 0 <= target_idx < len(enemies) and enemies[target_idx].hp > 0:
            return enemies[target_idx]
        # Фоллбэк: первый живой
        for e in enemies:
            if e.hp > 0:
                return e
        return None

    @staticmethod
    def handle_target_click(view, mouse_pos):
        """Проверка клика по вражеским панелям. Возвращает True если цель изменилась."""
        rects = getattr(view, 'enemy_panel_rects', [])
        combat = view.gm.active_combat
        for i, rect in enumerate(rects):
            if rect.collidepoint(mouse_pos):
                if combat.enemies[i].hp > 0:
                    combat._target_index = i
                    return True
        return False

    @staticmethod
    def draw_target_indicator(screen, rect):
        """Светящаяся рамка вокруг выбранной цели."""
        if rect is None:
            return
        # Жёлтая рамка-подсветка
        glow = pygame.Rect(rect.x - 3, rect.y - 3, rect.w + 6, rect.h + 6)
        pygame.draw.rect(screen, _GOLD, glow, 3, border_radius=14)
