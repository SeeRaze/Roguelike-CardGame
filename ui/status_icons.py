# ui/status_icons.py
# Геометрические иконки статус-эффектов (вместо текстовых аббревиатур в бейджах).
# Эталон стиля — ui/map_icons.py (рисование примитивами pygame, без ассетов).
# Диспетчер draw_status_icon(screen, key, cx, cy, r, color): рисует символ статуса
# в квадрате радиуса r вокруг (cx, cy) цветом color. Неизвестный ключ → буквенный
# фолбэк (первая буква аббревиатуры из StatusRegistry). Data-driven остаётся:
# набор ключей берётся из STATUSES, цвет — из badge_fg.
import pygame

from core.StatusRegistry import STATUSES

# Кэш мелкого шрифта для буквенного фолбэка (создаётся лениво — pygame.init).
_FALLBACK_FONT = None


def _fallback_font(size: int):
    global _FALLBACK_FONT
    if _FALLBACK_FONT is None or _FALLBACK_FONT.get_height() != size:
        _FALLBACK_FONT = pygame.font.SysFont("Arial", size, bold=True)
    return _FALLBACK_FONT


# ── Примитивы-помощники (переиспользуются несколькими иконками) ──────────────

def _droplet(screen, cx, cy, r, color):
    """Капля (вода/кровь/яд): круг снизу + остриё сверху."""
    br = int(r * 0.62)
    bcy = cy + int(r * 0.25)
    pygame.draw.circle(screen, color, (cx, bcy), br)
    pts = [(cx, cy - r), (cx - br, bcy), (cx + br, bcy)]
    pygame.draw.polygon(screen, color, pts)


def _arrow(screen, cx, cy, r, color, up=True):
    """Толстая вертикальная стрелка вверх/вниз."""
    w = max(3, int(r * 0.45))
    head = int(r * 0.6)
    if up:
        tip_y, base_y = cy - r, cy + r
        pygame.draw.line(screen, color, (cx, base_y), (cx, tip_y), w)
        pygame.draw.polygon(screen, color, [
            (cx, tip_y), (cx - head, tip_y + head), (cx + head, tip_y + head)])
    else:
        tip_y, base_y = cy + r, cy - r
        pygame.draw.line(screen, color, (cx, base_y), (cx, tip_y), w)
        pygame.draw.polygon(screen, color, [
            (cx, tip_y), (cx - head, tip_y - head), (cx + head, tip_y - head)])


def _flame(screen, cx, cy, r, color):
    """Язык пламени: вытянутый треугольник с изгибом основания."""
    pts = [
        (cx, cy - r),
        (cx + int(r * 0.7), cy + int(r * 0.3)),
        (cx + int(r * 0.35), cy + r),
        (cx - int(r * 0.35), cy + r),
        (cx - int(r * 0.7), cy + int(r * 0.3)),
    ]
    pygame.draw.polygon(screen, color, pts)


def _shield(screen, cx, cy, r, color, filled=True):
    """Геральдический щит."""
    pts = [
        (cx - int(r * 0.75), cy - int(r * 0.8)),
        (cx + int(r * 0.75), cy - int(r * 0.8)),
        (cx + int(r * 0.75), cy + int(r * 0.1)),
        (cx, cy + r),
        (cx - int(r * 0.75), cy + int(r * 0.1)),
    ]
    pygame.draw.polygon(screen, color, pts, 0 if filled else max(2, int(r * 0.22)))


def _plus(screen, cx, cy, r, color):
    """Медицинский крест (хил/реген)."""
    w = max(3, int(r * 0.42))
    pygame.draw.line(screen, color, (cx, cy - r), (cx, cy + r), w)
    pygame.draw.line(screen, color, (cx - r, cy), (cx + r, cy), w)


