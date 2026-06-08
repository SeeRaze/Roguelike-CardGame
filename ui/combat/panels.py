# ui/combat/panels.py
# Боковые панели боевого экрана: панель игрока, панель врага, лог.
import pygame
from core.positioning import Rank, Line
from ui.combat.hud import CombatHUD, _RELIC_BADGE, _RELIC_GAP
from ui.combat.layout import (
    _PANEL_BG, _PANEL_BORDER, _GOLD, _WHITE, _RED, _GREEN, _BLUE, _GRAY,
    _INTENT_OTHER, _PANEL_W, _PANEL_TOP, _P_PX, _P_IX, _E_PX, _E_IW,
)

# Позиционка (§5b): бейдж ранга ФРОНТ/ТЫЛ. Фронт — тёплый («на острие»), тыл — прохладный.
_RANK_FRONT_COLOR = (230, 130, 60)
_RANK_BACK_COLOR  = (120, 160, 220)

# Ось линий (§11): краткий ярлык колонки в бейдже — «ФРОНТ·Ц», «ТЫЛ·Л».
_LINE_ABBR = {Line.LEFT: "Л", Line.CENTER: "Ц", Line.RIGHT: "П"}


def _fit_text(font, text, max_w):
    """Усечь строку с «…», чтобы её рендер влез в max_w пикселей (имена врагов в
    групповом бою выезжали за рамку панели). Возвращает готовую к рендеру строку."""
    if font.size(text)[0] <= max_w:
        return text
    ell = "…"
    # Откусываем с конца, пока «текст…» не влезет (или не останется 1 символ).
    while text and font.size(text + ell)[0] > max_w:
        text = text[:-1]
    return (text + ell) if text else ell


def _draw_rank_chip(screen, font, rank, x, y, line=None):
    """Мини-бейдж 2D-позиции: ранг (ФРОНТ/ТЫЛ) + опц. линия (·Л/·Ц/·П) от (x, y).
    rank=None → ничего не рисует (позиционка выключена). Возвращает Rect или None."""
    if rank is None:
        return None
    text  = "ФРОНТ" if rank == Rank.FRONT else "ТЫЛ"
    abbr  = _LINE_ABBR.get(line)
    if abbr:
        text = f"{text}·{abbr}"
    color = _RANK_FRONT_COLOR if rank == Rank.FRONT else _RANK_BACK_COLOR
    label = font.render(text, True, color)
    chip  = pygame.Rect(x, y, label.get_width() + 8, label.get_height() + 4)
    pygame.draw.rect(screen, (25, 25, 35), chip, border_radius=4)
    pygame.draw.rect(screen, color, chip, 1, border_radius=4)
    screen.blit(label, (chip.x + 4, chip.y + 2))
    return chip


