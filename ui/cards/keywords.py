# ui/cards/keywords.py
# Сбор ключевых слов карты и отрисовка модульного тултипа-глоссария.
import pygame
from core.cards.base import (
    StatusEffect, RegenEffect, HealEffect, DetonateEffect,
    BarrierEffect,
)
from core.cards.debuff.bleed import BleedEffect
from core.cards.buff.vampirism import VampireBuffEffect
from core.cards.air import FlowEffect, SpreadEffect
from core.cards.echo import EchoEffect
from core.cards.mage import MasteryEffect
from core.StatusRegistry import STATUSES
from ui.cards.data import _EXTRA_KEYWORDS, effect_icon_color
from ui.status_icons import draw_status_icon


def get_card_keywords(card) -> list[tuple[str, int]]:
    seen     = set()
    keywords = []
    for effect in card.effects:
        key = None
        val = 0
        if isinstance(effect, StatusEffect):
            key = effect.status_type
            val = effect.upgrade_turns if card.upgraded else effect.base_turns
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
        elif isinstance(effect, DetonateEffect):
            key = "detonate"
            val = 0
        elif isinstance(effect, SpreadEffect):
            key = "spread"
            val = 0
        elif isinstance(effect, EchoEffect):
            key = "echo"
            val = effect.upgrade_val if card.upgraded else effect.base_val
        elif isinstance(effect, BarrierEffect):
            key = "barrier"
            val = effect.upgrade_val if card.upgraded else effect.base_val
        elif isinstance(effect, MasteryEffect):
            key = "mastery"
            val = effect.upgrade_val if card.upgraded else effect.base_val

        if key and key not in seen:
            if key in STATUSES or key in _EXTRA_KEYWORDS:
                seen.add(key)
                keywords.append((key, val))
    return keywords


def get_forge_passives(card, player) -> list[tuple[str, str]]:
    """Пассивки ковки карты как (label, tier) — для блока тултипа. Пусто, если
    карта не кована / нет игрока. label — человекочитаемое имя тега из TAGS."""
    if player is None:
        return []
    from core.ForgeRegistry import resolve_forge_record, TAGS
    rec = resolve_forge_record(card, player)
    if not rec:
        return []
    out = []
    for slot in rec.get("slots") or []:
        spec = TAGS.get(slot.get("tag_id"))
        if spec:
            out.append((spec.get("label", slot.get("tag_id")),
                        spec.get("tier", "early")))
    return out


def draw_card_keyword_tooltip(screen, font_title, font_desc, card, card_rect,
                              damage_steps=None, player=None):
    """Модульный тултип карты (стиль Hearthstone): блоки «Расчёт урона» / эффекты
    (с иконкой) / пассивки ковки. Каждый блок — иконка + заголовок + описание,
    разделённые линиями. Клампится в пределах экрана (вниз и вбок)."""
    keywords = get_card_keywords(card)
    passives = get_forge_passives(card, player)
    if not keywords and not damage_steps and not passives:
        return

    pad_x, pad_y = 14, 10
    icon_r = 9                      # радиус иконки слева от заголовка блока
    icon_slot = icon_r * 2 + 8      # ширина колонки под иконку
    line_h_title = font_title.get_linesize()
    line_h_desc  = font_desc.get_linesize() + 1
    gap          = 6
    section_gap  = 4

    # blocks: (icon_key|None, title_surf, [desc_surf...])
    blocks = []
    max_w  = 0

    # Блок «Расчёт урона» (аудит механик): база→модификаторы→итог. Без иконки.
    if damage_steps:
        title_surf = font_title.render("Расчёт урона", True, (255, 220, 80))
        desc_lines = []
        for label, kind, val in damage_steps:
            txt = f"{label}: ×{val:g}" if kind == "×" else f"{label}: +{val}"
            desc_lines.append(font_desc.render(txt, True, (210, 210, 210)))
        block_w = max([title_surf.get_width()]
                      + [s.get_width() for s in desc_lines]) + pad_x * 2 + icon_slot
        max_w = max(max_w, block_w)
        blocks.append((None, title_surf, desc_lines))

    # Блоки эффектов: иконка + название + описание (из STATUSES/_EXTRA_KEYWORDS).
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
        ) + pad_x * 2 + icon_slot
        max_w = max(max_w, block_w)
        blocks.append((key, title_surf, desc_lines))

    # Блок пассивок ковки: по строке на тег (золото=легендарная, серебро=ранняя).
    if passives:
        head = font_title.render("Ковка", True, (255, 220, 80))
        desc_lines = []
        for label, tier in passives:
            col = (245, 210, 90) if tier == "legendary" else (200, 200, 210)
            # Узкий «×» в начале лейбла сливается со словом — отделяем пробелом.
            if label[:1] in ("×", "x", "х"):
                label = label[:1] + " " + label[1:].lstrip()
            desc_lines.append(font_desc.render("• " + label, True, col))
        block_w = max([head.get_width()]
                      + [s.get_width() for s in desc_lines]) + pad_x * 2 + icon_slot
        max_w = max(max_w, block_w)
        blocks.append(("_forge", head, desc_lines))

    box_w = max_w
    box_h = pad_y * 2
    for _icon, title_surf, desc_lines in blocks:
        box_h += line_h_title + section_gap
        box_h += len(desc_lines) * line_h_desc
        box_h += gap
    box_h -= gap

    screen_w, screen_h = screen.get_size()
    tip_x = card_rect.right + 12
    tip_y = card_rect.top
    if tip_x + box_w > screen_w - 10:
        tip_x = card_rect.left - box_w - 12
    if tip_x < 10:
        tip_x = 10
    if tip_y + box_h > screen_h - 10:
        tip_y = screen_h - box_h - 10
    if tip_y < 10:
        tip_y = 10

    bg_rect = pygame.Rect(tip_x, tip_y, box_w, box_h)
    pygame.draw.rect(screen, (18, 18, 24), bg_rect, border_radius=8)
    pygame.draw.rect(screen, (180, 160, 80), bg_rect, 1, border_radius=8)

    cursor_y = tip_y + pad_y
    for i, (icon_key, title_surf, desc_lines) in enumerate(blocks):
        if i > 0:
            sep_y = cursor_y - gap // 2
            pygame.draw.line(
                screen, (80, 80, 80),
                (tip_x + pad_x, sep_y),
                (tip_x + box_w - pad_x, sep_y), 1
            )
        # Иконка слева от заголовка (если у блока есть символ).
        title_x = tip_x + pad_x
        if icon_key and icon_key != "_forge":
            draw_status_icon(screen, icon_key,
                             tip_x + pad_x + icon_r, cursor_y + line_h_title // 2,
                             icon_r, effect_icon_color(icon_key))
            title_x += icon_slot
        elif icon_key == "_forge":
            # Маленькая «звезда ковки» (мастерство-иконка как символ прокачки).
            draw_status_icon(screen, "mastery",
                             tip_x + pad_x + icon_r, cursor_y + line_h_title // 2,
                             icon_r, (245, 210, 90))
            title_x += icon_slot
        screen.blit(title_surf, (title_x, cursor_y))
        cursor_y += line_h_title + section_gap
        for desc_surf in desc_lines:
            screen.blit(desc_surf, (title_x, cursor_y))
            cursor_y += line_h_desc
        cursor_y += gap
