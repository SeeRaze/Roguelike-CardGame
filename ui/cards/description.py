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


# Урон-число карты пишется ПАРОЙ N(M) (base/upgrade). Несущественные числа —
# счётчик ударов «3 удара», проценты «130%» — без скобок, их НЕ трогаем.
_DMG_PAIR_RE = re.compile(r'(\d+)\s*\((\d+)\)')

# Свёртка ЛЮБОЙ пары base(upgrade) в одно число, включая процентные «30%(40%)» —
# у классовых карт множители/цена пишутся в процентах, и «значение после улучшения»
# в скобках игроку не нужно (приводим к общему виду, как у обычных карт).
_ANY_PAIR_RE = re.compile(r'(\d+%?)\s*\((\d+%?)\)')


def _get_base_damage(description: str, is_upgraded: bool) -> int:
    """Напечатанное урон-число = ПЕРВАЯ пара N(M): база (или верхнее при улучшении).
    Якорь на пару, а не на первое число, спасает мульти-хит карты («3 удара по
    2(3)»), где первое число — счётчик ударов, а не урон. Fallback на первое
    число, если пар в строке нет."""
    pair = _DMG_PAIR_RE.search(description)
    if pair:
        return int(pair.group(2) if is_upgraded else pair.group(1))
    match = re.search(r'\d+', description)
    return int(match.group()) if match else 0


def _resolve_pairs(s: str, is_upgraded: bool) -> str:
    """Свернуть все пары base(upgrade) в одно число: верхнее при улучшении, базовое
    иначе. Ловит и процентные пары «30%(40%)» (классовые множители/цена), чтобы
    «(значение после улучшения)» не торчало в скобках."""
    return _ANY_PAIR_RE.sub(r'\2' if is_upgraded else r'\1', s)


# Пары «N (M)» в описании = base/upgrade одного эффекта. Ковка (+δ) бампит эффекты,
# но НЕ строку описания — поэтому без проекции форжёная карта в костре/магазине
# показывает устаревшее число (см. core.forge.apply_linear_level).
_PAIR_RE = re.compile(r'(\d+)(\s*)\((\d+)\)')


def _effect_display_pairs(card):
    """Текущие отображаемые пары (base, upgrade) эффектов карты В ПОРЯДКЕ: значения
    (DamageEffect/ShieldEffect/…) или длительности (StatusEffect). Ровно те числа,
    что печатаются в описании пары N(M)."""
    pairs = []
    for e in getattr(card, "effects", None) or []:
        if hasattr(e, "base_val") and hasattr(e, "upgrade_val"):
            pairs.append((e.base_val, e.upgrade_val))
        elif hasattr(e, "base_turns") and hasattr(e, "upgrade_turns"):
            pairs.append((e.base_turns, e.upgrade_turns))
    return pairs


def project_forge_values(card) -> str:
    """Описание карты с пересчётом пар N(M) из ТЕКУЩИХ значений эффектов (ковка их
    бампит, строку — нет). Позиционно: i-я пара ↔ i-й отображаемый эффект, исходный
    пробел сохраняется. СТРАХОВКА: если число пар в строке ≠ числу эффектов —
    строка возвращается БЕЗ изменений (нестандартные описания: мульти-хиты,
    призывы, «половину» — их не корёжим)."""
    desc = getattr(card, "description", "") or ""
    matches = list(_PAIR_RE.finditer(desc))
    eff_pairs = _effect_display_pairs(card)
    if not matches or len(matches) != len(eff_pairs):
        return desc
    out, last = [], 0
    for m, (bv, uv) in zip(matches, eff_pairs):
        out.append(desc[last:m.start()])
        out.append(f"{bv}{m.group(2)}({uv})")
        last = m.end()
    out.append(desc[last:])
    return "".join(out)


def _resolve_description(description: str, is_upgraded: bool,
                         player=None, enemy=None,
                         base_override=None, predicted=None) -> str:
    # Вне боя (костёр/магазин) числа уже актуальны через project_forge_values —
    # просто сворачиваем пары N(M) в одно число.
    if player is None or enemy is None:
        return _resolve_pairs(description, is_upgraded)

    # База урона = ЗНАЧЕНИЕ ЭФФЕКТА карты (base_override), а не число из строки:
    # ковка (+δ) бампит эффект, но НЕ строку описания. printed_base — что напечатано
    # в урон-паре (для решения, надо ли подсветить изменённое число).
    printed_base = _get_base_damage(description, is_upgraded)
    base_dmg = base_override if base_override is not None else printed_base
    if base_dmg == 0:
        return _resolve_pairs(description, is_upgraded)

    # Показанное число = ГАРАНТИРОВАННОЕ (predicted считает renderer через
    # EffectCalculator.preview: баффы игрока + дебаффы врага + Заточка + уровень,
    # БЕЗ условных комбо/forge — те идут чипами). Fallback (контексты без боя) —
    # локальный детерминир. расчёт. Превью == фактический удар (единый источник).
    if predicted is None:
        predicted = EffectCalculator.calculate_damage(
            attacker=player, target=enemy, base_damage=base_dmg, dry_run=True,
        )

    # Подсвечиваем число, только если оно отличается от напечатанного (модификатор/
    # ковка). Замену ЦЕЛИМ строго в урон-пару N(M), а остальные пары сворачиваем —
    # так счётчик ударов «3 удара» в мульти-хит картах не перетирается уроном.
    dmg_pair = _DMG_PAIR_RE.search(description)
    if predicted != printed_base:
        marked = DMG_MARKER + str(predicted)
        if dmg_pair is not None:
            head = _resolve_pairs(description[:dmg_pair.start()], is_upgraded)
            tail = _resolve_pairs(description[dmg_pair.end():], is_upgraded)
            return head + marked + tail
        # Карта без пары (урон бара числом) — заменяем первое число.
        return re.sub(r'\d+', marked, _resolve_pairs(description, is_upgraded),
                      count=1)
    return _resolve_pairs(description, is_upgraded)


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
