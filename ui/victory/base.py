# ui/victory/base.py
# Экран наград после победы: состояние, оркестрация отрисовки, обработка кликов.
import pygame
from ui.combat.hud import CombatHUD
from ui.victory.data import _BG
from ui.victory import rewards_view, modal


class VictoryScreen:
    """Статический класс — экран наград после победы в бою."""

    _claim_rects    = []
    _claim_all_rect = None
    _continue_rect  = None

    # Для тултипа реликвии: (rect, relic) или None
    _hovered_relic  = None

    _show_modal = False
    _modal_yes  = None
    _modal_no   = None

    @classmethod
    def draw_screen(cls, view):
        screen = view.screen
        W, H   = screen.get_size()
        mouse  = pygame.mouse.get_pos()

        screen.fill(_BG)

        fonts = {
            "title": view.main_font,
            "body":  view.card_font,
            "small": view.card_desc_font,
        }

        rewards_view.draw_rewards(cls, view, screen, fonts, mouse)

        # Модальное окно поверх всего
        if cls._show_modal:
            modal.draw_modal(cls, screen, W, H, fonts["body"], fonts["small"], mouse)

        # Тултип реликвии -- самым последним, поверх всего
        if cls._hovered_relic and not cls._show_modal:
            _, relic = cls._hovered_relic
            CombatHUD.draw_relic_tooltip(screen, fonts["small"], relic, mouse)

    @classmethod
    def handle_clicks(cls, view, mouse_pos):
        if cls._show_modal:
            if cls._modal_yes and cls._modal_yes.collidepoint(mouse_pos):
                cls._show_modal = False
                cls._proceed(view)
            elif cls._modal_no and cls._modal_no.collidepoint(mouse_pos):
                cls._show_modal = False
            return

        rewards = view.gm.pending_rewards

        for rect, idx in cls._claim_rects:
            if rect.collidepoint(mouse_pos) and not rewards[idx]["applied"]:
                cls._apply_reward(view.gm, rewards[idx])
                return

        if cls._claim_all_rect and cls._claim_all_rect.collidepoint(mouse_pos):
            for reward in rewards:
                if not reward["applied"]:
                    cls._apply_reward(view.gm, reward)
            return

        if cls._continue_rect and cls._continue_rect.collidepoint(mouse_pos):
            has_unclaimed = any(not r["applied"] for r in rewards)
            if has_unclaimed:
                cls._show_modal = True
            else:
                cls._proceed(view)

    @staticmethod
    def _apply_reward(gm, reward):
        if reward["type"] == "gold":
            gm.player_gold += reward["value"]
        elif reward["type"] == "relic":
            gm.relics.append(reward["value"])
        elif reward["type"] == "key":
            gm.player_keys += reward["value"]
        reward["applied"] = True

    @staticmethod
    def _proceed(view):
        VictoryScreen._show_modal      = False
        view.gm.pending_rewards        = []
        view.gm.current_floor         += 1
        view.scroll_y                  = 0
        view.gm.setup_next_floor()
