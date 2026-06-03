# ui/combat/panels.py
# Боковые панели боевого экрана: полоса реликвий, панель игрока, панель врага, лог.
import pygame
from ui.combat.hud import CombatHUD
from ui.combat.layout import (
    _PANEL_BG, _PANEL_BORDER, _GOLD, _WHITE, _RED, _GREEN, _BLUE, _GRAY,
    _INTENT_OTHER, _SW, _PANEL_W, _PANEL_TOP, _P_PX, _P_IX, _E_PX, _E_IX, _E_IW,
)


def draw_relic_bar(view, screen):
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


def draw_player_panel(view, screen, player, intent_dmg):
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


def draw_enemy_panel(view, screen, enemy, player, intent_dmg, hover_dmg):
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


def draw_combat_log(view, screen, combat):
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
