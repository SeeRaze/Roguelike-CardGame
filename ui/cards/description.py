# ui/cards/description.py
# Отрисовка заголовка карты и «умного» описания с проекцией урона.
import pygame
import re
from core.EffectCalculator import EffectCalculator
from ui.cards.data import COLOR_DMG, COLOR_GRAY, DMG_MARKER


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


def _get_base_damage(description: str, is_upgraded: bool) -> int:
    if is_upgraded:
        match = re.search(r'\d+\s*\((\d+)\)', description)
    else:
        match = re.search(r'(\d+)', description)
    return int(match.group(1)) if match else 0


def _resolve_description(description: str, is_upgraded: bool,
                         player=None, enemy=None,
                         base_override=None, predicted=None) -> str:
    if is_upgraded:
        cleaned = re.sub(r'\d+\s*\((\d+)\)', r'\1', description)
    else:
        cleaned = re.sub(r'(\d+)\s*\(\d+\)', r'\1', description)

    if player is None or enemy is None:
        return cleaned

    # База урона = ЗНАЧЕНИЕ ЭФФЕКТА карты (base_override), а не число из строки:
    # ковка (+δ) бампит эффект, но НЕ строку описания. printed_base — что напечатано
    # в строке (для решения, надо ли подсветить изменённое число).
    printed_base = _get_base_damage(description, is_upgraded)
    base_dmg = base_override if base_override is not None else printed_base
    if base_dmg == 0:
        return cleaned

    # Показанное число = ГАРАНТИРОВАННОЕ (predicted считает renderer через
    # EffectCalculator.preview: баффы игрока + дебаффы врага + Заточка + уровень,
    # БЕЗ условных комбо/forge — те идут чипами). Fallback (контексты без боя) —
    # локальный детерминир. расчёт. Превью == фактический удар (единый источник).
    if predicted is None:
        predicted = EffectCalculator.calculate_damage(
            attacker=player, target=enemy, base_damage=base_dmg, dry_run=True,
        )

    # Подсвечиваем число, только если оно отличается от напечатанного (есть модификатор
    # ИЛИ уровень ковки) — иначе показываем строку как есть.
    if predicted != printed_base:
        return re.sub(r'\d+', DMG_MARKER + str(predicted), cleaned, count=1)
    return cleaned


def draw_smart_description(surface, description, font, card_rect,
                           is_upgraded, player=None, enemy=None,
                           base_override=None, predicted=None):
    text = _resolve_description(
        description, is_upgraded, player, enemy, base_override, predicted)
    color_digit = COLOR_DMG
    font_big = pygame.font.SysFont("Arial", font.size("0")[1] + 4, bold=True)

    words = text.split(' ')
    lines = []
    current_line = []
    max_width = card_rect.width - 24

    for word in words:
        clean_word = word.replace(DMG_MARKER, "")
        test_str = " ".join(
            [w.replace(DMG_MARKER, "") for w, _ in current_line]
            + [clean_word]
        )
        if font.size(test_str)[0] <= max_width:
            current_line.append((word, word.startswith(DMG_MARKER)))
        else:
            lines.append(current_line)
            current_line = [(word, word.startswith(DMG_MARKER))]
    if current_line:
        lines.append(current_line)

    y_pos = card_rect.y + 110
    line_height = font.get_linesize() + 4

    for line in lines:
        x_pos = card_rect.x + 15
        for word, is_dmg_word in line:
            clean_word = word.replace(DMG_MARKER, "")
            if is_dmg_word:
                display   = f"*{clean_word}*"
                word_surf = font_big.render(display + " ", True, color_digit)
            elif is_upgraded and clean_word.isdigit():
                word_surf = font_big.render(clean_word + " ", True, COLOR_DMG)
            else:
                word_surf = font.render(clean_word + " ", True, COLOR_GRAY)
            surface.blit(word_surf, (x_pos, y_pos))
            x_pos += word_surf.get_width()
        y_pos += line_height