def _skull(screen, cx, cy, r, color):
    """Череп: голова-круг + два глаза + зубцы челюсти."""
    pygame.draw.circle(screen, color, (cx, cy - int(r * 0.15)), int(r * 0.7))
    eye = max(2, int(r * 0.16))
    bg = (15, 15, 15)
    for ex in (cx - int(r * 0.28), cx + int(r * 0.28)):
        pygame.draw.circle(screen, bg, (ex, cy - int(r * 0.2)), eye)
    # Челюсть
    jaw_w = int(r * 0.5)
    jaw_y = cy + int(r * 0.45)
    pygame.draw.rect(screen, color,
                     (cx - jaw_w, cy + int(r * 0.25), jaw_w * 2, int(r * 0.4)))
    for jx in (cx - int(r * 0.2), cx, cx + int(r * 0.2)):
        pygame.draw.line(screen, bg, (jx, cy + int(r * 0.3)), (jx, jaw_y), 1)


def _bolt(screen, cx, cy, r, color):
    """Молния-зигзаг."""
    pts = [
        (cx + int(r * 0.25), cy - r),
        (cx - int(r * 0.45), cy + int(r * 0.1)),
        (cx + int(r * 0.05), cy + int(r * 0.1)),
        (cx - int(r * 0.25), cy + r),
        (cx + int(r * 0.5), cy - int(r * 0.2)),
        (cx, cy - int(r * 0.2)),
    ]
    pygame.draw.polygon(screen, color, pts)


def _star(screen, cx, cy, r, color, points=4):
    """Искрящаяся звезда (мастерство): остроконечная N-лучевая."""
    import math
    pts = []
    for i in range(points * 2):
        ang = math.pi * i / points - math.pi / 2
        rad = r if i % 2 == 0 else int(r * 0.38)
        pts.append((cx + int(rad * math.cos(ang)),
                    cy + int(rad * math.sin(ang))))
    pygame.draw.polygon(screen, color, pts)


# ── Диспетчер ────────────────────────────────────────────────────────────────

