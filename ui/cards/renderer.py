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

        if not can_afford:
            CardRenderer._draw_unaffordable_overlay(surface, rect)

        return rect

    @staticmethod
    def draw_card_keyword_tooltip(screen, font_title, font_desc, card, card_rect):
        keywords.draw_card_keyword_tooltip(screen, font_title, font_desc, card, card_rect)

    @staticmethod
    def _draw_unaffordable_overlay(surface, rect: pygame.Rect):
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (rect.x, rect.y))
