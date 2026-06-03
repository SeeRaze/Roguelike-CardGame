import pygame
from core.EffectCalculator import EffectCalculator
from ui.combat.hud import CombatHUD

# ── Палитра ──────────────────────────────────────────────────────────────────
_BG           = (12, 12, 22)
_PANEL_BG     = (22, 22, 40)
_PANEL_BORDER = (160, 160, 255)
_GOLD         = (255, 220, 60)
_WHITE        = (220, 220, 220)
_RED          = (220, 80, 80)
_GREEN        = (80, 210, 100)
_BLUE         = (100, 180, 255)
_GRAY         = (120, 120, 140)
_INTENT_OTHER = (180, 180, 255)

# ── Геометрия (1920×1080) ────────────────────────────────────────────────────
_SW, _SH      = 1920, 1080
_PANEL_W      = 560
_PANEL_MARGIN = 30          # отступ от края экрана
_PANEL_TOP    = 70          # верх панелей (под рelic-баром)
_INNER_PAD    = 25          # отступ текста внутри панели

# Левая панель (игрок)
_P_PX  = _PANEL_MARGIN                          # 30
_P_IX  = _P_PX + _INNER_PAD                     # 55

# Правая панель (враг) -- зеркально
_E_PX  = _SW - _PANEL_MARGIN - _PANEL_W         # 1330
_E_IX  = _E_PX + _INNER_PAD                     # 1355
_E_IW  = _PANEL_W - _INNER_PAD * 2              # 510  (ширина контента)