def draw_status_icon(screen, key: str, cx: int, cy: int, r: int, color) -> None:
    """Рисует иконку статуса key в квадрате радиуса r вокруг (cx, cy)."""
    lw = max(2, int(r * 0.28))   # стандартная толщина штриха

    if key == "vulnerable":
        # Прицел: круг + перекрестие + точка (цель «на мушке»).
        pygame.draw.circle(screen, color, (cx, cy), r, lw)
        pygame.draw.line(screen, color, (cx - r, cy), (cx + r, cy), lw)
        pygame.draw.line(screen, color, (cx, cy - r), (cx, cy + r), lw)

    elif key == "weak":
        _arrow(screen, cx, cy, r, color, up=False)

    elif key == "strength":
        _arrow(screen, cx, cy, r, color, up=True)

    elif key == "wet":
        _droplet(screen, cx, cy, r, color)
        # Волна-блик под каплей.
        pygame.draw.arc(screen, (255, 255, 255),
                        (cx - int(r * 0.3), cy, int(r * 0.6), int(r * 0.5)),
                        3.6, 5.8, max(1, lw // 2))

    elif key == "ignited":
        _flame(screen, cx, cy, r, color)

    elif key == "poison":
        _skull(screen, cx, cy, r, color)

    elif key == "bleed":
        _droplet(screen, cx, cy, r, color)

    elif key == "regen":
        _plus(screen, cx, cy, r, color)

    elif key == "thorns":
        # Шипастая звезда (отражение).
        _star(screen, cx, cy, r, color, points=6)

    elif key == "vampire":
        # Два клыка под дугой.
        pygame.draw.arc(screen, color,
                        (cx - r, cy - r, r * 2, r * 2), 0.2, 2.94, lw)
        for fx in (cx - int(r * 0.35), cx + int(r * 0.35)):
            pygame.draw.polygon(screen, color, [
                (fx - int(r * 0.18), cy),
                (fx + int(r * 0.18), cy),
                (fx, cy + r)])

    elif key == "shock":
        _bolt(screen, cx, cy, r, color)

    elif key == "shatter":
        # Трещина-зигзаг с ответвлением.
        main = [
            (cx - int(r * 0.1), cy - r),
            (cx + int(r * 0.3), cy - int(r * 0.2)),
            (cx - int(r * 0.2), cy + int(r * 0.2)),
            (cx + int(r * 0.15), cy + r),
        ]
        pygame.draw.lines(screen, color, False, main, lw)
        pygame.draw.line(screen, color,
                         (cx + int(r * 0.3), cy - int(r * 0.2)),
                         (cx + r, cy - int(r * 0.5)), max(1, lw - 1))

    elif key == "echo":
        # Звуковые дуги-эхо (рябь вправо).
        for i, rad in enumerate((int(r * 0.45), int(r * 0.75), r)):
            pygame.draw.arc(screen, color,
                            (cx - rad, cy - rad, rad * 2, rad * 2),
                            -1.0, 1.0, max(1, lw - i // 1))

    elif key == "barrier":
        _shield(screen, cx, cy, r, color, filled=False)

    elif key == "mastery":
        _star(screen, cx, cy, r, color, points=4)

    elif key == "discipline":
        # Ровный строй (порядок/дисциплина): 4 вертикальных столбика одинаковой
        # высоты на общей базе. Отличается от barrier (контур щита) — это про строй,
        # а не защиту. Тема Воина «держишь строй → +урон».
        base_y = cy + r
        top_y  = cy - r
        for col in (-int(r * 0.66), -int(r * 0.22), int(r * 0.22), int(r * 0.66)):
            pygame.draw.line(screen, color, (cx + col, top_y), (cx + col, base_y), lw)
        pygame.draw.line(screen, color, (cx - r, base_y), (cx + r, base_y), lw)

    elif key == "instability":
        # Предупреждающий треугольник с «!» (нестабильность/глитч/ошибка). Тема
        # айти-сеттинга (warning-токен) — ресурс «Нестабильность» Химика/Мага.
        pts = [(cx, cy - r), (cx - r, cy + int(r * 0.85)), (cx + r, cy + int(r * 0.85))]
        pygame.draw.polygon(screen, color, pts, lw)
        pygame.draw.line(screen, color,
                         (cx, cy - int(r * 0.2)), (cx, cy + int(r * 0.35)), lw)
        pygame.draw.circle(screen, color, (cx, cy + int(r * 0.62)), max(1, lw // 2))

    elif key == "frenzy":
        # Следы когтей: три параллельные диагонали.
        for off in (-int(r * 0.45), 0, int(r * 0.45)):
            pygame.draw.line(screen, color,
                             (cx + off - int(r * 0.3), cy - r),
                             (cx + off + int(r * 0.3), cy + r), lw)

    elif key == "heal":
        # Зелёный крест-аптечка (псевдо-ключ карт лечения).
        _plus(screen, cx, cy, r, color)

    elif key == "flow":
        # Поток воздуха: две горизонтальные «ветровые» дуги-завитка.
        for off in (-int(r * 0.35), int(r * 0.35)):
            pygame.draw.arc(screen, color,
                            (cx - r, cy + off - int(r * 0.5), int(r * 1.5), r),
                            0.3, 3.0, lw)
            pygame.draw.circle(screen, color,
                               (cx + int(r * 0.5), cy + off), max(1, lw // 2))

    elif key == "detonate":
        # Взрыв-вспышка: 8-лучевая «бахнувшая» звезда + ядро.
        _star(screen, cx, cy, r, color, points=8)
        pygame.draw.circle(screen, color, (cx, cy), max(2, int(r * 0.3)))

    elif key == "spread":
        # Распространение: центр + 4 разлетающиеся точки-стрелки.
        pygame.draw.circle(screen, color, (cx, cy), max(2, int(r * 0.28)))
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            ex, ey = cx + dx * r, cy + dy * r
            pygame.draw.line(screen, color, (cx, cy), (ex, ey), max(1, lw - 1))
            pygame.draw.circle(screen, color, (ex, ey), max(1, int(r * 0.18)))

    else:
        # Фолбэк: первая буква аббревиатуры статуса.
        data = STATUSES.get(key)
        ch = (data["abbr"][:1] if data and data.get("abbr") else "?")
        font = _fallback_font(max(10, int(r * 1.6)))
        surf = font.render(ch, True, color)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))
