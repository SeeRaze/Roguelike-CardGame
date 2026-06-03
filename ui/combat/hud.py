import pygame
from core.StatusRegistry import STATUSES
from core.rarity import RARITY_COLORS

# ── Палитра (единая тёмно-синяя тема) ──────────────────────────────────────
_PANEL_BG     = (22, 22, 40)
_PANEL_BORDER = (160, 160, 255)
_HP_BG        = (35, 35, 35)
_HP_GREEN     = (60, 200, 80)
_HP_YELLOW    = (220, 200, 50)
_HP_RED       = (200, 60, 60)
_HP_SHIELD    = (70, 160, 240)
_HP_PROJ      = (220, 80, 80)
_ENERGY_ON    = (100, 180, 255)
_ENERGY_OFF   = (40, 40, 65)
_ENERGY_BRD   = (160, 160, 255)

# Геометрия бейджа реликвии
_RELIC_BADGE = 42
_RELIC_GAP   = 8

_badge_font = None   # ленивый кэш (pygame.font готов только после init)


def _get_badge_font():
    global _badge_font
    if _badge_font is None:
        _badge_font = pygame.font.SysFont("Arial", 18, bold=True)
    return _badge_font


def _relic_abbr(name: str) -> str:
    """2-буквенная аббревиатура: инициалы двух слов либо первые 2 буквы."""
    words = name.split()
    if len(words) >= 2:
        return (words[0][:1] + words[1][:1]).upper()
    return name[:2].upper()


def _hp_color(ratio):
    if ratio > 0.5:
        return _HP_GREEN
    if ratio > 0.25:
        return _HP_YELLOW
    return _HP_RED


