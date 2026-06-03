import pygame
import re
from core.EffectCalculator import EffectCalculator
from core.cards.base import (
    StatusEffect, PoisonEffect,
    RegenEffect, HealEffect, VampireDamageEffect
)
from core.cards.debuff.bleed import BleedEffect
from core.StatusRegistry import STATUSES
_EXTRA_KEYWORDS = {
    "heal":    ("Лечение",    "Восстанавливает N HP."),
    "vampire": ("Вампиризм",  "Восстанавливает 50% нанесённого урона."),
    }


class CardRenderer:
    COLOR_COMBO    = (255, 215, 0)
    COLOR_DMG      = (46, 204, 113)
    COLOR_GRAY     = (200, 200, 200)
    COLOR_COST_LOW = (160, 40, 40)
    _DMG_MARKER    = "§"

    @staticmethod
    def get_card_colors(card):
        name = card.name.lower()
        if "огн" in name or "поджог" in name:
            return (45, 20, 20), (231, 76, 60)
        elif "всплеск" in name or "дожд" in name or "вод" in name:
            return (20, 35, 50), (52, 152, 219)
        elif "яд" in name or "токсин" in name or "кислот" in name:
            return (20, 45, 20), (46, 204, 113)
        elif "скруч" in name or "нейтрал" in name or "устраш" in name:
            return (40, 20, 45), (155, 89, 182)
        elif card.card_type == "attack":
            return (45, 45, 45), (240, 70, 70)
        else:
            return (40, 40, 40), (70, 160, 240)

    @staticmethod
    def _get_card_keywords(card) -> list[tuple[str, int]]:
        """
        Возвращает список (status_key, value) для статусных эффектов карты.
        value = реальное число с учётом апгрейда карты.
        Псевдо-ключи: 'heal', 'vampire' -- не статусы, но показываются в тултипе.
        """
        seen     = set()
        keywords = []
        for effect in card.effects:
            key = None
            val = 0
            if isinstance(effect, StatusEffect):
                key = effect.status_type
                val = effect.upgrade_turns if card.upgraded else effect.base_turns
            elif isinstance(effect, PoisonEffect):
                key = "poison"
                val = effect.upgrade_val if card.upgraded else effect.base_val
            elif isinstance(effect, RegenEffect):
                key = "regen"
                val = effect.upgrade_val if card.upgraded else effect.base_val
            elif isinstance(effect, BleedEffect):
                key = "bleed"
                val = effect.upgrade_val if card.upgraded else effect.base_val
            elif isinstance(effect, VampireDamageEffect):
                key = "vampire"
                val = 50
            elif isinstance(effect, HealEffect):
                key = "heal"
                val = effect.upgrade_val if card.upgraded else effect.base_val

            if key and key not in seen:
                if key in STATUSES or key in _EXTRA_KEYWORDS:
                    seen.add(key)
                    keywords.append((key, val))
        return keywords

    @staticmethod
    def draw_card_keyword_tooltip(screen, font_title, font_desc, card, card_rect):
        """
        Рисует окошко с расшифровкой ключевых слов карты.
        Появляется справа от карты (или слева если нет места).
        """
        keywords = CardRenderer._get_card_keywords(card)
        if not keywords:
            return

        pad_x, pad_y = 14, 10
        line_h_title = font_title.get_linesize()
        line_h_desc  = font_desc.get_linesize() + 1
        gap          = 6
        section_gap  = 4

        blocks = []
        max_w  = 0
        for key, val in keywords:
            if key in STATUSES:
                title_str, desc_str = STATUSES[key]["keyword"]
            else:
                title_str, desc_str = _EXTRA_KEYWORDS[key]
            desc_str   = desc_str.replace("N", str(val))
            title_surf = font_title.render(title_str, True, (255, 220, 80))
            desc_lines = [
                font_desc.render(l, True, (210, 210, 210))
                for l in desc_str.split("\n")
            ]
            block_w = max(
                title_surf.get_width(),
                max(s.get_width() for s in desc_lines)
            ) + pad_x * 2
            max_w = max(max_w, block_w)
            blocks.append((title_surf, desc_lines))

        box_w = max_w
        box_h = pad_y * 2
        for title_surf, desc_lines in blocks:
            box_h += line_h_title + section_gap
            box_h += len(desc_lines) * line_h_desc
            box_h += gap
        box_h -= gap

        screen_w, screen_h = screen.get_size()
        tip_x = card_rect.right + 12
        tip_y = card_rect.top
        if tip_x + box_w > screen_w - 10:
            tip_x = card_rect.left - box_w - 12
        if tip_y + box_h > screen_h - 10:
            tip_y = screen_h - box_h - 10

        bg_rect = pygame.Rect(tip_x, tip_y, box_w, box_h)
        pygame.draw.rect(screen, (18, 18, 24), bg_rect, border_radius=8)
        pygame.draw.rect(screen, (180, 160, 80), bg_rect, 1, border_radius=8)

        cursor_y = tip_y + pad_y
        for i, (title_surf, desc_lines) in enumerate(blocks):
            if i > 0:
                sep_y = cursor_y - gap // 2
                pygame.draw.line(
                    screen, (80, 80, 80),
                    (tip_x + pad_x, sep_y),
                    (tip_x + box_w - pad_x, sep_y), 1
                )
            screen.blit(title_surf, (tip_x + pad_x, cursor_y))
            cursor_y += line_h_title + section_gap
            for desc_surf in desc_lines:
                screen.blit(desc_surf, (tip_x + pad_x, cursor_y))
                cursor_y += line_h_desc
            cursor_y += gap

    @staticmethod
    def draw_centered_title(surface, text, font, card_rect, is_hovered):
        words = text.split(' ')
        lines = []
        current_line = ""
        max_width = card_rect.width - 20
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        line_height = font.get_linesize()
        start_y = card_rect.y + 20
        color = (241, 196, 15) if is_hovered else (255, 255, 255)
        for i, line in enumerate(lines):
            line_surf = font.render(line, True, color)
            x = card_rect.x + (card_rect.width // 2) - (line_surf.get_width() // 2)
            surface.blit(line_surf, (x, start_y + i * line_height))

    @staticmethod
    def _get_base_damage(description: str, is_upgraded: bool) -> int:
        if is_upgraded:
            match = re.search(r'\d+\s*\((\d+)\)', description)
        else:
            match = re.search(r'(\d+)', description)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _resolve_description(description: str, is_upgraded: bool,
                             player=None, enemy=None) -> tuple[str, bool]:
        is_combo = False
        if is_upgraded:
            cleaned = re.sub(r'\d+\s*\((\d+)\)', r'\1', description)
        else:
            cleaned = re.sub(r'(\d+)\s*\(\d+\)', r'\1', description)

        if player is None or enemy is None:
            return cleaned, is_combo

        is_combo   = getattr(enemy, 'wet', 0) > 0 and getattr(enemy, 'ignited', 0) > 0
        is_boosted = (
            getattr(player, 'strength', 0) > 0
            or getattr(enemy, 'vulnerable', 0) > 0
            or is_combo
        )

        if not is_boosted:
            return cleaned, is_combo

        base_dmg = CardRenderer._get_base_damage(description, is_upgraded)
        if base_dmg == 0:
            return cleaned, is_combo

        predicted = EffectCalculator.calculate_damage(
            attacker=player, target=enemy,
            base_damage=base_dmg, dry_run=True,
        )
        resolved = re.sub(
            r'\d+', CardRenderer._DMG_MARKER + str(predicted), cleaned, count=1
        )
        return resolved, is_combo

    @staticmethod
    def draw_smart_description(surface, description, font, card_rect,
                               is_upgraded, player=None, enemy=None):
        text, is_combo = CardRenderer._resolve_description(
            description, is_upgraded, player, enemy
        )
        color_digit = CardRenderer.COLOR_COMBO if is_combo else CardRenderer.COLOR_DMG
        font_big = pygame.font.SysFont("Arial", font.size("0")[1] + 4, bold=True)

        words = text.split(' ')
        lines = []
        current_line = []
        max_width = card_rect.width - 24

        for word in words:
            clean_word = word.replace(CardRenderer._DMG_MARKER, "")
            test_str = " ".join(
                [w.replace(CardRenderer._DMG_MARKER, "") for w, _ in current_line]
                + [clean_word]
            )
            if font.size(test_str)[0] <= max_width:
                current_line.append((word, word.startswith(CardRenderer._DMG_MARKER)))
            else:
                lines.append(current_line)
                current_line = [(word, word.startswith(CardRenderer._DMG_MARKER))]
        if current_line:
            lines.append(current_line)

        y_pos = card_rect.y + 110
        line_height = font.get_linesize() + 4

        for line in lines:
            x_pos = card_rect.x + 15
            for word, is_dmg_word in line:
                clean_word = word.replace(CardRenderer._DMG_MARKER, "")
                if is_dmg_word:
                    display  = f"*{clean_word}*"
                    word_surf = font_big.render(display + " ", True, color_digit)
                elif is_upgraded and clean_word.isdigit():
                    word_surf = font_big.render(clean_word + " ", True, CardRenderer.COLOR_DMG)
                else:
                    word_surf = font.render(clean_word + " ", True, CardRenderer.COLOR_GRAY)
                surface.blit(word_surf, (x_pos, y_pos))
                x_pos += word_surf.get_width()
            y_pos += line_height

    @staticmethod
    def _draw_unaffordable_overlay(surface, rect: pygame.Rect):
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (rect.x, rect.y))

    @staticmethod
    def draw(surface, card, x, y, font_title, font_desc,
             is_hovered=False, player=None, enemy=None):
        """Мастер-метод полной отрисовки карты 180×250."""
        width, height = 180, 250
        rect = pygame.Rect(x, y, width, height)

        can_afford = (
            player is None
            or not hasattr(player, 'energy')
            or card.cost <= player.energy
        )

        bg_color = (55, 55, 60) if is_hovered else (35, 35, 38)
        border_thickness = 5 if is_hovered else 3
        _, border_color = CardRenderer.get_card_colors(card)

        pygame.draw.rect(surface, bg_color, rect, border_radius=10)
        pygame.draw.rect(surface, border_color, rect, border_thickness, border_radius=10)

        cost_color = CardRenderer.COLOR_COST_LOW if not can_afford else border_color
        cost_surf  = font_title.render(str(card.cost), True, cost_color)
        surface.blit(cost_surf, (rect.x + 14, rect.y + 12))

        CardRenderer.draw_centered_title(surface, card.name, font_title, rect, is_hovered)

        if card.card_type == "attack" and player is not None and enemy is not None:
            CardRenderer.draw_smart_description(
                surface, card.description, font_desc, rect,
                card.upgraded, player=player, enemy=enemy
            )
        else:
            CardRenderer.draw_smart_description(
                surface, card.description, font_desc, rect,
                card.upgraded
            )

        if not can_afford:
            CardRenderer._draw_unaffordable_overlay(surface, rect)

        return rect