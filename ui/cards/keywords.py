# ui/cards/keywords.py
# Сбор ключевых слов карты и отрисовка тултипа-глоссария.
import pygame
from core.cards.base import StatusEffect, PoisonEffect, RegenEffect, HealEffect
from core.cards.debuff.bleed import BleedEffect
from core.cards.buff.vampirism import VampireBuffEffect
from core.cards.air import FlowEffect
from core.StatusRegistry import STATUSES
from ui.cards.data import _EXTRA_KEYWORDS


def get_card_keywords(card) -> list[tuple[str, int]]:
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
        elif isinstance(effect, FlowEffect):
            key = "flow"
            val = effect.upgrade_val if card.upgraded else effect.base_val

        if key and key not in seen:
            if key in STATUSES or key in _EXTRA_KEYWORDS:
                seen.add(key)
                keywords.append((key, val))
    return keywords


def draw_card_keyword_tooltip(screen, font_title, font_desc, card, card_rect):
    keywords = get_card_keywords(card)
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
            font_desc.render(line, True, (210, 210, 210))
            for line in desc_str.split("\n")
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
