# ui/cards/description.py
# Отрисовка заголовка карты и «умного» описания с проекцией урона.
import colorsys
import pygame
import re
from core.EffectCalculator import EffectCalculator
from ui.cards.data import COLOR_DMG, COLOR_GRAY, DMG_MARKER


def _rainbow_color(phase: float):
    """RGB по фазе 0..1 (полный круг по цветовому тону). Для переливающегося
    названия легендарно-кованой карты (15+ уровень)."""
    r, g, b = colorsys.hsv_to_rgb(phase % 1.0, 0.75, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)


def draw_centered_title(surface, text, font, card_rect, is_hovered,
                        color=None, rainbow=False, phase=0.0):
    """Заголовок карты по центру (с переносом). color переопределяет базовый цвет
    (для индикации уровня ковки). rainbow=True → каждая буква переливается радугой
    (легендарная ковка); phase — сдвиг радуги во времени (анимация в реал-тайме).

    Возвращает Y нижней границы заголовка (для динамической раскладки описания)."""
    words = text.split(' ')
    lines = []
    current_line = ""
    # Сужаем доступную ширину названия: верхнюю зону занимают орб стоимости (слева)
    # и камень редкости (справа), поэтому первая строка не должна под них залезать.
    max_width = card_rect.width - 56
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
    # Название опущено НИЖЕ орба/камня (верхняя зона ~44px), чтобы не пересекаться.
    start_y = card_rect.y + 46

    if color is None:
        color = (241, 196, 15) if is_hovered else (255, 255, 255)

    for i, line in enumerate(lines):
        ly = start_y + i * line_height
        if rainbow:
            # Каждая буква — свой тон, плавно смещающийся по строке и по времени.
            total_w = font.size(line)[0]
            x = card_rect.x + (card_rect.width // 2) - (total_w // 2)
            for j, ch in enumerate(line):
                col = _rainbow_color(phase + (i * 8 + j) * 0.06)
                cs = font.render(ch, True, col)
                surface.blit(cs, (x, ly))
                x += cs.get_width()
        else:
            line_surf = font.render(line, True, color)
            x = card_rect.x + (card_rect.width // 2) - (line_surf.get_width() // 2)
            surface.blit(line_surf, (x, ly))

    return start_y + len(lines) * line_height


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


def _wrap_lines(text, font, max_width):
    """Перенос текста по словам под заданную ширину. Возвращает список строк,
    где строка = список (word, is_dmg_word). DMG_MARKER не учитывается в ширине."""
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        clean_word = word.replace(DMG_MARKER, "")
        test_str = " ".join(
            [w.replace(DMG_MARKER, "") for w, _ in current_line] + [clean_word])
        if font.size(test_str)[0] <= max_width or not current_line:
            current_line.append((word, word.startswith(DMG_MARKER)))
        else:
            lines.append(current_line)
            current_line = [(word, word.startswith(DMG_MARKER))]
    if current_line:
        lines.append(current_line)
    return lines


def draw_smart_description(surface, description, font, card_rect,
                           is_upgraded, player=None, enemy=None,
                           base_override=None, predicted=None,
                           top_y=None, bottom_y=None):
    """Описание карты с проекцией урона и ДИНАМИЧЕСКИМ шрифтом: кегль подбирается
    так, чтобы текст уместился в зону [top_y .. bottom_y] (между названием и
    строкой тегов/чипов). При большом числе пассивок зона ужимается — шрифт
    автоматически уменьшается, без вылезания за карту."""
    text = _resolve_description(
        description, is_upgraded, player, enemy, base_override, predicted)

    # Границы зоны описания (дефолты — как раньше, если вызывающий не задал).
    if top_y is None:
        top_y = card_rect.y + 96
    if bottom_y is None:
        bottom_y = card_rect.bottom - 28
    avail_h = max(20, bottom_y - top_y)
    max_width = card_rect.width - 24

    # Подбор кегля: от базового вниз до минимума, пока текст влезает по высоте.
    base_size = font.size("0")[1]
    chosen_font = font
    chosen_lines = None
    for size in range(base_size, 9, -1):
        f = pygame.font.SysFont("Arial", size)
        lines = _wrap_lines(text, f, max_width)
        line_h = f.get_linesize() + 2
        if len(lines) * line_h <= avail_h:
            chosen_font, chosen_lines = f, lines
            break
    if chosen_lines is None:
        # Даже минимальный кегль не влез — берём минимальный и обрезаем по высоте.
        chosen_font = pygame.font.SysFont("Arial", 10)
        chosen_lines = _wrap_lines(text, chosen_font, max_width)

    line_height = chosen_font.get_linesize() + 2
    font_big = pygame.font.SysFont(
        "Arial", chosen_font.size("0")[1] + 3, bold=True)

    max_lines = max(1, avail_h // line_height)
    y_pos = top_y
    for line in chosen_lines[:max_lines]:
        x_pos = card_rect.x + 15
        for word, is_dmg_word in line:
            clean_word = word.replace(DMG_MARKER, "")
            if is_dmg_word:
                word_surf = font_big.render(f"*{clean_word}* ", True, COLOR_DMG)
            elif is_upgraded and clean_word.isdigit():
                word_surf = font_big.render(clean_word + " ", True, COLOR_DMG)
            else:
                word_surf = chosen_font.render(clean_word + " ", True, COLOR_GRAY)
            surface.blit(word_surf, (x_pos, y_pos))
            x_pos += word_surf.get_width()
        y_pos += line_height
