# ui/map_icons.py
# Карта башни: геометрия узлов + примитивы отрисовки в едином неон-тёмно-синем
# стиле проекта (как HUD/панели). Без ассетов — всё рисуется pygame.
#   • node_pos / радиусы — геометрия (используется и в MapView.handle_click).
#   • build_map_background — кэш статичного фона (градиент + рельсы путей + сетка).
#   • draw_edge — ребро-связь со свечением по состоянию (walked/open/locked).
#   • draw_node_frame — узел: halo-свечение + диск + иконка + стеклянный блик.
#   • draw_node_icon — символ типа узла (битва/элита/привал/...).
import math
import pygame

# ── Тип узла: цвет и подпись ────────────────────────────────────────────────
NODE_COLORS = {
    "COMBAT":   (210, 70,  70),
    "ELITE":    (185, 90,  225),
    "CAMPFIRE": (230, 150, 50),
    "SHOP":     (70,  190, 90),
    "CHEST":    (210, 165, 55),
    "EVENT":    (70,  140, 220),
    "BOSS":     (225, 55,  55),
}

NODE_LABELS = {
    "COMBAT":   "Битва",
    "ELITE":    "Элита",
    "CAMPFIRE": "Лестница",
    "SHOP":     "Магазин",
    "CHEST":    "Сундук",
    "EVENT":    "Событие",
    "BOSS":     "Босс",
}

# ── Геометрия раскладки (горизонтальный вид: ярусы слева→направо, 3 пути) ────
MAP_LEFT  = 150
MAP_RIGHT = 1780
ROW_Y     = [305, 515, 725]      # y трёх путей (A / B / C)
MAP_TOP   = 215                  # верх рабочей зоны (под сетку)
MAP_BOT   = 815                  # низ рабочей зоны

NODE_R     = 17
NODE_R_ACT = 24
NODE_R_BSS = 34

# ── Палитра неон-тёмной темы ────────────────────────────────────────────────
BG_TOP    = (12, 13, 27)
BG_BOTTOM = (24, 21, 44)
RAIL_COL  = (34, 36, 62)
GRID_COL  = (24, 26, 46)
PERI      = (160, 160, 255)      # фирменный сине-сиреневый (рамки панелей)

EDGE_LOCKED      = (48, 50, 78)
EDGE_OPEN        = (130, 205, 255)
EDGE_OPEN_GLOW   = (45, 105, 175)
EDGE_WALKED      = (255, 205, 90)
EDGE_WALKED_GLOW = (135, 95, 30)

HALO_AVAIL = (255, 220, 70)
HALO_BOSS  = (225, 70, 200)
HALO_HOVER = (255, 255, 255)

_BG_CACHE: dict = {}


def node_pos(row: int, col: int, total_rows: int) -> tuple:
    """Экранные координаты узла (ярус row, путь col)."""
    t = row / (total_rows - 1) if total_rows > 1 else 0
    x = int(MAP_LEFT + t * (MAP_RIGHT - MAP_LEFT))
    y = ROW_Y[col]
    return x, y


# ── Фон (кэшируется: статичен между кадрами) ────────────────────────────────

def build_map_background(w: int, h: int, total_rows: int) -> pygame.Surface:
    """Статичный фон карты: вертикальный градиент + рельсы путей + тиковая сетка
    ярусов. Кэшируется по (w, h, total_rows) — строится один раз."""
    key = (w, h, total_rows)
    cached = _BG_CACHE.get(key)
    if cached is not None:
        return cached

    surf = pygame.Surface((w, h))
    # Вертикальный градиент.
    for y in range(h):
        f = y / max(1, h - 1)
        col = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * f) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (w, y))

    # Тиковая сетка ярусов (вертикали под каждым шагом — «этажи башни»).
    if total_rows > 1:
        for row in range(total_rows):
            x = int(MAP_LEFT + row / (total_rows - 1) * (MAP_RIGHT - MAP_LEFT))
            pygame.draw.line(surf, GRID_COL, (x, MAP_TOP), (x, MAP_BOT), 1)

    # Рельсы трёх путей (горизонтальные направляющие со свечением-подложкой).
    for y in ROW_Y:
        pygame.draw.line(surf, (20, 22, 40), (MAP_LEFT - 30, y), (MAP_RIGHT + 30, y), 7)
        pygame.draw.line(surf, RAIL_COL,     (MAP_LEFT - 30, y), (MAP_RIGHT + 30, y), 2)

    _BG_CACHE[key] = surf
    return surf


