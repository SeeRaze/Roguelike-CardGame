import pygame

NODE_COLORS = {
    "COMBAT":   (200, 60,  60),
    "ELITE":    (180, 80,  220),
    "CAMPFIRE": (220, 140, 40),
    "SHOP":     (60,  180, 60),
    "CHEST":    (180, 140, 40),
    "EVENT":    (60,  120, 200),
    "BOSS":     (220, 40,  40),
}

NODE_LABELS = {
    "COMBAT":   "Битва",
    "ELITE":    "Элита",
    "CAMPFIRE": "Привал",
    "SHOP":     "Магазин",
    "CHEST":    "Сундук",
    "EVENT":    "Событие",
    "BOSS":     "БОСС",
}

MAP_LEFT = 120
MAP_RIGHT = 1820
ROW_Y = [300, 540, 780]

NODE_R     = 18
NODE_R_ACT = 24
NODE_R_BSS = 30


def node_pos(row: int, col: int, total_rows: int) -> tuple:
    t = row / (total_rows - 1) if total_rows > 1 else 0
    x = int(MAP_LEFT + t * (MAP_RIGHT - MAP_LEFT))
    y = ROW_Y[col]
    return x, y


def draw_node_icon(screen, ntype: str, cx: int, cy: int,
                   r: int, fill: tuple, border: tuple, bw: int):
    """Рисует иконку узла по типу. cx/cy — центр, r — радиус."""

    pygame.draw.circle(screen, fill,   (cx, cy), r)
    pygame.draw.circle(screen, border, (cx, cy), r, bw)

    ic = tuple(min(255, c + 80) for c in fill)

    if ntype == "COMBAT":
        w = int(r * 0.55)
        pygame.draw.line(screen, ic, (cx - w, cy - w), (cx + w, cy + w), 3)
        pygame.draw.line(screen, ic, (cx + w, cy - w), (cx - w, cy + w), 3)
        hw = int(r * 0.25)
        pygame.draw.line(screen, ic, (cx - w - hw, cy - w + hw),
                         (cx - w + hw, cy - w - hw), 2)
        pygame.draw.line(screen, ic, (cx + w - hw, cy + w + hw),
                         (cx + w + hw, cy + w - hw), 2)

    elif ntype == "ELITE":
        base_y = cy + int(r * 0.35)
        base_l = cx - int(r * 0.55)
        base_r = cx + int(r * 0.55)
        top_y  = cy - int(r * 0.45)
        mid_y  = cy - int(r * 0.1)
        pts = [
            (base_l, base_y),
            (base_l, mid_y),
            (cx - int(r * 0.28), top_y),
            (cx,                 mid_y - int(r * 0.15)),
            (cx,                 top_y - int(r * 0.1)),
            (cx,                 mid_y - int(r * 0.15)),
            (cx + int(r * 0.28), top_y),
            (base_r, mid_y),
            (base_r, base_y),
        ]
        pygame.draw.polygon(screen, ic, pts)
        pygame.draw.polygon(screen, border, pts, 1)

    elif ntype == "CAMPFIRE":
        for dx, scale in ((-int(r*0.3), 0.55), (0, 0.75), (int(r*0.3), 0.55)):
            tip_y  = cy - int(r * scale)
            base_w = int(r * 0.22)
            base_y = cy + int(r * 0.3)
            pts = [(cx + dx, tip_y),
                   (cx + dx - base_w, base_y),
                   (cx + dx + base_w, base_y)]
            pygame.draw.polygon(screen, ic, pts)
        pygame.draw.line(screen, (160, 100, 50),
                         (cx - int(r*0.5), cy + int(r*0.35)),
                         (cx + int(r*0.5), cy + int(r*0.35)), 2)

    elif ntype == "SHOP":
        cr = int(r * 0.55)
        pygame.draw.circle(screen, ic, (cx, cy), cr)
        pygame.draw.circle(screen, fill, (cx, cy), cr, 2)
        font = pygame.font.SysFont("Arial", max(10, int(r * 0.7)), bold=True)
        surf = font.render("з", True, fill)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))

    elif ntype == "CHEST":
        bw2 = int(r * 0.65)
        bh  = int(r * 0.45)
        lx  = cx - bw2
        by  = cy - int(r * 0.1)
        pygame.draw.rect(screen, ic,
                         (lx, by, bw2 * 2, bh), border_radius=2)
        pygame.draw.rect(screen, tuple(min(255, c+30) for c in ic),
                         (lx, by - int(bh * 0.55), bw2 * 2, int(bh * 0.55)),
                         border_radius=2)
        pygame.draw.rect(screen, fill,
                         (cx - int(r*0.12), by - int(bh*0.1),
                          int(r*0.24), int(bh*0.55)), border_radius=1)

    elif ntype == "EVENT":
        font = pygame.font.SysFont("Arial", max(14, int(r * 1.1)), bold=True)
        surf = font.render("?", True, ic)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))

    elif ntype == "BOSS":
        sk_r = int(r * 0.55)
        pygame.draw.circle(screen, ic, (cx, cy - int(r*0.05)), sk_r)
        ew = int(r * 0.15)
        for ex in (cx - int(r*0.22), cx + int(r*0.22)):
            ey = cy - int(r * 0.1)
            pygame.draw.line(screen, fill,
                             (ex-ew, ey-ew), (ex+ew, ey+ew), 2)
            pygame.draw.line(screen, fill,
                             (ex+ew, ey-ew), (ex-ew, ey+ew), 2)
        tw = int(r * 0.55)
        ty = cy + int(r * 0.3)
        for i in range(3):
            tx = cx - tw + i * int(tw * 0.7) + int(tw * 0.15)
            pygame.draw.rect(screen, fill,
                             (tx, ty, int(tw*0.3), int(r*0.25)))