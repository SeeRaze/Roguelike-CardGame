import pygame
import re
from core.EffectCalculator import EffectCalculator
from core.cards.base import (
    StatusEffect, PoisonEffect,
    RegenEffect, HealEffect, VampireDamageEffect,
    DamageEffect, ShieldEffect
)
from core.cards.debuff.bleed import BleedEffect
from core.cards.buff.strength import BuffEffect
from core.StatusRegistry import STATUSES
from core.cards.buff.vampirism import VampireBuffEffect

# Псевдо-ключи для тултипов (не статусы Creature)
_EXTRA_KEYWORDS = {
    "heal":    ("Лечение",    "Восстанавливает N HP."),
    "vampire": ("Вампиризм",  "Восстанавливает 50% нанесённого урона."),
}

# ─── Палитра карт ────────────────────────────────────────────────────────────
_C = {
    "attack_pure":  ((50, 20, 20),  (220, 60,  60)),
    "bleed":        ((45, 10, 15),  (160, 30,  55)),
    "poison":       ((15, 40, 15),  (50,  180, 80)),
    "fire":         ((50, 30, 10),  (230, 140, 30)),
    "water":        ((15, 30, 55),  (52,  152, 219)),
    "vampire":      ((40, 15, 40),  (180, 60,  200)),
    "heal":         ((15, 45, 25),  (80,  220, 120)),
    "regen":        ((10, 40, 35),  (30,  180, 140)),
    "shield":       ((15, 25, 50),  (70,  130, 220)),
    "buff":         ((45, 35, 10),  (210, 170, 40)),
    "debuff":       ((35, 15, 45),  (155, 89,  182)),
    "attack_mixed": ((45, 20, 20),  (200, 80,  80)),
    "default":      ((30, 30, 38),  (90,  120, 180)),
}


def _classify_card(card):
    """Определяет класс карты по составу эффектов. Возвращает ключ из _C."""
    effects = card.effects
    has_damage   = any(isinstance(e, (DamageEffect, VampireDamageEffect)) for e in effects)
    has_vampire  = any(isinstance(e, VampireBuffEffect) for e in effects)
    has_bleed    = any(isinstance(e, BleedEffect) for e in effects)
    has_poison   = any(isinstance(e, PoisonEffect) for e in effects)
    has_shield   = any(isinstance(e, ShieldEffect) for e in effects)
    has_heal     = any(isinstance(e, HealEffect) for e in effects)
    has_regen    = any(isinstance(e, RegenEffect) for e in effects)
    has_buff     = any(isinstance(e, BuffEffect) for e in effects)

    has_ignited  = any(isinstance(e, StatusEffect) and e.status_type == "ignited" for e in effects)
    has_wet      = any(isinstance(e, StatusEffect) and e.status_type == "wet"     for e in effects)
    has_debuff   = any(
        isinstance(e, StatusEffect) and e.status_type in ("vulnerable", "weak")
        for e in effects
    )

    if has_vampire:   return "vampire"
    if has_bleed:     return "bleed"
    if has_poison:    return "poison"
    if has_ignited:   return "fire"
    if has_wet:       return "water"
    if has_regen:     return "regen"
    if has_heal:      return "heal"
    if has_buff:      return "buff"
    if has_debuff:    return "debuff"
    if has_shield and not has_damage: return "shield"
    if has_damage and not has_shield and not has_debuff: return "attack_pure"
    if has_damage:    return "attack_mixed"
    if has_shield:    return "shield"
    return "default"


class CardRenderer:
    COLOR_COMBO    = (255, 215, 0)
    COLOR_DMG      = (46,  204, 113)
    COLOR_GRAY     = (200, 200, 200)
    COLOR_COST_LOW = (160, 40,  40)
    COLOR_COST_DISC = (80, 220, 80)   # зелёный -- скидка Разбойника
    _DMG_MARKER    = "§"

    @staticmethod
    def get_card_colors(card):
        """Возвращает (bg_color, border_color) по типу эффектов карты."""
        key = _classify_card(card)
        return _C[key]

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
            cost_color = CardRenderer.COLOR_COST_DISC
        elif not can_afford:
            cost_color = CardRenderer.COLOR_COST_LOW
        else:
            cost_color = border_color

        cost_surf = font_title.render(str(display_cost), True, cost_color)
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
                    display   = f"*{clean_word}*"
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
    def _get_card_keywords(card) -> list[tuple[str, int]]:
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
            elif isinstance(effect, VampireBuffEffect):
                key = "vampire"
                val = effect.upgrade_val if card.upgraded else effect.base_val
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