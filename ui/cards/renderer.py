# ui/cards/renderer.py
# Публичный фасад отрисовки карты: оркестрирует classifier/description/keywords.
import pygame
from ui.cards.classifier import classify_card
from ui.cards.data import _C, COLOR_COST_LOW, COLOR_COST_DISC
from ui.cards import description, keywords


class CardRenderer:
    @staticmethod
    def get_card_colors(card):
        """Возвращает (bg_color, border_color) по типу эффектов карты."""
        return _C[classify_card(card)]

    @staticmethod
    def draw(surface, card, x, y, font_title, font_desc,
             is_hovered=False, player=None, enemy=None):
        """Мастер-метод полной отрисовки карты 180×250."""
        width, height = 180, 250
        rect = pygame.Rect(x, y, width, height)

        # temp_cost: механика Разбойника (-1 к стоимости случайной карты)
        display_cost = getattr(card, 'temp_cost', card.cost)
        is_discounted = display_cost < card.cost

        can_afford = (
            player is None
            or not hasattr(player, 'energy')
            or display_cost <= player.energy
        )

        bg_color, border_color = CardRenderer.get_card_colors(card)

        if is_hovered:
            bg_color = tuple(min(255, c + 20) for c in bg_color)

        border_thickness = 5 if is_hovered else 3

        pygame.draw.rect(surface, bg_color, rect, border_radius=10)
        pygame.draw.rect(surface, border_color, rect, border_thickness, border_radius=10)

        if is_discounted:
            cost_color = COLOR_COST_DISC
        elif not can_afford:
            cost_color = COLOR_COST_LOW
        else:
            cost_color = border_color

        cost_surf = font_title.render(str(display_cost), True, cost_color)
        surface.blit(cost_surf, (rect.x + 14, rect.y + 12))

        description.draw_centered_title(surface, card.name, font_title, rect, is_hovered)

        if card.card_type == "attack" and player is not None and enemy is not None:
            description.draw_smart_description(
                surface, card.description, font_desc, rect,
                card.upgraded, player=player, enemy=enemy
            )
        else:
            description.draw_smart_description(
                surface, card.description, font_desc, rect,
                card.upgraded
            )

        CardRenderer._draw_forge_marks(surface, card, player, rect, font_desc)

        if not can_afford:
            CardRenderer._draw_unaffordable_overlay(surface, rect)

        return rect

    @staticmethod
    def _draw_forge_marks(surface, card, player, rect, font):
        """Метки прокачки карты (39.5): бейдж уровня (сверху-справа) + точки-теги
        снизу-слева. Золотая точка — легендарный ×mult (истинный компаунд),
        серебряная — ранний +mult; число рядом = grade Гипер-заряда. Полные
        условия тегов — в будущей итерации тултипа/иконок (HUD-читаемость)."""
        if player is None:
            return
        from core.ForgeRegistry import resolve_forge_record, TAGS
        rec = resolve_forge_record(card, player)
        if not rec:
            return

        level = rec.get("level", 0)
        if level > 0:
            badge = font.render(f"Ур.{level}", True, (120, 220, 120))
            bx = rect.right - badge.get_width() - 12
            bg = pygame.Surface((badge.get_width() + 8, badge.get_height() + 4),
                                pygame.SRCALPHA)
            bg.fill((0, 0, 0, 150))
            surface.blit(bg, (bx - 4, rect.y + 8))
            surface.blit(badge, (bx, rect.y + 10))

        dot_x = rect.x + 12
        dot_y = rect.bottom - 20
        for slot in rec.get("slots") or []:
            spec = TAGS.get(slot.get("tag_id"), {})
            col = (235, 200, 80) if spec.get("kind") == "mult" else (200, 200, 210)
            pygame.draw.circle(surface, col, (dot_x + 5, dot_y + 5), 6)
            pygame.draw.circle(surface, (0, 0, 0), (dot_x + 5, dot_y + 5), 6, 1)
            grade = slot.get("grade", 0)
            if grade:
                g = font.render(str(grade), True, (255, 240, 180))
                surface.blit(g, (dot_x + 12, dot_y - 2))
                dot_x += g.get_width() + 4
            dot_x += 18

    @staticmethod
    def draw_card_keyword_tooltip(screen, font_title, font_desc, card, card_rect):
        keywords.draw_card_keyword_tooltip(screen, font_title, font_desc, card, card_rect)

    @staticmethod
    def _draw_unaffordable_overlay(surface, rect: pygame.Rect):
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (rect.x, rect.y))
