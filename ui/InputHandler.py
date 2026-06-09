import pygame
from ui.chest import Chest
from ui.shop import Shop
from ui.Campfire import Campfire
from ui.combat.targeting import TargetingSystem


def _check_relic_panel(view, mouse_pos) -> bool:
    """Общий хелпер: открытая RelicPanel перехватывает клики; клик по кнопке
    «АРТЕФАКТЫ (N)» (resource_hud) открывает панель. Возвращает True, если
    клик поглощён и дальнейшая обработка не нужна."""
    from ui.combat.relic_panel import RelicPanel

    if RelicPanel.is_open(view):
        RelicPanel.handle_click(view, mouse_pos)
        return True

    btn = getattr(view, 'hud_relic_btn_rect', None)
    if btn and btn.collidepoint(mouse_pos):
        RelicPanel.open(view)
        return True
    return False


def _handle_combat(view, mouse_pos):
    from ui.combat.relic_panel import RelicPanel

    # Открытая панель реликвий перехватывает все клики
    if RelicPanel.is_open(view):
        RelicPanel.handle_click(view, mouse_pos)
        return

    if all(e.hp <= 0 for e in view.gm.active_combat.enemies):
        if view.gm.current_state == "COMBAT":
            view.gm.distribute_combat_rewards()
        return

    # Открыть панель: клик по метке «АРТЕФАКТЫ» или слоту «+N»
    btn = getattr(view, 'relic_panel_btn_rect', None)
    ov  = getattr(view, 'relic_overflow_rect', None)
    if (btn and btn.collidepoint(mouse_pos)) or (ov and ov.collidepoint(mouse_pos)):
        RelicPanel.open(view)
        return

    # Клик по вражеской панели — выбор цели
    if TargetingSystem.handle_target_click(view, mouse_pos):
        return

    # Клик по активной реликвии (бейдж на полосе)
    for rect, relic in getattr(view, 'relic_rects', []):
        if rect.collidepoint(mouse_pos):
            if getattr(relic, 'is_active', False):
                relic.activate(view.gm.active_combat)
            return

    # Клик по слоту активной способности класса
    ability_rect = getattr(view, 'ability_rect', None)
    if ability_rect and ability_rect.collidepoint(mouse_pos):
        ability = getattr(view.gm.active_combat.player, 'active_ability', None)
        if ability and ability.is_ready():
            ability.activate(view.gm.active_combat)
            # Способность может убить игрока в свой ход (Берсерк бьёт себя)
            view.gm.active_combat.check_player_defeat()
            # Способность могла добить врага → обработать смерть (on_kill/статы/
            # перенос стаи) в момент килла, как и розыгрыш карты.
            view.gm.active_combat._process_enemy_deaths()
            # ...или добить последнего врага → немедленный переход в награды.
            view.gm.active_combat._check_victory()
        return

    if view.end_turn_rect.collidepoint(mouse_pos):
        view.gm.active_combat.end_turn_phase()
        return

    hand_size = len(view.gm.active_combat.deck_manager.hand)
    for index in range(hand_size):
        card_x = view.calculate_card_x(index, hand_size)
        card_rect = pygame.Rect(
            card_x, view.base_y, view.card_width, view.card_height
        )
        if card_rect.collidepoint(mouse_pos):
            target = TargetingSystem.get_current_target(view.gm.active_combat)
            view.gm.active_combat.play_card_by_index(index, target=target)
            break


def _handle_campfire(view, mouse_pos):
    if _check_relic_panel(view, mouse_pos):
        return
    Campfire.handle_clicks(view, mouse_pos)


def _handle_shop(view, mouse_pos):
    if _check_relic_panel(view, mouse_pos):
        return
    Shop.handle_clicks(view, mouse_pos)


def _handle_chest(view, mouse_pos):
    if _check_relic_panel(view, mouse_pos):
        return
    Chest.handle_clicks(view, mouse_pos)


def _handle_event(view, mouse_pos):
    if _check_relic_panel(view, mouse_pos):
        return
    from ui.EventView import handle_clicks as event_clicks
    event_clicks(view, mouse_pos)


def _handle_victory(view, mouse_pos):
    from ui.victory import VictoryScreen
    VictoryScreen.handle_clicks(view, mouse_pos)


def _handle_card_library(view, mouse_pos):
    from ui.library import CardLibraryView
    CardLibraryView.handle_click(view, mouse_pos)


def _handle_relic_library(view, mouse_pos):
    from ui.relic_library import RelicLibraryView
    RelicLibraryView.handle_click(view, mouse_pos)


def _handle_leaderboard(view, mouse_pos):
    from ui.LeaderboardView import LeaderboardView
    from ui.MainMenu import MainMenu
    from ui.EventView import reset as event_reset
    from managers.GameManager import GameManager

    if LeaderboardView.handle_clicks(view, mouse_pos):
        Shop.reset()
        Campfire.reset()
        MainMenu.reset()
        event_reset()
        view.gm = GameManager()
        view.gm.current_state = "MAIN_MENU"
        print("[СИСТЕМА] Рестарт завершён. Возврат в главное меню.")


STATE_HANDLERS = {
    "COMBAT":       _handle_combat,
    "CAMPFIRE":     _handle_campfire,
    "SHOP":         _handle_shop,
    "CHEST":        _handle_chest,
    "EVENT":        _handle_event,
    "LEADERBOARD":  _handle_leaderboard,
    "VICTORY":      _handle_victory,
    "CARD_LIBRARY": _handle_card_library,
    "RELIC_LIBRARY": _handle_relic_library,
}


class InputHandler:
    @staticmethod
    def process_mouse_clicks(view, mouse_pos):
        handler = STATE_HANDLERS.get(view.gm.current_state)
        if handler:
            handler(view, mouse_pos)

    @staticmethod
    def process_scroll(view, event_button):
        direction = -1 if event_button == 4 else 1

        # Открытая панель артефактов перехватывает прокрутку (модальна на всех экранах).
        from ui.combat.relic_panel import RelicPanel
        if RelicPanel.is_open(view):
            RelicPanel.scroll(direction)
            return

        state = view.gm.current_state

        if state == "CARD_LIBRARY":
            from ui.library import CardLibraryView
            cards = CardLibraryView._get_cards()
            CardLibraryView.handle_scroll(direction, len(cards))

        elif state == "RELIC_LIBRARY":
            from ui.relic_library import RelicLibraryView
            RelicLibraryView.handle_scroll(direction)

        elif state in ("CAMPFIRE", "SHOP"):
            view.scroll_y = max(0, view.scroll_y + direction * 60)