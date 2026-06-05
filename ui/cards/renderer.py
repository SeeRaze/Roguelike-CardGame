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
             is_hovered=False, player=None, enemy=None, combat_manager=None):
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

        preview = None
        if card.card_type == "attack" and player is not None and enemy is not None:
            # База урона для превью — из ЭФФЕКТА (учитывает уровень ковки +δ), а не
            # из строки описания (которая ковкой не обновляется).
            base = CardRenderer._card_base_damage(card)
            predicted = None
            if base and combat_manager is not None:
                # Единый расчёт: ГАРАНТИРОВАННОЕ число (баффы/дебаффы/Заточка/уровень)
                # для строки + чипы условных реакций (комбо/ковка). Превью == удар.
                from core.EffectCalculator import EffectCalculator
                preview = EffectCalculator.preview(
                    player, enemy, base, combat_manager=combat_manager,
                    game_manager=getattr(combat_manager, "gm", None), card=card)
                predicted = preview["guaranteed"]
            description.draw_smart_description(
                surface, card.description, font_desc, rect,
                card.upgraded, player=player, enemy=enemy,
                base_override=base, predicted=predicted,
            )
        else:
            description.draw_smart_description(
                surface, card.description, font_desc, rect,
                card.upgraded
            )

        CardRenderer._draw_forge_marks(surface, card, player, rect, font_desc)
        if preview is not None:
            CardRenderer._draw_reaction_chips(surface, rect, preview, font_desc)

        if not can_afford:
            CardRenderer._draw_unaffordable_overlay(surface, rect)

        return rect

    @staticmethod
    def _card_base_damage(card):
        """Текущее значение урона карты из ЭФФЕКТА (а не из строки описания):
        upgrade_val если карта улучшена/прокачана, иначе base_val. Учитывает
        линейный слой ковки (+δ бампит base_val/upgrade_val). None, если карта без
        урона. Используется для корректного превью числа на карте (39.5 хотфикс)."""
        from core.cards.base import DamageEffect
        for e in card.effects:
            if isinstance(e, DamageEffect):
                return e.upgrade_val if card.upgraded else e.base_val
        return None

    # Цвета чипов реакций (минимал-стиль, решение юзера: смысл из цвета + ховера).
    _CHIP_COMBO = (70, 130, 180)    # стихийное комбо (ПАР и т.п.) — стально-синий
    _CHIP_FORGE = (200, 120, 40)    # forge-теги — оранжевый

    @staticmethod
    def _draw_reaction_chips(surface, rect, preview, font):
        """Схематичные чипы условных реакций, что СРАБОТАЮТ против текущей цели:
        только цвет + ×множитель (синий=комбо, оранж=ковка). Полные названия и
        разбор — в ховер-тултипе. Низ карты, выровнены вправо (растут влево),
        чтобы не пересекаться с точками-тегами (низ-слева)."""
        chips = []
        for r in preview.get("reactions", []):
            chips.append((f"×{r['mult']:g}", CardRenderer._CHIP_COMBO))
        fm = preview.get("forge_mult", 1.0)
        if fm and fm != 1.0:
            chips.append((f"×{fm:g}", CardRenderer._CHIP_FORGE))
        if not chips:
            return

        x = rect.right - 8
        for text, color in reversed(chips):
            ts = font.render(text, True, (255, 255, 255))
            w, h = ts.get_width() + 12, ts.get_height() + 4
            chip = pygame.Rect(x - w, rect.bottom - h - 6, w, h)
            pygame.draw.rect(surface, color, chip, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255), chip, 1, border_radius=6)
            surface.blit(ts, (chip.x + 6, chip.y + 2))
            x -= w + 4

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
    def draw_card_keyword_tooltip(screen, font_title, font_desc, card, card_rect,
                                  damage_steps=None):
        keywords.draw_card_keyword_tooltip(
            screen, font_title, font_desc, card, card_rect, damage_steps)

    @staticmethod
    def _draw_unaffordable_overlay(surface, rect: pygame.Rect):
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (rect.x, rect.y))
