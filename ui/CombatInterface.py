import pygame
from core.EffectCalculator import EffectCalculator
from ui.combat.hud import CombatHUD


class CombatInterface:
    """Оркестратор отрисовки боевого экрана под разрешение 1920x1080."""

    @staticmethod
    def draw_combat_screen(view):
        view.screen.fill((30, 30, 30))
        WHITE  = (255, 255, 255)
        RED    = (240, 70,  70)
        GREEN  = (70,  240, 70)
        BLUE   = (70,  160, 240)
        YELLOW = (240, 240, 70)
        GRAY   = (150, 150, 150)

        combat = view.gm.active_combat
        enemy  = combat.enemy
        player = combat.player
        dm     = combat.deck_manager

        # --- РЕЛИКВИИ ---
        view.draw_text("АРТЕФАКТЫ:", view.card_font, YELLOW, 100, 20)
        if hasattr(view.gm, 'relics'):
            for r_idx, relic in enumerate(view.gm.relics):
                view.draw_text(
                    f"[{relic.name}]", view.card_desc_font, WHITE,
                    250 + r_idx * 180, 23
                )

        # 1. ИНТЕРФЕЙС ВРАГА
        view.draw_text(f"ВРАГ: {enemy.name}", view.main_font, WHITE, 100, 70)
        if enemy.hp > 0:
            CombatHUD.draw_hp_bar(
                view.screen, 100, 120, 500, 25,
                enemy.hp, enemy.max_hp, enemy.shield
            )
            shield_str = f" (+{enemy.shield} Щит)" if enemy.shield > 0 else ""
            view.draw_text(
                f"HP: {enemy.hp}/{enemy.max_hp}{shield_str}",
                view.card_font, RED, 100, 155
            )

            if enemy.intent_type == "attack" and enemy.intent_value:
                predicted = EffectCalculator.calculate_damage(
                    attacker=enemy, target=player,
                    base_damage=enemy.intent_value, dry_run=True
                )
                dmg_color  = CombatHUD.get_intent_damage_color(predicted, player.shield)
                label      = "НАМЕРЕНИЕ: АТАКА на "
                label_surf = view.main_font.render(label, True, YELLOW)
                view.screen.blit(label_surf, (100, 195))
                dmg_surf = view.main_font.render(str(predicted), True, dmg_color)
                view.screen.blit(dmg_surf, (100 + label_surf.get_width(), 195))
            elif enemy.intent_type:
                view.draw_text(
                    f"НАМЕРЕНИЕ: {enemy.intent_type.upper()} на {enemy.intent_value}",
                    view.main_font, YELLOW, 100, 195
                )

            view.enemy_badge_rects = CombatHUD.draw_status_badges(
                view.screen, view.card_desc_font, enemy, 100, 240
            )
        else:
            view.draw_text(
                " [!!!] ВРАГ ПОВЕРЖЕН! КЛИКНИТЕ ДЛЯ СЛЕДУЮЩЕГО ЭТАЖА [!!!]",
                view.main_font, GREEN, 100, 120
            )
            view.enemy_badge_rects = []

        view.draw_text("-" * 120, view.ui_font, GRAY, 100, 290)

        # 2. ИНТЕРФЕЙС ИГРОКА
        view.draw_text("ИГРОК: Вы", view.main_font, WHITE, 100, 330)
        CombatHUD.draw_hp_bar(
            view.screen, 100, 380, 500, 25,
            player.hp, player.max_hp, player.shield
        )
        player_shield_str = f" (+{player.shield} Щит)" if player.shield > 0 else ""
        view.draw_text(
            f"HP: {player.hp}/{player.max_hp}{player_shield_str}",
            view.card_font, GREEN, 100, 415
        )

        view.draw_text("Энергия: ", view.main_font, BLUE, 100, 460)
        for i in range(player.max_energy):
            sphere_x = 270 + i * 45
            sphere_y = 480
            if i < player.energy:
                pygame.draw.circle(view.screen, BLUE, (sphere_x, sphere_y), 15)
            else:
                pygame.draw.circle(
                    view.screen, (50, 50, 60), (sphere_x, sphere_y), 15, 2
                )

        view.draw_text(
            f"Золото: {view.gm.player_gold} монет",
            view.main_font, YELLOW, 450, 460
        )

        view.player_badge_rects = CombatHUD.draw_status_badges(
            view.screen, view.card_desc_font, player, 100, 510
        )

        view.draw_text("=" * 100, view.ui_font, WHITE, 100, 570)

        # 3. ДИНАМИЧЕСКИЙ ВЕЕР КАРТ
        hand_size = len(dm.hand)
        view.draw_text(
            f"Колода: {len(dm.draw_pile)} шт.", view.main_font, YELLOW, 100, 600
        )
        view.draw_text(
            f"Сброс: {len(dm.discard_pile)} шт.", view.main_font, GRAY, 1600, 600
        )

        for index, card in enumerate(dm.hand):
            card_x = view.calculate_card_x(index, hand_size)
            card_y = view.base_y
            if index == view.hovered_card_index:
                card_y = view.base_y - 40
            view.draw_card_by_data(card, card_x, card_y, enemy=enemy, player=player)

        # 4. КНОПКА КОНЦА ХОДА
        btn_color = (90, 90, 95) if view.is_end_turn_hovered else (60, 60, 60)
        pygame.draw.rect(view.screen, btn_color, view.end_turn_rect)
        pygame.draw.rect(view.screen, WHITE, view.end_turn_rect, 2)
        view.draw_text(
            "КОНЕЦ ХОДА", view.card_font, WHITE,
            view.end_turn_rect.x + 45, view.end_turn_rect.y + 18
        )

        # 5. БОЕВОЙ ЛОГ
        log_x, log_y = 1400, 70
        log_rect = pygame.Rect(log_x - 15, log_y - 15, 420, 220)
        pygame.draw.rect(view.screen, (20, 20, 20), log_rect)
        pygame.draw.rect(view.screen, GRAY, log_rect, 1)
        view.draw_text("ИСТОРИЯ ДЕЙСТВИЙ:", view.card_font, YELLOW, log_x, log_y)
        for log_index, message in enumerate(combat.combat_log):
            view.draw_text(
                message, view.card_desc_font, WHITE,
                log_x, log_y + 35 + log_index * 26
            )

        # 6. ТУЛТИП СТАТУСА -- рисуется ПОСЛЕДНИМ, поверх всего
        hovered_key = getattr(view, 'hovered_status_key', None)
        hovered_val = getattr(view, 'hovered_status_val', 0)
        if hovered_key:
            mouse_pos = pygame.mouse.get_pos()
            CombatHUD.draw_status_tooltip(
                view.screen, view.card_desc_font,
                hovered_key, hovered_val, mouse_pos
            )