# ── Свечение (мягкий радиальный halo через SRCALPHA) ────────────────────────

def _glow(screen, cx: int, cy: int, r: int, color, strength: int = 110) -> None:
    """Мягкое радиальное свечение: концентрические круги от слабого к сильному."""
    if r <= 0:
        return
    surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    layers = 5
    for i in range(layers, 0, -1):
        a  = int(strength * (i / layers) ** 2)
        rr = int(r * i / layers)
        pygame.draw.circle(surf, (*color, a), (r, r), rr)
    screen.blit(surf, (cx - r, cy - r))


# ── Ребро-связь ─────────────────────────────────────────────────────────────

def draw_edge(screen, p1, p2, kind: str) -> None:
    """Связь между узлами. kind: 'walked' (пройдено) / 'open' (доступно сейчас)
    / 'locked' (прочее). Открытые/пройденные — со свечением, остальные — тускло."""
    if kind == "walked":
        glow, core, gw, cw = EDGE_WALKED_GLOW, EDGE_WALKED, 10, 4
    elif kind == "open":
        glow, core, gw, cw = EDGE_OPEN_GLOW, EDGE_OPEN, 9, 3
    else:
        pygame.draw.line(screen, EDGE_LOCKED, p1, p2, 1)
        return

    pygame.draw.line(screen, glow, p1, p2, gw)      # подложка-свечение
    pygame.draw.line(screen, core, p1, p2, cw)      # яркое ядро
    pygame.draw.circle(screen, core, p2, cw)        # скруглённые концы
    pygame.draw.circle(screen, core, p1, cw)


# ── Узел: оправа (halo + диск + иконка + блик) ──────────────────────────────