class CombatInterface:
    """Оркестратор отрисовки боевого экрана. 1920×1080."""

    # ── ГЛАВНЫЙ МЕТОД ─────────────────────────────────────────────────────────
    @staticmethod
    def draw_combat_screen(view):
        screen = view.screen
        screen.fill(_BG)

        combat = view.gm.active_combat
        enemy  = combat.enemy
        player = combat.player
        dm     = combat.deck_manager

        # Проекция урона: намерение врага → на HP-бар игрока
        intent_dmg = 0
        if enemy.intent_type == "attack" and enemy.intent_value:
            intent_dmg = EffectCalculator.calculate_damage(
                attacker=enemy, target=player,
                base_damage=enemy.intent_value, dry_run=True
            )

        # Проекция урона: hover-карта → на HP-бар врага
        hover_dmg = 0
        if view.hover.card_obj:
            hover_dmg = EffectCalculator.calculate_damage(
                attacker=player, target=enemy,
                base_damage=getattr(view.hover.card_obj, 'damage', 0),
                dry_run=True
            )

        CombatInterface._draw_relic_bar(view, screen)
        CombatInterface._draw_player_panel(view, screen, player, intent_dmg)
        CombatInterface._draw_enemy_panel(view, screen, enemy, player,
                                          intent_dmg, hover_dmg)
        CombatInterface._draw_combat_log(view, screen, combat)
        CombatInterface._draw_hand(view, screen, dm, enemy, player)
        CombatInterface._draw_piles(view, screen, dm)
        CombatInterface._draw_end_turn_btn(view, screen)

        # Тултипы -- поверх всего
        mp = pygame.mouse.get_pos()
        if view.hover.status_key:
            CombatHUD.draw_status_tooltip(
                screen, view.card_desc_font,
                view.hover.status_key, view.hover.status_val, mp
            )
        if view.hover.relic_obj:
            CombatHUD.draw_relic_tooltip(
                screen, view.card_desc_font,
                view.hover.relic_obj, mp
            )
        if view.hover.pile_type:
            if view.hover.pile_type == "draw":
                cards = (view._draw_pile_display
                         if not getattr(view.gm, 'reveal_draw_order', False)
                         else dm.draw_pile.copy())
                title = f"ДОБОР ({len(dm.draw_pile)})"
            else:
                cards = list(reversed(dm.discard_pile))
                title = f"СБРОС ({len(dm.discard_pile)})"
            CombatHUD.draw_pile_tooltip(
                screen, view.card_font, view.card_desc_font,
                cards, title, mp
            )

    # ── ПОЛОСА РЕЛИКВИЙ ───────────────────────────────────────────────────────
    @staticmethod
    def _draw_relic_bar(view, screen):
        bar = pygame.Rect(0, 0, _SW, 52)
        pygame.draw.rect(screen, _PANEL_BG, bar)
        pygame.draw.rect(screen, _PANEL_BORDER, bar, 1)

        lbl = view.card_desc_font.render("АРТЕФАКТЫ:", True, _GOLD)
        screen.blit(lbl, (18, 16))

        if hasattr(view.gm, 'relics'):
            view.relic_rects = CombatHUD.draw_relics(
                screen, view.card_desc_font,
                view.gm.relics, 160, 10
            )
        else:
            view.relic_rects = []

    # ── ЛЕВАЯ ПАНЕЛЬ: ИГРОК ───────────────────────────────────────────────────
    @staticmethod
    def _draw_player_panel(view, screen, player, intent_dmg):
        panel_h = 440
        panel   = pygame.Rect(_P_PX, _PANEL_TOP, _PANEL_W, panel_h)
        pygame.draw.rect(screen, _PANEL_BG, panel, border_radius=12)
        pygame.draw.rect(screen, _PANEL_BORDER, panel, 2, border_radius=12)

        x, y = _P_IX, _PANEL_TOP + 20

        screen.blit(view.main_font.render("ИГРОК", True, _WHITE), (x, y))

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

        y += 42
        screen.blit(view.card_desc_font.render(
            f"Золото: {view.gm.player_gold}", True, _GOLD
        ), (x, y))

        # Статусы
        y += 38
        pygame.draw.line(screen, _PANEL_BORDER, (x, y), (x + _E_IW, y), 1)
        y += 10
        view.player_badge_rects = CombatHUD.draw_status_badges(
            screen, view.card_desc_font, player, x, y
        )

    # ── ПРАВАЯ ПАНЕЛЬ: ВРАГ ───────────────────────────────────────────────────
    @staticmethod
    def _draw_enemy_panel(view, screen, enemy, player, intent_dmg, hover_dmg):
        panel_h = 380
        panel   = pygame.Rect(_E_PX, _PANEL_TOP, _PANEL_W, panel_h)
        pygame.draw.rect(screen, _PANEL_BG, panel, border_radius=12)
        pygame.draw.rect(screen, _PANEL_BORDER, panel, 2, border_radius=12)

        x, y = _E_IX, _PANEL_TOP + 20

        if enemy.hp <= 0:
            screen.blit(view.main_font.render("ВРАГ ПОВЕРЖЕН!", True, _GREEN),
                        (x + 60, y + 130))
            screen.blit(view.card_desc_font.render(
                "Кликните для продолжения", True, _GRAY), (x + 40, y + 175))
            view.enemy_badge_rects = []
            return

        screen.blit(view.main_font.render(
            f"ВРАГ: {enemy.name}", True, _WHITE), (x, y))

        y += 44
        CombatHUD.draw_hp_bar(
            screen, x, y, _E_IW, 26,
            enemy.hp, enemy.max_hp, enemy.shield,
            incoming_dmg=hover_dmg
        )
        y += 32
        shld_str = f"  +{enemy.shield} щит" if enemy.shield > 0 else ""
        screen.blit(view.card_desc_font.render(
            f"HP: {enemy.hp} / {enemy.max_hp}{shld_str}", True, _RED
        ), (x, y))

        y += 44
        pygame.draw.line(screen, _PANEL_BORDER, (x, y - 6), (x + _E_IW, y - 6), 1)
        if enemy.intent_type == "attack" and intent_dmg:
            dmg_color = CombatHUD.get_intent_damage_color(intent_dmg, player.shield)
            lbl = view.card_desc_font.render("Намерение: атака на ", True, _GOLD)
            screen.blit(lbl, (x, y))
            screen.blit(view.card_desc_font.render(
                str(intent_dmg), True, dmg_color), (x + lbl.get_width(), y))
        elif enemy.intent_type:
            screen.blit(view.card_desc_font.render(
                f"Намерение: {enemy.intent_type} {enemy.intent_value or ''}",
                True, _INTENT_OTHER), (x, y))
        else:
            screen.blit(view.card_desc_font.render(
                "Намерение: —", True, _GRAY), (x, y))

        # Статусы
        y += 38
        pygame.draw.line(screen, _PANEL_BORDER, (x, y), (x + _E_IW, y), 1)
        y += 10
        view.enemy_badge_rects = CombatHUD.draw_status_badges(
            screen, view.card_desc_font, enemy, x, y
        )

    # ── БОЕВОЙ ЛОГ ────────────────────────────────────────────────────────────
    @staticmethod
    def _draw_combat_log(view, screen, combat):
        log_top = _PANEL_TOP + 400          # под панелью врага (380 + 20 зазор)
        log     = pygame.Rect(_E_PX, log_top, _PANEL_W, 260)
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

    # ── РУКА (КАРТЫ) ──────────────────────────────────────────────────────────
    @staticmethod
    def _draw_hand(view, screen, dm, enemy, player):
        hand_size = len(dm.hand)
        for index, card in enumerate(dm.hand):
            card_x = view.calculate_card_x(index, hand_size)
            card_y = (view.base_y - 40
                      if index == view.hover.card_index
                      else view.base_y)
            view.draw_card_by_data(card, card_x, card_y,
                                   enemy=enemy, player=player)

    # ── СТОПКИ ────────────────────────────────────────────────────────────────
    @staticmethod
    def _draw_piles(view, screen, dm):
        CombatInterface._draw_pile(
            screen, view.card_font, view.card_desc_font,
            view.draw_pile_rect, len(dm.draw_pile), "ДОБОР", _BLUE
        )
        CombatInterface._draw_pile(
            screen, view.card_font, view.card_desc_font,
            view.discard_pile_rect, len(dm.discard_pile), "СБРОС", _GRAY
        )

    @staticmethod
    def _draw_pile(screen, font_title, font_desc, rect, count, label, color):
        pygame.draw.rect(screen, (28, 28, 48), rect, border_radius=8)
        pygame.draw.rect(screen, color, rect, 2, border_radius=8)

        inner = rect.inflate(-12, -12)
        pygame.draw.rect(screen, (38, 38, 60), inner, border_radius=4)
        for i in range(inner.left + 8, inner.right, 16):
            pygame.draw.line(screen, (48, 48, 72),
                             (i, inner.top), (i, inner.bottom))
        for j in range(inner.top + 8, inner.bottom, 16):
            pygame.draw.line(screen, (48, 48, 72),
                             (inner.left, j), (inner.right, j))

        count_surf = font_title.render(str(count), True, (230, 230, 230))
        screen.blit(count_surf, (
            rect.centerx - count_surf.get_width() // 2,
            rect.centery - count_surf.get_height() // 2
        ))
        label_surf = font_desc.render(label, True, color)
        screen.blit(label_surf, (
            rect.centerx - label_surf.get_width() // 2,
            rect.bottom + 6
        ))

    # ── КНОПКА КОНЦА ХОДА ─────────────────────────────────────────────────────
    @staticmethod
    def _draw_end_turn_btn(view, screen):
        dr    = view.discard_pile_rect
        btn_w = 220
        btn_h = 52
        btn   = pygame.Rect(dr.right - btn_w, dr.top - btn_h - 12, btn_w, btn_h)
        view.end_turn_rect = btn

        # Hover считаем напрямую -- не зависим от InputHandler
        hover        = btn.collidepoint(pygame.mouse.get_pos())
        bg           = (70, 70, 120) if hover else (40, 40, 75)
        border_color = (200, 200, 255) if hover else _PANEL_BORDER

        pygame.draw.rect(screen, bg, btn, border_radius=12)
        pygame.draw.rect(screen, border_color, btn, 2, border_radius=12)

        if hover:
            glow = btn.inflate(-4, -4)
            pygame.draw.rect(screen, (100, 100, 180), glow, 1, border_radius=10)

        lbl = view.card_desc_font.render("КОНЕЦ ХОДА", True,
                                         (255, 255, 255) if hover else _WHITE)
        screen.blit(lbl, (
            btn.centerx - lbl.get_width() // 2,
            btn.centery - lbl.get_height() // 2
        ))