def draw_player_panel(view, screen, player, intent_dmg):
    panel_h = 440
    panel   = pygame.Rect(_P_PX, _PANEL_TOP, _PANEL_W, panel_h)
    pygame.draw.rect(screen, _PANEL_BG, panel, border_radius=12)
    pygame.draw.rect(screen, _PANEL_BORDER, panel, 2, border_radius=12)

    x, y = _P_IX, _PANEL_TOP + 20

    title = view.main_font.render("ИГРОК", True, _WHITE)
    screen.blit(title, (x, y))
    # Позиционка (§5b): бейдж ранга героя рядом с заголовком (None → нет бейджа).
    _draw_rank_chip(screen, view.card_desc_font, getattr(player, "rank", None),
                    x + title.get_width() + 16, y + 6, getattr(player, "line", None))

    y += 44
    CombatHUD.draw_hp_bar(
        screen, x, y, _E_IW, 26,
        player.hp, player.max_hp, player.shield,
        incoming_dmg=intent_dmg
    )
    y += 32
    shld_str = f"  +{player.shield} щит" if player.shield > 0 else ""
    screen.blit(view.card_desc_font.render(
        f"HP: {player.hp} / {player.max_hp}{shld_str}", True, _GREEN
    ), (x, y))

    y += 44
    screen.blit(view.card_desc_font.render("Энергия:", True, _BLUE), (x, y))
    CombatHUD.draw_energy_diamonds(
        screen, x + 120, y - 2,
        player.energy, player.max_energy, size=14
    )

    # Артефакты (реликвии) — в панели героя (перенесены из верхней плашки; золото/FP
    # ушли в единую строку ресурсов слева-сверху). Клик по метке открывает модальный
    # инвентарь; слот «+N» при переполнении — тоже.
    y += 42
    lbl = view.card_desc_font.render("АРТЕФАКТЫ:", True, _GOLD)
    lbl_rect = pygame.Rect(x - 4, y - 4, lbl.get_width() + 10, 26)
    if lbl_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(screen, (40, 40, 60), lbl_rect, border_radius=4)
    screen.blit(lbl, (x, y))
    view.relic_panel_btn_rect = lbl_rect
    view.relic_overflow_rect  = None

    ry = y + 30
    if hasattr(view.gm, 'relics') and view.gm.relics:
        view.relic_rects, hidden = CombatHUD.draw_relics(
            screen, view.gm.relics, x, ry, max_x=x + _E_IW)
        if hidden > 0:
            ox    = x + len(view.relic_rects) * (_RELIC_BADGE + _RELIC_GAP)
            orect = pygame.Rect(ox, ry, _RELIC_BADGE, _RELIC_BADGE)
            pygame.draw.rect(screen, (45, 45, 70), orect, border_radius=6)
            pygame.draw.rect(screen, _GOLD, orect, 2, border_radius=6)
            plus = view.card_desc_font.render(f"+{hidden}", True, _GOLD)
            screen.blit(plus, (orect.centerx - plus.get_width() // 2,
                               orect.centery - plus.get_height() // 2))
            view.relic_overflow_rect = orect
    else:
        view.relic_rects = []
    y = ry + _RELIC_BADGE

    # Статусы
    y += 38
    pygame.draw.line(screen, _PANEL_BORDER, (x, y), (x + _E_IW, y), 1)
    y += 10
    view.player_badge_rects = CombatHUD.draw_status_badges(
        screen, view.card_desc_font, player, x, y
    )

    # Слот активной способности
    y += 44
    pygame.draw.line(screen, _PANEL_BORDER, (x, y), (x + _E_IW, y), 1)
    y += 10
    ability = getattr(player, 'active_ability', None)
    if ability:
        view.ability_rect = CombatHUD.draw_ability_slot(
            screen, view.card_desc_font, ability, x, y
        )
    else:
        view.ability_rect = None


def draw_enemy_panels(view, screen, enemies, player, projection=None):
    """Отрисовка панелей врагов. 1 враг — полноразмерная, 2–3 — компактные.
    `projection` — {враг: полный_урон наведённой карты} для визуальной проекции
    на HP-баре (цель для одиночных атак, все враги для AoE)."""
    projection = projection or {}
    n = len(enemies)
    if n == 0:
        view.enemy_panel_rects = []
        view.enemy_badge_rects = []
        return

    # Размеры панелей в зависимости от количества врагов
    if n == 1:
        panel_w = _PANEL_W                         # 560 — как раньше
        gap = 0
    elif n == 2:
        panel_w = 270
        gap = 20
    else:  # n == 3
        panel_w = 180
        gap = 10

    panel_h = 380
    # Внутренний отступ пропорционален ширине панели
    inner_pad = max(10, int(panel_w * 0.04))

    view.enemy_panel_rects = []
    all_badges = []  # список (rect, key, val, enemy) для ховера

    for i, enemy in enumerate(enemies):
        px = _E_PX + i * (panel_w + gap)
        py = _PANEL_TOP
        panel_rect = pygame.Rect(px, py, panel_w, panel_h)
        view.enemy_panel_rects.append(panel_rect)

        pygame.draw.rect(screen, _PANEL_BG, panel_rect, border_radius=12)
        border_color = _PANEL_BORDER
        pygame.draw.rect(screen, border_color, panel_rect, 2, border_radius=12)

        x, y = px + inner_pad, py + 16

        # --- Мёртвый враг: затемнённая панель ---
        if enemy.hp <= 0:
            dim = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 120))
            screen.blit(dim, (px, py))
            dead_text = view.card_desc_font.render("ПОВЕРЖЕН", True, _GRAY)
            screen.blit(dead_text, (px + (panel_w - dead_text.get_width()) // 2,
                                    py + panel_h // 2 - 12))
            continue

        # --- Имя ---
        name_font = view.main_font if n <= 2 else view.card_desc_font
        enemy_label = f"ВРАГ: {enemy.name}" if n <= 2 else enemy.name.split("(")[0].strip()
        # Усечение по ширине: при нескольких длинных именах текст выезжал за рамку.
        # Резервируем место справа под бейдж ранга (~84px) + внутренний отступ.
        name_max_w = panel_w - inner_pad * 2 - 84
        enemy_label = _fit_text(name_font, enemy_label, name_max_w)
        screen.blit(name_font.render(enemy_label, True, _WHITE), (x, y))

        # Позиционка (§11): бейдж ранга врага (ФРОНТ/ТЫЛ·линия) в правом-верхнем углу —
        # читаемость перехвата (жив фронт → тыл недостижим). None → нет (позиционка off).
        _draw_rank_chip(screen, view.card_desc_font, getattr(enemy, "rank", None),
                        px + panel_w - 78, py + 8, getattr(enemy, "line", None))

        # --- HP-бар (ширина под панель) ---
        bar_w = panel_w - inner_pad * 2
        y += 36
        CombatHUD.draw_hp_bar(
            screen, x, y, bar_w, 22,
            enemy.hp, enemy.max_hp, enemy.shield,
            incoming_dmg=projection.get(enemy, 0),
        )
        y += 26
        hp_font = view.card_desc_font
        shld_str = f" +{enemy.shield}щ" if enemy.shield > 0 else ""
        hp_text = f"HP:{enemy.hp}/{enemy.max_hp}{shld_str}"
        screen.blit(hp_font.render(hp_text, True, _RED), (x, y))

        # --- Намерение ---
        y += 34
        line_end = x + bar_w
        pygame.draw.line(screen, _PANEL_BORDER, (x, y - 4), (line_end, y - 4), 1)
        intent = enemy.intent
        if isinstance(intent, type(pygame.Rect)):  # fallback — intent всегда есть
            pass
        if enemy.intent_type == "attack":
            dmg_color = CombatHUD.get_intent_damage_color(
                enemy.intent_value, player.shield)
            intent_text = f"Атака {enemy.intent_value}"
            screen.blit(hp_font.render(intent_text, True, dmg_color), (x, y))
        elif enemy.intent_type == "defend":
            screen.blit(hp_font.render(f"Защита {enemy.intent_value}", True, _BLUE), (x, y))
        elif enemy.intent_type == "debuff":
            screen.blit(hp_font.render(f"Слабость {enemy.intent_value}", True, _INTENT_OTHER), (x, y))
        else:
            screen.blit(hp_font.render("—", True, _GRAY), (x, y))

        # --- Статусы ---
        y += 30
        pygame.draw.line(screen, _PANEL_BORDER, (x, y), (line_end, y), 1)
        y += 8
        badges = CombatHUD.draw_status_badges(
            screen, view.card_desc_font, enemy, x, y
        )
        for rect, key, val in badges:
            all_badges.append((rect, key, val, enemy))

    view.enemy_badge_rects = all_badges


def draw_ally_panels(view, screen, allies):
    """Отрисовка панелей союзников в центральной зоне (x=590..1330).

    Позиционка (§5b): если союзники расставлены по рангам — рисуем ДВА ряда (фронт
    сверху, тыл снизу) + бейдж ранга на каждой панели. Без рангов (позиционка off) —
    прежний одноряд (нулевой визуальный регресс)."""
    living = [a for a in allies if a.hp > 0]
    if not living:
        view.ally_panel_rects = []
        return

    # Мини-панель союзника
    ally_w = 160
    ally_h = 180
    gap = 20
    start_x = 610                     # левый край центральной зоны + отступ
    start_y = _PANEL_TOP + 10

    view.ally_panel_rects = []

    # Раскладка по рядам: с рангами → фронт/тыл; без рангов → один ряд (как раньше).
    positioned = any(getattr(a, "rank", None) is not None for a in living)
    # Колонки по линии (§11): внутри ряда сортируем Л→Ц→П, чтобы 2D-сетка читалась.
    _line_order = {Line.LEFT: 0, Line.CENTER: 1, Line.RIGHT: 2}
    if positioned:
        rows = [
            sorted([a for a in living if getattr(a, "rank", None) == Rank.FRONT],
                   key=lambda a: _line_order.get(getattr(a, "line", None), 1)),
            sorted([a for a in living if getattr(a, "rank", None) == Rank.BACK],
                   key=lambda a: _line_order.get(getattr(a, "line", None), 1)),
        ]
    else:
        rows = [living]

    for row_idx, row in enumerate(rows):
        py = start_y + row_idx * (ally_h + gap)
        for col_idx, ally in enumerate(row):
            px = start_x + col_idx * (ally_w + gap)
            panel_rect = pygame.Rect(px, py, ally_w, ally_h)
            view.ally_panel_rects.append(panel_rect)

            # Фон и рамка (зеленоватый оттенок для союзников)
            ally_bg = (20, 40, 20)
            pygame.draw.rect(screen, ally_bg, panel_rect, border_radius=10)
            pygame.draw.rect(screen, (60, 140, 60), panel_rect, 2, border_radius=10)

            x, y = px + 10, py + 10

            # Имя (усекаем по ширине) + бейдж ранга справа. Резерв ~46px под чип ранга.
            ally_name = _fit_text(view.card_desc_font, ally.name, ally_w - 20 - 46)
            name_surf = view.card_desc_font.render(ally_name, True, _GREEN)
            screen.blit(name_surf, (x, y))
            _draw_rank_chip(screen, view.card_desc_font, getattr(ally, "rank", None),
                            x + name_surf.get_width() + 6, y, getattr(ally, "line", None))

            # HP-бар
            y += 26
            bar_w = ally_w - 20
            CombatHUD.draw_hp_bar(
                screen, x, y, bar_w, 16,
                ally.hp, ally.max_hp, ally.shield,
            )
            y += 20
            hp_text = f"HP:{ally.hp}/{ally.max_hp}"
            if ally.shield > 0:
                hp_text += f" +{ally.shield}щ"
            screen.blit(view.card_desc_font.render(hp_text, True, _WHITE), (x, y))

            # Атака
            y += 24
            atk_text = f"Атака: {ally.attack_power}"
            screen.blit(view.card_desc_font.render(atk_text, True, _GOLD), (x, y))

            # Статусы (компактно)
            y += 24
            CombatHUD.draw_status_badges(
                screen, view.card_desc_font, ally, x, y
            )


def draw_combat_log(view, screen, combat):
    # Позиция: под панелями врагов (если есть enemy_panel_rects) или фиксированно
    if hasattr(view, 'enemy_panel_rects') and view.enemy_panel_rects:
        log_top = max(r.bottom for r in view.enemy_panel_rects) + 12
    else:
        log_top = _PANEL_TOP + 400
    log = pygame.Rect(_E_PX, log_top, _PANEL_W, 260)
    pygame.draw.rect(screen, _PANEL_BG, log, border_radius=12)
    pygame.draw.rect(screen, _PANEL_BORDER, log, 2, border_radius=12)

    screen.blit(view.card_desc_font.render(
        "ЛОГ БОЕВЫХ ДЕЙСТВИЙ", True, _GOLD), (log.x + 14, log.y + 12))
    pygame.draw.line(screen, _PANEL_BORDER,
                     (log.x + 14, log.y + 36),
                     (log.right - 14, log.y + 36), 1)

    for i, msg in enumerate(combat.combat_log):
        if i >= 7:
            break
        alpha = max(150, 255 - i * 16)
        screen.blit(view.card_desc_font.render(
            msg, True, (alpha, alpha, alpha)),
            (log.x + 14, log.y + 46 + i * 26))