def draw_node_frame(screen, ntype, cx, cy, r, fill, border, bw,
                    halo=None, halo_r=0) -> None:
    """Полная отрисовка узла: опциональное halo-свечение, диск, рамка, иконка типа
    и стеклянный блик сверху-слева для объёма."""
    if halo is not None and halo_r > 0:
        _glow(screen, cx, cy, halo_r, halo, strength=120)

    draw_node_icon(screen, ntype, cx, cy, r, fill, border, bw)

    # Стеклянный блик: тонкая светлая дуга по верхне-левому краю.
    if r >= 12:
        hl = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.arc(hl, (255, 255, 255, 60),
                        (3, 3, r * 2 - 6, r * 2 - 6), 0.6, 2.4, max(2, r // 7))
        screen.blit(hl, (cx - r, cy - r))


def draw_node_icon(screen, ntype: str, cx: int, cy: int,
                   r: int, fill: tuple, border: tuple, bw: int):
    """Рисует узел: диск + рамка + детализированный символ типа.
    cx/cy — центр, r — радиус. Геометрия масштабируется через r (одинаково
    выглядит и в узле, и в чипе легенды)."""
    pygame.draw.circle(screen, fill,   (cx, cy), r)
    pygame.draw.circle(screen, border, (cx, cy), r, bw)

    ic = tuple(min(255, c + 95) for c in fill)              # светлая деталь
    sh = tuple(max(0, c - 45) for c in fill)               # тень/контур

    def _rr(v):    # масштаб по радиусу
        return int(r * v)

    if ntype == "COMBAT":
        # Рогатая морда монстра (узнаваемый «обычный враг»).
        # Голова — сердцевидный силуэт с острым подбородком.
        head = [
            (cx,            cy + _rr(0.66)),
            (cx - _rr(0.6), cy + _rr(0.02)),
            (cx - _rr(0.5), cy - _rr(0.5)),
            (cx,            cy - _rr(0.28)),
            (cx + _rr(0.5), cy - _rr(0.5)),
            (cx + _rr(0.6), cy + _rr(0.02)),
        ]
        # Рога (вверх-в стороны из верхних углов лба).
        l_horn = [(cx - _rr(0.5), cy - _rr(0.45)),
                  (cx - _rr(0.24), cy - _rr(0.42)),
                  (cx - _rr(0.72), cy - _rr(0.95))]
        r_horn = [(cx + _rr(0.5), cy - _rr(0.45)),
                  (cx + _rr(0.24), cy - _rr(0.42)),
                  (cx + _rr(0.72), cy - _rr(0.95))]
        pygame.draw.polygon(screen, ic, l_horn)
        pygame.draw.polygon(screen, ic, r_horn)
        pygame.draw.polygon(screen, ic, head)
        pygame.draw.polygon(screen, sh, head, 1)
        # Злые наклонные глаза.
        pygame.draw.polygon(screen, sh, [
            (cx - _rr(0.4), cy - _rr(0.06)),
            (cx - _rr(0.1), cy + _rr(0.06)),
            (cx - _rr(0.36), cy + _rr(0.14))])
        pygame.draw.polygon(screen, sh, [
            (cx + _rr(0.4), cy - _rr(0.06)),
            (cx + _rr(0.1), cy + _rr(0.06)),
            (cx + _rr(0.36), cy + _rr(0.14))])
        # Пара клыков.
        for fx in (-_rr(0.16), _rr(0.16)):
            pygame.draw.polygon(screen, (245, 245, 240), [
                (cx + fx - _rr(0.06), cy + _rr(0.34)),
                (cx + fx + _rr(0.06), cy + _rr(0.34)),
                (cx + fx, cy + _rr(0.56))])

    elif ntype == "ELITE":
        # Корона с самоцветами (элитный враг).
        base_y = cy + _rr(0.42)
        base_l = cx - _rr(0.6)
        base_r = cx + _rr(0.6)
        top_y  = cy - _rr(0.5)
        mid_y  = cy - _rr(0.05)
        pts = [
            (base_l, base_y), (base_l, mid_y),
            (cx - _rr(0.3), top_y + _rr(0.18)),
            (cx - _rr(0.15), mid_y - _rr(0.05)),
            (cx, top_y),
            (cx + _rr(0.15), mid_y - _rr(0.05)),
            (cx + _rr(0.3), top_y + _rr(0.18)),
            (base_r, mid_y), (base_r, base_y),
        ]
        pygame.draw.polygon(screen, ic, pts)
        pygame.draw.polygon(screen, sh, pts, 1)
        # Лента-основание короны.
        pygame.draw.rect(screen, sh,
                         (base_l, base_y - _rr(0.12), _rr(1.2), _rr(0.18)))
        # Самоцветы на зубцах.
        for gx, gy in ((cx, top_y + _rr(0.16)),
                       (cx - _rr(0.3), top_y + _rr(0.3)),
                       (cx + _rr(0.3), top_y + _rr(0.3))):
            pygame.draw.circle(screen, (255, 80, 80), (gx, int(gy)), max(1, _rr(0.1)))

    elif ntype == "CAMPFIRE":
        # Костёр: двойное пламя (внешнее + жёлтое ядро) над скрещёнными поленьями.
        flame_out = [
            (cx, cy - _rr(0.75)),
            (cx + _rr(0.5), cy - _rr(0.05)),
            (cx + _rr(0.32), cy + _rr(0.4)),
            (cx - _rr(0.32), cy + _rr(0.4)),
            (cx - _rr(0.5), cy - _rr(0.05)),
        ]
        pygame.draw.polygon(screen, (255, 140, 40), flame_out)
        flame_in = [
            (cx, cy - _rr(0.4)),
            (cx + _rr(0.26), cy + _rr(0.05)),
            (cx + _rr(0.15), cy + _rr(0.35)),
            (cx - _rr(0.15), cy + _rr(0.35)),
            (cx - _rr(0.26), cy + _rr(0.05)),
        ]
        pygame.draw.polygon(screen, (255, 230, 110), flame_in)
        # Поленья крест-накрест.
        for a, b in (((-0.55, 0.62), (0.55, 0.42)),
                     ((0.55, 0.62), (-0.55, 0.42))):
            pygame.draw.line(screen, (150, 95, 50),
                             (cx + _rr(a[0]), cy + _rr(a[1])),
                             (cx + _rr(b[0]), cy + _rr(b[1])), max(2, _rr(0.14)))

    elif ntype == "SHOP":
        # Мешок золота: круглый мешочек, горловина с завязкой, символ монеты.
        bag_r = _rr(0.52)
        pygame.draw.circle(screen, ic, (cx, cy + _rr(0.12)), bag_r)
        pygame.draw.circle(screen, sh, (cx, cy + _rr(0.12)), bag_r, 1)
        # Горловина.
        neck = [(cx - _rr(0.3), cy - _rr(0.35)),
                (cx + _rr(0.3), cy - _rr(0.35)),
                (cx + _rr(0.18), cy - _rr(0.08)),
                (cx - _rr(0.18), cy - _rr(0.08))]
        pygame.draw.polygon(screen, sh, neck)
        # Завязка.
        pygame.draw.line(screen, (240, 230, 120),
                         (cx - _rr(0.22), cy - _rr(0.22)),
                         (cx + _rr(0.22), cy - _rr(0.22)), max(1, _rr(0.1)))
        # Монетный знак на мешке.
        font = pygame.font.SysFont("Arial", max(9, _rr(0.6)), bold=True)
        surf = font.render("$", True, (255, 235, 120))
        screen.blit(surf, surf.get_rect(center=(cx, cy + _rr(0.16))))

    elif ntype == "CHEST":
        # Сундук: корпус + выпуклая крышка + оковки + замок.
        bw2 = _rr(0.6)
        body_top = cy - _rr(0.02)
        body_h   = _rr(0.5)
        pygame.draw.rect(screen, ic, (cx - bw2, body_top, bw2 * 2, body_h),
                         border_radius=2)
        # Крышка-дуга.
        lid = pygame.Rect(cx - bw2, cy - _rr(0.5), bw2 * 2, _rr(0.62))
        pygame.draw.rect(screen, tuple(min(255, c + 25) for c in ic), lid,
                         border_top_left_radius=_rr(0.5),
                         border_top_right_radius=_rr(0.5))
        pygame.draw.line(screen, sh, (cx - bw2, body_top), (cx + bw2, body_top),
                         max(1, _rr(0.08)))
        # Вертикальные оковки.
        for ox in (-_rr(0.4), _rr(0.4)):
            pygame.draw.line(screen, sh, (cx + ox, cy - _rr(0.45)),
                             (cx + ox, cy + body_top - cy + body_h), max(1, _rr(0.1)))
        # Замок.
        pygame.draw.rect(screen, (250, 220, 110),
                         (cx - _rr(0.12), body_top - _rr(0.06),
                          _rr(0.24), _rr(0.28)), border_radius=1)

    elif ntype == "EVENT":
        # Знак вопроса в ромбе-табличке.
        diamond = [(cx, cy - _rr(0.8)), (cx + _rr(0.8), cy),
                   (cx, cy + _rr(0.8)), (cx - _rr(0.8), cy)]
        pygame.draw.polygon(screen, ic, diamond)
        pygame.draw.polygon(screen, sh, diamond, 1)
        font = pygame.font.SysFont("Arial", max(12, _rr(1.0)), bold=True)
        surf = font.render("?", True, sh)
        screen.blit(surf, surf.get_rect(center=(cx, cy - _rr(0.02))))

    elif ntype == "BOSS":
        # Череп: купол + большие глазницы + нос + ряд зубов + венец-зубцы.
        dome_r = _rr(0.52)
        cyc    = cy - _rr(0.12)
        pygame.draw.circle(screen, (235, 235, 240), (cx, cyc), dome_r)
        # Челюсть.
        jaw = pygame.Rect(cx - _rr(0.34), cyc + _rr(0.2), _rr(0.68), _rr(0.4))
        pygame.draw.rect(screen, (235, 235, 240), jaw, border_radius=2)
        # Глазницы.
        for ex in (-_rr(0.24), _rr(0.24)):
            pygame.draw.circle(screen, (20, 18, 28),
                               (cx + ex, cyc - _rr(0.02)), max(2, _rr(0.18)))
        # Нос.
        pygame.draw.polygon(screen, (20, 18, 28), [
            (cx, cyc + _rr(0.06)),
            (cx - _rr(0.08), cyc + _rr(0.24)),
            (cx + _rr(0.08), cyc + _rr(0.24))])
        # Зубы.
        for tx in (-_rr(0.18), 0, _rr(0.18)):
            pygame.draw.line(screen, (20, 18, 28),
                             (cx + tx, cyc + _rr(0.34)),
                             (cx + tx, cyc + _rr(0.56)), 1)


def draw_legend_chip(screen, ntype, label, x, y, font):
    """Чип легенды: иконка + подпись (используется в MapView). Возвращает ширину."""
    draw_node_icon(screen, ntype, x + 13, y, 12,
                   NODE_COLORS[ntype], (190, 190, 210), 1)
    surf = font.render(label, True, (205, 205, 220))
    screen.blit(surf, (x + 30, y - surf.get_height() // 2))
    return 30 + surf.get_width()


def pulse(period_ms: int = 1100) -> float:
    """0..1 синусоида по времени — для пульсации доступных узлов."""
    t = pygame.time.get_ticks()
    return (math.sin(t / period_ms * 2 * math.pi) + 1) / 2
