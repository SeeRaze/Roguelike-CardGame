# ui/combat/interface.py
# Оркестратор отрисовки боевого экрана: проекции урона, панели, рука, тултипы.
import pygame
from core.EffectCalculator import EffectCalculator
from ui.combat.hud import CombatHUD
from ui.combat.layout import _BG
from ui.combat import panels, bottom
from ui.combat.relic_panel import RelicPanel


class CombatInterface:
    """Оркестратор отрисовки боевого экрана. 1920×1080."""

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

        panels.draw_relic_bar(view, screen)
        panels.draw_player_panel(view, screen, player, intent_dmg)
        panels.draw_enemy_panel(view, screen, enemy, player, intent_dmg, hover_dmg)
        panels.draw_combat_log(view, screen, combat)
        bottom.draw_hand(view, screen, dm, enemy, player)
        bottom.draw_piles(view, screen, dm)
        bottom.draw_end_turn_btn(view, screen)

        CombatInterface._draw_tooltips(view, screen, dm)

        # Инвентарь реликвий -- модальный оверлей поверх всего
        if RelicPanel.is_open(view):
            RelicPanel.draw(view, screen)

    @staticmethod
    def _draw_tooltips(view, screen, dm):
        """Тултипы поверх всего: статус, реликвия, способность, стопка."""
        mp = pygame.mouse.get_pos()
        if view.hover.status_key:
            CombatHUD.draw_status_tooltip(
                screen, view.card_desc_font,
                view.hover.status_key, view.hover.status_val, mp
            )
        if view.hover.relic_obj:
            CombatHUD.draw_relic_tooltip(
                screen, view.card_desc_font, view.hover.relic_obj, mp
            )
        # Тултип активной способности
        ability = getattr(view.gm.player, 'active_ability', None)
        if ability and getattr(view, 'ability_rect', None) and \
                view.ability_rect.collidepoint(mp):
            CombatHUD.draw_ability_tooltip(screen, view.card_desc_font, ability, mp)
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
