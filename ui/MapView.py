import math

import pygame
from ui.map_icons import (
    NODE_COLORS, NODE_LABELS,
    NODE_R, NODE_R_ACT, NODE_R_BSS,
    ROW_Y, MAP_LEFT, MAP_RIGHT, MAP_BOT, PERI,
    HALO_AVAIL, HALO_BOSS, HALO_HOVER,
    node_pos, build_map_background, draw_edge, draw_node_frame,
    draw_legend_chip, pulse,
)

# Подписи путей (по числу путей-строк = len(ROW_Y)).
_PATH_LABELS = ("A", "B", "C")


class MapView:

    @staticmethod
    def draw_map(view):
        gm     = view.gm
        screen = view.screen
        W, H   = view.screen_width, view.screen_height

        if not gm.map_grid:
            screen.fill((12, 13, 27))
            return

        total_rows      = len(gm.map_grid)
        current_row     = (gm.current_floor - 1) % total_rows
        available_nodes = gm.get_available_nodes()
        available_cols  = {n.col for n in available_nodes}
        mouse_pos       = pygame.mouse.get_pos()
        path_set        = set(gm.player_path)
        last_node       = gm.player_path[-1] if gm.player_path else None

        # ── Фон (кэш): градиент + рельсы путей + сетка ярусов ──────────────
        screen.blit(build_map_background(W, H, total_rows), (0, 0))

        font_step = pygame.font.SysFont("Courier New", 15)
        font_tip  = pygame.font.SysFont("Arial", 22, bold=True)
        font_lane = pygame.font.SysFont("Arial", 20, bold=True)
        font_leg  = pygame.font.SysFont("Arial", 18)

        hovered_node = None

        # Босс-ярус: ряды 18→только центр (см. MapGenerator) → рисуем босса
        # одним крупным центральным узлом, боковые BOSS-узлы пропускаем.
        def _skip(row, col):
            row_types = {n.node_type for n in gm.map_grid[row]}
            return row_types == {"BOSS"} and col != 1

        # ── 1. РЁБРА-СВЯЗИ (сначала, под узлами) ───────────────────────────
        for row in range(total_rows - 1):
            for col in range(3):
                if _skip(row, col):
                    continue
                node = gm.map_grid[row][col]
                p1   = node_pos(row, col, total_rows)
                for nc in node.connections:
                    if _skip(row + 1, nc):
                        nc_draw = 1
                    else:
                        nc_draw = nc
                    p2 = node_pos(row + 1, nc_draw, total_rows)
                    if (row, col) in path_set and (row + 1, nc) in path_set:
                        kind = "walked"
                    elif last_node == (row, col):
                        kind = "open"
                    else:
                        kind = "locked"
                    draw_edge(screen, p1, p2, kind)

        # ── 2. УЗЛЫ ────────────────────────────────────────────────────────
        pls = pulse()
        for row in range(total_rows):
            for col in range(3):
                if _skip(row, col):
                    continue
                node  = gm.map_grid[row][col]
                x, y  = node_pos(row, col, total_rows)
                ntype = node.node_type

                is_visited = (row, col) in path_set
                is_avail   = (row == current_row and col in available_cols)
                is_boss    = (ntype == "BOSS")

                r = NODE_R_BSS if is_boss else (NODE_R_ACT if is_avail else NODE_R)

                is_hovered = (is_avail and
                              abs(mouse_pos[0] - x) < r + 8 and
                              abs(mouse_pos[1] - y) < r + 8)
                if is_hovered:
                    hovered_node = node

                base = NODE_COLORS.get(ntype, (120, 120, 120))
                halo, halo_r = None, 0

                if is_visited:
                    fill, border, bw = (34, 34, 46), (78, 78, 96), 2
                elif is_hovered:
                    fill   = tuple(min(255, c + 70) for c in base)
                    border, bw = HALO_HOVER, 3
                    halo, halo_r = HALO_HOVER, r + 16
                elif is_avail:
                    fill, border, bw = base, HALO_AVAIL, 3
                    halo   = HALO_AVAIL
                    halo_r = int(r + 10 + 8 * pls)          # дышащее свечение
                elif is_boss:
                    fill, border, bw = base, HALO_BOSS, 3
                    halo, halo_r = HALO_BOSS, int(r + 12 + 6 * pls)
                else:
                    fill   = tuple(c // 3 for c in base)
                    border, bw = (40, 42, 60), 2

                draw_node_frame(screen, ntype, x, y, r, fill, border, bw,
                                halo=halo, halo_r=halo_r)

                # Галочка на пройденном узле.
                if is_visited:
                    pygame.draw.lines(screen, (120, 210, 120), False, [
                        (x - 6, y), (x - 1, y + 6), (x + 7, y - 6)], 3)

        # ── 3. МАРКЕР ИГРОКА (парящий ромб со свечением) ───────────────────
        if gm.player_path and not _skip(*gm.player_path[-1]):
            pr, pc = gm.player_path[-1]
            px, py = node_pos(pr, pc, total_rows)
            oy = int(4 * math.sin(pygame.time.get_ticks() / 500))
            top = py - NODE_R - 20 + oy
            pts = [(px, top), (px - 9, top + 11), (px, top + 22), (px + 9, top + 11)]
            glow = pygame.Surface((40, 44), pygame.SRCALPHA)
            pygame.draw.polygon(glow, (255, 240, 60, 70),
                                [(20, 0), (4, 22), (20, 44), (36, 22)])
            screen.blit(glow, (px - 20, top - 11))
            pygame.draw.polygon(screen, (255, 240, 90), pts)
            pygame.draw.polygon(screen, (120, 90, 20), pts, 2)

        # ── 4. ТЕГИ ПУТЕЙ (слева, рамочные чипы-буквы по числу путей) ──────
        for col, y in enumerate(ROW_Y):
            label = _PATH_LABELS[col] if col < len(_PATH_LABELS) else str(col + 1)
            chip = pygame.Rect(46, y - 22, 60, 44)
            pygame.draw.rect(screen, (24, 26, 48), chip, border_radius=10)
            pygame.draw.rect(screen, PERI, chip, 2, border_radius=10)
            cs = font_lane.render(label, True, (210, 212, 245))
            screen.blit(cs, cs.get_rect(center=chip.center))

        # ── 5. ЛИНЕЙКА ЯРУСОВ (снизу) ──────────────────────────────────────
        ruler_y = MAP_BOT + 30
        for row in range(total_rows):
            x, _ = node_pos(row, 1, total_rows)
            is_cur = (row == current_row)
            color  = (255, 220, 60) if is_cur else (70, 72, 96)
            surf   = font_step.render(str(row + 1), True, color)
            screen.blit(surf, surf.get_rect(center=(x, ruler_y)))
            pygame.draw.line(screen, color, (x, ruler_y - 16), (x, ruler_y - 10),
                             2 if is_cur else 1)

        # ── 6. HEADER-ПЛАШКА (справа-сверху) ───────────────────────────────
        MapView._draw_header(view, gm, total_rows, current_row)

        # ── 7. ЛЕГЕНДА (рамочный бар снизу) ────────────────────────────────
        ly = H - 120
        bar = pygame.Rect(MAP_LEFT - 40, ly - 26, MAP_RIGHT - MAP_LEFT + 80, 52)
        bar_bg = pygame.Surface(bar.size, pygame.SRCALPHA)
        bar_bg.fill((18, 19, 36, 200))
        screen.blit(bar_bg, bar.topleft)
        pygame.draw.rect(screen, (60, 62, 96), bar, 1, border_radius=10)
        cx = bar.x + 24
        for ntype, label in NODE_LABELS.items():
            cx += draw_legend_chip(screen, ntype, label, cx, bar.centery, font_leg) + 36

        # ── 8. ТУЛТИП наведённого узла ─────────────────────────────────────
        if hovered_node:
            label = NODE_LABELS.get(hovered_node.node_type, hovered_node.node_type)
            tip   = font_tip.render(f"► {label}", True, (255, 240, 100))
            bg = pygame.Surface((tip.get_width() + 16, tip.get_height() + 10),
                                pygame.SRCALPHA)
            bg.fill((10, 10, 20, 220))
            bx, by = mouse_pos[0] + 16, mouse_pos[1] - 34
            screen.blit(bg, (bx - 8, by - 5))
            screen.blit(tip, (bx, by))

        # ── 9. ПОДСКАЗКА ───────────────────────────────────────────────────
        if available_nodes:
            surf = font_leg.render(
                "Выберите подсвеченный узел, чтобы войти в комнату",
                True, (130, 132, 165))
            screen.blit(surf, surf.get_rect(center=(W // 2, H - 42)))

        view._map_hovered_col = hovered_node.col if hovered_node else None

    @staticmethod
    def _draw_header(view, gm, total_rows, current_row):
        screen = view.screen
        tier   = (gm.current_floor - 1) // total_rows + 1
        keys   = getattr(gm, "player_keys", 0)

        panel = pygame.Rect(1488, 16, 416, 118)
        bg = pygame.Surface(panel.size, pygame.SRCALPHA)
        bg.fill((20, 21, 40, 215))
        screen.blit(bg, panel.topleft)
        pygame.draw.rect(screen, PERI, panel, 2, border_radius=12)

        info_font = pygame.font.SysFont("Courier New", 19)
        px = panel.x + 18
        title = view.main_font.render("КАРТА БАШНИ", True, (235, 236, 255))
        screen.blit(title, (px, panel.y + 12))

        info = info_font.render(
            f"Этаж {gm.current_floor}  •  Ярус {tier}  •  Шаг {current_row + 1}/{total_rows}",
            True, (240, 220, 60))
        screen.blit(info, (px, panel.y + 50))

        # Ключи — отдельной строкой (золотой ромб-маркер + число).
        ky = panel.y + 82
        pygame.draw.polygon(screen, (255, 215, 0),
                            [(px + 7, ky), (px + 13, ky + 8),
                             (px + 7, ky + 16), (px + 1, ky + 8)])
        pygame.draw.polygon(screen, (120, 90, 20),
                            [(px + 7, ky), (px + 13, ky + 8),
                             (px + 7, ky + 16), (px + 1, ky + 8)], 1)
        ks = info_font.render(f"Ключи: {keys}", True, (255, 215, 0))
        screen.blit(ks, (px + 24, ky - 2))

        # Кнопка «Сохранить и выйти» — под панелью карты. Сохраняет забег (точка MAP =
        # чистое состояние) и уводит в главное меню, откуда можно «Продолжить».
        mbtn = pygame.Rect(panel.x, panel.bottom + 12, panel.width, 44)
        hovered = mbtn.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, (60, 50, 30) if hovered else (40, 34, 22),
                         mbtn, border_radius=10)
        pygame.draw.rect(screen, (210, 180, 90), mbtn, 2, border_radius=10)
        mlbl = info_font.render("СОХРАНИТЬ И ВЫЙТИ В МЕНЮ", True, (240, 220, 150))
        screen.blit(mlbl, (mbtn.centerx - mlbl.get_width() // 2,
                           mbtn.centery - mlbl.get_height() // 2))
        view.btn_map_menu = mbtn

    @staticmethod
    def handle_click(view, mouse_pos):
        gm = view.gm
        if not gm.map_grid:
            return

        # «Сохранить и выйти»: снапшот забега → главное меню (проверяем ДО узлов карты).
        mbtn = getattr(view, "btn_map_menu", None)
        if mbtn is not None and mbtn.collidepoint(mouse_pos):
            from managers import RunSave
            RunSave.save_run(gm)
            gm.current_state = "MAIN_MENU"
            print("[КАРТА] Забег сохранён → главное меню")
            return
        total_rows      = len(gm.map_grid)
        available_nodes = gm.get_available_nodes()

        for node in available_nodes:
            x, y = node_pos(node.row, node.col, total_rows)
            r    = NODE_R_BSS if node.node_type == "BOSS" else NODE_R_ACT
            dist = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
            if dist <= r + 8:
                room_type = node.node_type
                gm.enter_chosen_room(room_type, col=node.col)
                if gm.current_state == "CHEST":
                    from ui.chest import Chest
                    Chest.init_chest(view)
                elif gm.current_state == "EVENT":
                    from ui.EventView import init_event
                    init_event(view.gm)
                return
