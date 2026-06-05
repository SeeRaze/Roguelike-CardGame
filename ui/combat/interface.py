# ui/combat/interface.py
# Оркестратор отрисовки боевого экрана: проекции урона, панели, рука, тултипы.
import pygame
from core.EffectCalculator import EffectCalculator
from ui.combat.hud import CombatHUD
from ui.combat.layout import _BG
from ui.combat import panels, bottom
from ui.combat.relic_panel import RelicPanel
from ui.combat.targeting import TargetingSystem


class CombatInterface:
    """Оркестратор отрисовки боевого экрана. 1920×1080."""

    @staticmethod
    def draw_combat_screen(view):
        screen = view.screen
        screen.fill(_BG)

        combat = view.gm.active_combat
        enemies = combat.enemies
        player  = combat.player
        dm      = combat.deck_manager

        # Проекция урона: сумма намерений всех атакующих врагов → на HP-бар игрока
        intent_dmg = 0
        for e in enemies:
            if e.hp > 0 and e.intent_type == "attack" and e.intent_value:
                intent_dmg += EffectCalculator.calculate_damage(
                    attacker=e, target=player,
                    base_damage=e.intent_value, dry_run=True
                )

        # Проекция урона наведённой карты на HP-бары врагов (полный урон через
        # единый EffectCalculator.preview): одиночные атаки → текущая цель, AoE →
        # все враги. {враг: урон}.
        projection = {}
        if view.hover.card_obj:
            projection = CombatInterface._card_projection(
                combat, player, view.hover.card_obj)

        panels.draw_relic_bar(view, screen)
        panels.draw_player_panel(view, screen, player, intent_dmg)
        panels.draw_enemy_panels(view, screen, enemies, player, projection)

        # Индикатор выбранной цели
        target_idx = getattr(combat, '_target_index', 0)
        if hasattr(view, 'enemy_panel_rects') and \
                0 <= target_idx < len(view.enemy_panel_rects):
            target_rect = view.enemy_panel_rects[target_idx]
            if enemies[target_idx].hp > 0:
                TargetingSystem.draw_target_indicator(screen, target_rect)

        panels.draw_ally_panels(view, screen, combat.allies)
        panels.draw_combat_log(view, screen, combat)
        bottom.draw_hand(view, screen, dm, enemies, player)
        bottom.draw_piles(view, screen, dm)
        bottom.draw_end_turn_btn(view, screen)

        CombatInterface._draw_tooltips(view, screen, dm)

        # Инвентарь реликвий -- модальный оверлей поверх всего
        if RelicPanel.is_open(view):
            RelicPanel.draw(view, screen)

    @staticmethod
    def _card_projection(combat, player, card):
        """{враг: полный_урон наведённой карты} для проекции на HP-барах. Прямой
        урон (DamageEffect, мульти-хит складываем) → текущая цель; AoE-Возмездие
        (ShieldDamageEffect, база = щит×ratio) → все живые враги. Полный урон
        (с комбо/ковкой) = что реально снимется, через единый EffectCalculator."""
        from core.cards.base import DamageEffect
        from core.cards.warrior import ShieldDamageEffect
        proj = {}
        if card is None:
            return proj
        gm = combat.gm

        dmg_base = sum(
            (e.upgrade_val if card.upgraded else e.base_val)
            for e in card.effects if isinstance(e, DamageEffect)
        )
        if dmg_base > 0:
            target = combat.get_target_enemy()
            if target is not None:
                proj[target] = EffectCalculator.preview(
                    player, target, dmg_base, combat_manager=combat,
                    game_manager=gm, card=card)["full"]

        for eff in card.effects:
            if isinstance(eff, ShieldDamageEffect):
                ratio = eff.upgrade_ratio if card.upgraded else eff.base_ratio
                base = int(getattr(player, "shield", 0) * ratio)
                if base > 0:
                    for e in combat.enemies:
                        if e.hp > 0:
                            d = EffectCalculator.preview(
                                player, e, base, combat_manager=combat,
                                game_manager=gm, card=card)["full"]
                            proj[e] = proj.get(e, 0) + d
        return proj

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