class CombatHUD:
    """Вспомогательные методы отрисовки HUD."""

    # ── HP-БАР С ПРОЕКЦИЕЙ УРОНА ────────────────────────────────────────────
    @staticmethod
    def draw_hp_bar(screen, x, y, width, height,
                    current_hp, max_hp, shield, incoming_dmg=0):
        pygame.draw.rect(screen, _HP_BG, (x, y, width, height), border_radius=4)

        ratio     = max(0.0, current_hp / max_hp)
        fill_w    = int(width * ratio)
        bar_color = _hp_color(ratio)

        if fill_w > 0:
            pygame.draw.rect(screen, bar_color,
                             (x, y, fill_w, height), border_radius=4)

        if incoming_dmg > 0:
            dmg_after_shield = max(0, incoming_dmg - shield)
            if dmg_after_shield > 0:
                proj_ratio = min(dmg_after_shield / max_hp, ratio)
                proj_w     = int(width * proj_ratio)
                proj_x     = x + fill_w - proj_w
                if proj_w > 0:
                    pygame.draw.rect(screen, _HP_PROJ,
                                     (proj_x, y, proj_w, height), border_radius=4)

        if shield > 0:
            shld_ratio = min(shield / max_hp, 1.0)
            shld_w     = int(width * shld_ratio)
            pygame.draw.rect(screen, _HP_SHIELD,
                             (x, y, shld_w, max(4, height // 4)), border_radius=2)

        pygame.draw.rect(screen, (100, 100, 120),
                         (x, y, width, height), 1, border_radius=4)

    # ── РОМБЫ ЭНЕРГИИ ───────────────────────────────────────────────────────
    @staticmethod
    def draw_energy_diamonds(screen, x, y, current, maximum, size=18):
        gap = size * 2 + 8
        for i in range(maximum):
            cx = x + i * gap + size
            cy = y + size
            pts = [(cx, cy - size), (cx + size, cy),
                   (cx, cy + size),  (cx - size, cy)]
            filled = i < current
            pygame.draw.polygon(screen, _ENERGY_ON if filled else _ENERGY_OFF, pts)
            pygame.draw.polygon(screen, _ENERGY_BRD, pts, 2)

    # ── БЕЙДЖИ СТАТУСОВ ─────────────────────────────────────────────────────
    @staticmethod
    def draw_status_badges(screen, font, creature, x, y):
        badge_rects = []
        cursor_x    = x
        pad_x, pad_y = 8, 4
        badge_h      = font.get_linesize() + pad_y * 2

        for key, data in STATUSES.items():
            val = getattr(creature, key, 0)
            if val <= 0:
                continue

            label     = f"{data['abbr']} {val}"
            text_surf = font.render(label, True, data["badge_fg"])
            badge_w   = text_surf.get_width() + pad_x * 2

            rect = pygame.Rect(cursor_x, y, badge_w, badge_h)
            pygame.draw.rect(screen, data["badge_bg"], rect, border_radius=5)
            pygame.draw.rect(screen, (255, 255, 255), rect, 1, border_radius=5)
            screen.blit(text_surf, (cursor_x + pad_x, y + pad_y))

            badge_rects.append((rect, key, val))
            cursor_x += badge_w + 6

        return badge_rects

    # ── РЕЛИКВИИ: КОМПАКТНЫЕ БЕЙДЖИ ──────────────────────────────────────────
    @staticmethod
    def draw_relics(screen, relics, x, y, max_x=None):
        """Раскладывает реликвии компактными бейджами слева направо.
        Если max_x задан и бейджи не влезают — рисует сколько помещается (минус место
        под слот «+N») и возвращает число скрытых. Возврат: (relic_rects, hidden_count)."""
        relic_rects = []
        step        = _RELIC_BADGE + _RELIC_GAP
        total       = len(relics)

        visible = total
        if max_x is not None:
            fit = max(0, (max_x - x) // step)
            if fit < total:
                visible = max(0, fit - 1)   # оставить место под «+N»

        for i, relic in enumerate(relics[:visible]):
            rect = pygame.Rect(x + i * step, y, _RELIC_BADGE, _RELIC_BADGE)
            CombatHUD.draw_relic_badge(screen, relic, rect)
            relic_rects.append((rect, relic))

        return relic_rects, total - visible

    @staticmethod
    def draw_relic_badge(screen, relic, rect):
        """Один квадратный бейдж: заливка/рамка по редкости, аббревиатура, маркер активной."""
        is_active = getattr(relic, 'is_active', False)
        used      = getattr(relic, '_used', False)
        rarity_c  = RARITY_COLORS.get(relic.rarity, (150, 150, 150))
        fill      = tuple(c // 5 + 12 for c in rarity_c)

        pygame.draw.rect(screen, fill, rect, border_radius=6)
        pygame.draw.rect(screen, rarity_c, rect, 2, border_radius=6)

        font = _get_badge_font()
        abbr = _relic_abbr(relic.name)
        ts   = font.render(abbr, True, (235, 235, 235))
        screen.blit(ts, (rect.centerx - ts.get_width() // 2,
                         rect.centery - ts.get_height() // 2))

        # Маркер активной способности (золотая точка; тусклая, если использована)
        if is_active:
            dot = (120, 100, 30) if used else (255, 215, 0)
            pygame.draw.circle(screen, dot, (rect.right - 7, rect.top + 7), 4)
            pygame.draw.circle(screen, (20, 20, 20), (rect.right - 7, rect.top + 7), 4, 1)

    # ── СЛОТ АКТИВНОЙ СПОСОБНОСТИ ───────────────────────────────────────────
    @staticmethod
    def draw_ability_slot(screen, font, ability, x, y) -> pygame.Rect:
        """
        Рисует кнопку активной способности класса.
        Возвращает Rect для обработки кликов в InputHandler.
        """
        ready = ability.is_ready()
        used  = getattr(ability, '_used', False)

        pad_x, pad_y = 12, 6
        label     = f"[СПОСОБНОСТЬ] {ability.name}"
        text_surf = font.render(label, True,
                                (255, 220, 60) if ready else (100, 100, 100))
        btn_w = text_surf.get_width() + pad_x * 2
        btn_h = text_surf.get_height() + pad_y * 2
        rect  = pygame.Rect(x, y, btn_w, btn_h)

        bg_color     = (40, 60, 40) if ready else (30, 30, 30)
        border_color = (80, 200, 80) if ready else (60, 60, 60)

        if ready and rect.collidepoint(pygame.mouse.get_pos()):
            bg_color     = (60, 90, 60)
            border_color = (120, 255, 120)

        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)
        screen.blit(text_surf, (x + pad_x, y + pad_y))

        status_text  = "готова" if ready else ("использована" if used else "не готова")
        status_color = (80, 200, 80) if ready else (120, 120, 120)
        status_surf  = font.render(status_text, True, status_color)
        screen.blit(status_surf, (x + pad_x, y + btn_h + 4))

        return rect

    # ── ТУЛТИП СТАТУСА ──────────────────────────────────────────────────────
    @staticmethod
    def draw_status_tooltip(screen, font_desc, status_key, status_val, mouse_pos):
        data = STATUSES.get(status_key)
        if not data:
            return
        raw_text = data["tooltip"].replace("N", str(status_val))
        lines    = raw_text.split("\n")
        CombatHUD._draw_tooltip(screen, font_desc, lines, mouse_pos,
                                border=(200, 200, 200))

    # ── ТУЛТИП РЕЛИКВИИ ─────────────────────────────────────────────────────
    @staticmethod
    def draw_relic_tooltip(screen, font, relic, mouse_pos):
        lines        = relic.description.split("\n")
        border_color = RARITY_COLORS.get(relic.rarity, (150, 150, 150))
        CombatHUD._draw_tooltip(screen, font, lines, mouse_pos,
                                title=relic.name, border=border_color)
    # ── ТУЛТИП АКТИВНОЙ СПОСОБНОСТИ ─────────────────────────────────────────
    @staticmethod
    def draw_ability_tooltip(screen, font, ability, mouse_pos):
        lines        = ability.description.split("\n")
        border_color = (80, 200, 80) if ability.is_ready() else (80, 80, 80)
        CombatHUD._draw_tooltip(screen, font, lines, mouse_pos,
                                title=ability.name, border=border_color)

    # ── ТУЛТИП СТОПКИ ───────────────────────────────────────────────────────
    @staticmethod
    def draw_pile_tooltip(screen, font_title, font_desc, cards, title, mouse_pos):
        lines = [f"  {c.name}" for c in cards] if cards else ["(пусто)"]
        CombatHUD._draw_tooltip(screen, font_desc, lines, mouse_pos,
                                title=title, title_font=font_title,
                                border=(180, 180, 180), above_cursor=True)

    # ── ВНУТРЕННИЙ ХЕЛПЕР ТУЛТИПА ───────────────────────────────────────────
    @staticmethod
    def _draw_tooltip(screen, font, lines, mouse_pos,
                      title=None, title_font=None,
                      border=(200, 200, 200), above_cursor=False):
        tf           = title_font or font
        pad_x, pad_y = 12, 8
        line_h       = font.get_linesize() + 2
        title_h      = (tf.get_linesize() + 6) if title else 0

        max_w = max((font.size(line)[0] for line in lines), default=60)
        if title:
            max_w = max(max_w, tf.size(title)[0])
        box_w = max_w + pad_x * 2
        box_h = title_h + len(lines) * line_h + pad_y * 2

        tip_x = mouse_pos[0] + 16
        tip_y = (mouse_pos[1] - box_h - 10) if above_cursor \
                else (mouse_pos[1] + 16)

        sw, sh = screen.get_size()
        if tip_x + box_w > sw - 10:
            tip_x = mouse_pos[0] - box_w - 10
        if tip_y < 10:
            tip_y = mouse_pos[1] + 16
        if tip_y + box_h > sh - 10:
            tip_y = sh - box_h - 10

        bg = pygame.Rect(tip_x, tip_y, box_w, box_h)
        pygame.draw.rect(screen, (18, 18, 28), bg, border_radius=6)
        pygame.draw.rect(screen, border, bg, 1, border_radius=6)

        oy = tip_y + pad_y
        if title:
            ts = tf.render(title, True, border)
            screen.blit(ts, (tip_x + pad_x, oy))
            oy += title_h

        for line in lines:
            screen.blit(font.render(line, True, (210, 210, 210)),
                        (tip_x + pad_x, oy))
            oy += line_h

    # ── ЦВЕТ УРОНА НАМЕРЕНИЯ ────────────────────────────────────────────────
    @staticmethod
    def get_intent_damage_color(predicted_dmg, player_shield):
        if predicted_dmg > player_shield:
            return (255, 80, 80)
        return (80, 160, 255)