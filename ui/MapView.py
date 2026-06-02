import pygame

NODE_COLORS = {
    "COMBAT":   (200, 60,  60),
    "CAMPFIRE": (220, 140, 40),
    "SHOP":     (60,  180, 60),
    "CHEST":    (180, 140, 40),
    "EVENT":    (80,  80,  200),
    "BOSS":     (200, 40,  200),
}

NODE_LABELS = {
    "COMBAT":   "Битва",
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

                pygame.draw.circle(screen, fill,   (x, y), r)
                pygame.draw.circle(screen, border, (x, y), r, bw)

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
            cx = lx + 12 + i * 160
            pygame.draw.circle(screen, NODE_COLORS[ntype], (cx, ly + 36), 10)
            pygame.draw.circle(screen, (180, 180, 180),    (cx, ly + 36), 10, 1)
            surf = view.ui_font.render(label, True, (200, 200, 200))
            screen.blit(surf, (cx + 16, ly + 26))

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
                room_type = "COMBAT" if node.node_type == "BOSS" else node.node_type
                gm.enter_chosen_room(room_type, col=node.col)
                # Инициализируем сундук сразу при входе
                if gm.current_state == "CHEST":
                    from ui.chest import Chest
                    Chest.init_chest(view)
                    # Инициализируем событие сразу при входе
                elif gm.current_state == "EVENT":
                    from ui.EventView import init_event
                    init_event(view.gm)
                return