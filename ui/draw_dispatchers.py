# ui/draw_dispatchers.py
# Диспетчер отрисовки: состояние gm.current_state -> функция отрисовки экрана.
# Добавить новый экран = один импорт + одна обёртка + одна строка в DRAW_HANDLERS.
from ui.MainMenu import MainMenu
from ui.MapView import MapView
from ui.Campfire import Campfire
from ui.shop import Shop
from ui.LeaderboardView import LeaderboardView
from ui.chest import Chest
from ui.victory import VictoryScreen
from ui.library import CardLibraryView
from ui.combat import CombatInterface
from ui.cards import CardRenderer


def _draw_main_menu(view):    MainMenu.draw_menu(view)
def _draw_hub(view):          MainMenu.draw_hub(view)
def _draw_map(view):          MapView.draw_map(view)
def _draw_campfire(view):     Campfire.draw_screen(view)
def _draw_shop(view):         Shop.draw_screen(view)
def _draw_leaderboard(view):  LeaderboardView.draw_screen(view)
def _draw_chest(view):        Chest.draw_screen(view)
def _draw_card_library(view): CardLibraryView.draw_screen(view)


def _draw_victory(view):
    # Награды — модальный ОВЕРЛЕЙ поверх боя: рисуем боевой экран на фоне, затем
    # затемнение + панель наград (бой виден сквозь полупрозрачную заглушку).
    CombatInterface.draw_combat_screen(view)
    VictoryScreen.draw_screen(view)


def _draw_event(view):
    from ui.EventView import draw_screen as draw_event
    draw_event(view)


def _draw_combat(view):
    CombatInterface.draw_combat_screen(view)
    if view.hover.card_obj and view.hover.card_rect:
        # Разбор урона для тултипа наведённой карты (база→модификаторы→итог).
        damage_steps = None
        combat = view.gm.active_combat
        card = view.hover.card_obj
        base = CardRenderer._card_base_damage(card) if card else None
        target = combat.get_target_enemy() if combat else None
        if combat and target and base:
            from core.EffectCalculator import EffectCalculator
            pv = EffectCalculator.preview(
                combat.player, target, base, combat_manager=combat,
                game_manager=view.gm, card=card)
            damage_steps = pv["steps"]
        CardRenderer.draw_card_keyword_tooltip(
            view.screen,
            view.card_font,
            view.card_desc_font,
            view.hover.card_obj,
            view.hover.card_rect,
            damage_steps,
            player=combat.player if combat else None,
        )


DRAW_HANDLERS = {
    "MAIN_MENU":    _draw_main_menu,
    "HUB":          _draw_hub,
    "MAP":          _draw_map,
    "COMBAT":       _draw_combat,
    "CAMPFIRE":     _draw_campfire,
    "SHOP":         _draw_shop,
    "LEADERBOARD":  _draw_leaderboard,
    "CHEST":        _draw_chest,
    "EVENT":        _draw_event,
    "VICTORY":      _draw_victory,
    "CARD_LIBRARY": _draw_card_library,
}
