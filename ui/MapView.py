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

MAP_LEFT   = 120
MAP_RIGHT  = 1820
ROW_Y      = [300, 540, 780]

NODE_R     = 18
NODE_R_ACT = 24
NODE_R_BSS = 30


def _node_pos(row: int, col: int, total_rows: int) -> tuple:
    t = row / (total_rows - 1) if total_rows > 1 else 0
    x = int(MAP_LEFT + t * (MAP_RIGHT - MAP_LEFT))
    y = ROW_Y[col]
    return x, y


def _draw_node_icon(screen, ntype: str, cx: int, cy: int,
                    r: int, fill: tuple, border: tuple, bw: int):
    """Рисует иконку узла по типу. cx/cy — центр, r — радиус."""

    # Фон-круг всегда
    pygame.draw.circle(screen, fill,   (cx, cy), r)
    pygame.draw.circle(screen, border, (cx, cy), r, bw)

    ic = tuple(min(255, c + 80) for c in fill)  # цвет иконки светлее фона

    if ntype == "COMBAT":
        # Два скрещенных меча (диагональные линии с засечками)
        w = int(r * 0.55)
        pygame.draw.line(screen, ic, (cx - w, cy - w), (cx + w, cy + w), 3)
        pygame.draw.line(screen, ic, (cx + w, cy - w), (cx - w, cy + w), 3)
        # Рукояти
        hw = int(r * 0.25)
        pygame.draw.line(screen, ic, (cx - w - hw, cy - w + hw),
                         (cx - w + hw, cy - w - hw), 2)
        pygame.draw.line(screen, ic, (cx + w - hw, cy + w + hw),
                         (cx + w + hw, cy + w - hw), 2)

    elif ntype == "ELITE":
        # Корона: основание + 3 зубца
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
        # Три треугольника пламени
        for dx, scale in ((-int(r*0.3), 0.55), (0, 0.75), (int(r*0.3), 0.55)):
            tip_y  = cy - int(r * scale)
            base_w = int(r * 0.22)
            base_y = cy + int(r * 0.3)
            pts = [(cx + dx, tip_y),
                   (cx + dx - base_w, base_y),
                   (cx + dx + base_w, base_y)]
            pygame.draw.polygon(screen, ic, pts)
        # Поленья
        pygame.draw.line(screen, (160, 100, 50),
                         (cx - int(r*0.5), cy + int(r*0.35)),
                         (cx + int(r*0.5), cy + int(r*0.35)), 2)

    elif ntype == "SHOP":
        # Монета с буквой "з"
        cr = int(r * 0.55)
        pygame.draw.circle(screen, ic, (cx, cy), cr)
        pygame.draw.circle(screen, fill, (cx, cy), cr, 2)
        font = pygame.font.SysFont("Arial", max(10, int(r * 0.7)), bold=True)
        surf = font.render("з", True, fill)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))

    elif ntype == "CHEST":
        # Сундук: прямоугольник + крышка + замок
        bw2  = int(r * 0.65)
        bh   = int(r * 0.45)
        lx   = cx - bw2
        by   = cy - int(r * 0.1)
        # Тело
        pygame.draw.rect(screen, ic,
                         (lx, by, bw2 * 2, bh), border_radius=2)
        # Крышка
        pygame.draw.rect(screen, tuple(min(255, c+30) for c in ic),
                         (lx, by - int(bh * 0.55), bw2 * 2, int(bh * 0.55)),
                         border_radius=2)
        # Полоса-замок
        pygame.draw.rect(screen, fill,
                         (cx - int(r*0.12), by - int(bh*0.1),
                          int(r*0.24), int(bh*0.55)), border_radius=1)

    elif ntype == "EVENT":
        # Вопросительный знак
        font = pygame.font.SysFont("Arial", max(14, int(r * 1.1)), bold=True)
        surf = font.render("?", True, ic)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))

    elif ntype == "BOSS":
        # Череп: круг + глаза + нос
        sk_r = int(r * 0.55)
        pygame.draw.circle(screen, ic, (cx, cy - int(r*0.05)), sk_r)
        # Глаза-крестики
        ew = int(r * 0.15)
        for ex in (cx - int(r*0.22), cx + int(r*0.22)):
            ey = cy - int(r * 0.1)
            pygame.draw.line(screen, fill,
                             (ex-ew, ey-ew), (ex+ew, ey+ew), 2)
            pygame.draw.line(screen, fill,
                             (ex+ew, ey-ew), (ex-ew, ey+ew), 2)
        # Зубы
        tw = int(r * 0.55)
        ty = cy + int(r * 0.3)
        for i in range(3):
            tx = cx - tw + i * int(tw * 0.7) + int(tw * 0.15)
            pygame.draw.rect(screen, fill,
                             (tx, ty, int(tw*0.3), int(r*0.25)))


class MapView:

    @staticmethod
    def draw_map(view):
        gm     = view.gm
        screen = view.screen
        screen.fill((12, 12, 22))

        if not gm.map_grid:
            return

        total_rows      = len(gm.map_grid)
        current_row     = (gm.current_floor - 1) % total_rows
        available_nodes = gm.get_available_nodes()
        available_cols  = {n.col for n in available_nodes}
        mouse_pos       = pygame.mouse.get_pos()

        font_step = pygame.font.SysFont("Courier New", 16)
        font_tip  = pygame.font.SysFont("Arial", 22, bold=True)

        hovered_node = None

        # ── 1. ЛИНИИ ──────────────────────────────────────────────────
        for row in range(total_rows - 1):
            for col in range(3):
                node = gm.map_grid[row][col]
                x1, y1 = _node_pos(row, col, total_rows)
                for nc in node.connections:
                    x2, y2 = _node_pos(row + 1, nc, total_rows)
                    walked = ((row, col) in gm.player_path and
                              (row + 1, nc) in gm.player_path)
                    color = (200, 170, 60) if walked else (50, 50, 70)
                    width = 2 if walked else 1
                    pygame.draw.line(screen, color, (x1, y1), (x2, y2), width)

        # ── 2. УЗЛЫ ───────────────────────────────────────────────────
        for row in range(total_rows):
            for col in range(3):
                node  = gm.map_grid[row][col]
                x, y  = _node_pos(row, col, total_rows)
                ntype = node.node_type

                is_visited = (row, col) in gm.player_path
                is_avail   = (row == current_row and col in available_cols)
                is_boss    = (ntype == "BOSS")

                r = NODE_R_BSS if is_boss else (NODE_R_ACT if is_avail else NODE_R)

                is_hovered = (is_avail and
                              abs(mouse_pos[0] - x) < r + 6 and
                              abs(mouse_pos[1] - y) < r + 6)
                if is_hovered:
                    hovered_node = node

                base = NODE_COLORS.get(ntype, (120, 120, 120))

                if is_visited:
                    fill   = (30, 30, 40)
                    border = (70, 70, 85)
                    bw     = 1
                elif is_hovered:
                    fill   = tuple(min(255, c + 70) for c in base)
                    border = (255, 255, 255)
                    bw     = 3
                elif is_avail:
                    fill   = base
                    border = (255, 220, 0)
                    bw     = 3
                elif is_boss:
                    fill   = base
                    border = (220, 80, 220)
                    bw     = 3
                else:
                    fill   = tuple(c // 3 for c in base)
                    border = (38, 38, 52)
                    bw     = 1

                _draw_node_icon(screen, ntype, x, y, r, fill, border, bw)

        # ── 3. МАРКЕР ИГРОКА ──────────────────────────────────────────
        if gm.player_path:
            pr, pc = gm.player_path[-1]
            px, py = _node_pos(pr, pc, total_rows)
            pts = [
                (px,     py - NODE_R - 14),
                (px - 8, py - NODE_R - 6),
                (px,     py - NODE_R - 2),
                (px + 8, py - NODE_R - 6),
            ]
            pygame.draw.polygon(screen, (255, 240, 60), pts)

        # ── 4. НОМЕРА ШАГОВ ───────────────────────────────────────────
        for row in range(total_rows):
            x, _ = _node_pos(row, 1, total_rows)
            step_num = row + 1
            is_cur   = (row == current_row)
            color    = (255, 220, 60) if is_cur else (55, 55, 75)
            surf     = font_step.render(str(step_num), True, color)
            rect     = surf.get_rect(center=(x, 870))
            screen.blit(surf, rect)
            tick_color = (255, 220, 60) if is_cur else (40, 40, 58)
            pygame.draw.line(screen, tick_color, (x, 855), (x, 862), 1)

        # ── 5. ПОДПИСИ ПУТЕЙ ──────────────────────────────────────────
        path_labels = ["Путь A", "Путь B", "Путь C"]
        for col in range(3):
            y = ROW_Y[col]
            surf = view.ui_font.render(path_labels[col], True, (90, 90, 110))
            screen.blit(surf, (30, y - 12))

        # ── 6. HUD ────────────────────────────────────────────────────
        WHITE  = (255, 255, 255)
        YELLOW = (240, 220, 60)
        tier   = (gm.current_floor - 1) // total_rows + 1

        view.draw_text("КАРТА БАШНИ", view.main_font, WHITE, 30, 20)
        view.draw_text(
            f"Этаж: {gm.current_floor}  |  Ярус: {tier}  |  Шаг: {current_row + 1}/{total_rows}",
            view.ui_font, YELLOW, 30, 58
        )
        view.draw_text(f"Золото: {gm.player_gold} з.", view.main_font, YELLOW, 1650, 20)
        keys = getattr(gm, "player_keys", 0)
        view.draw_text(f"Ключи: {keys}", view.main_font, (255, 215, 0), 1650, 58)

        # ── 7. ЛЕГЕНДА ────────────────────────────────────────────────
        lx, ly = 30, 900
        view.draw_text("Легенда:", view.ui_font, (160, 160, 180), lx, ly)
        for i, (ntype, label) in enumerate(NODE_LABELS.items()):
            cx = lx + 16 + i * 160
            _draw_node_icon(screen, ntype, cx, ly + 36, 12,
                            NODE_COLORS[ntype], (180, 180, 180), 1)
            surf = view.ui_font.render(label, True, (200, 200, 200))
            screen.blit(surf, (cx + 20, ly + 26))

        # ── 8. ТУЛТИП ─────────────────────────────────────────────────
        if hovered_node:
            label = NODE_LABELS.get(hovered_node.node_type, hovered_node.node_type)
            tip   = font_tip.render(f"► {label}", True, (255, 240, 100))
            screen.blit(tip, (mouse_pos[0] + 18, mouse_pos[1] - 28))

        # ── 9. ПОДСКАЗКА ──────────────────────────────────────────────
        if available_nodes:
            surf = view.ui_font.render(
                "Кликните по выделенному узлу чтобы войти в комнату",
                True, (120, 120, 150)
            )
            screen.blit(surf, (30, 1040))

        view._map_hovered_col = hovered_node.col if hovered_node else None

    @staticmethod
    def handle_click(view, mouse_pos):
        gm = view.gm
        if not gm.map_grid:
            return
        total_rows      = len(gm.map_grid)
        available_nodes = gm.get_available_nodes()

        for node in available_nodes:
            x, y = _node_pos(node.row, node.col, total_rows)
            r    = NODE_R_BSS if node.node_type == "BOSS" else NODE_R_ACT
            dist = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
            if dist <= r + 6:
                room_type = node.node_type
                if room_type in ("BOSS", "ELITE"):
                    room_type = "COMBAT"
                gm.enter_chosen_room(room_type, col=node.col)
                if gm.current_state == "CHEST":
                    from ui.chest import Chest
                    Chest.init_chest(view)
                elif gm.current_state == "EVENT":
                    from ui.EventView import init_event
                    init_event(view.gm)
                return