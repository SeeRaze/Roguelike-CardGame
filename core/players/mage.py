from core.players.base import Player
from core.cards import create_strike, create_defend, create_ignite, create_splash


def get_mage_deck():
    return [
        create_strike(), create_strike(),
        create_defend(), create_defend(), create_defend(),
        create_ignite(),   # Огонь
        create_splash(),   # Вода для комбо
    ]


class Mage(Player):
    def __init__(self):
        super().__init__(
            name="Маг",
            max_hp=55,
            max_energy=3,
            gold=90,
            starter_deck_factory=get_mage_deck,
        )

    # ------------------------------------------------------------------
    # Пассивка «Стихийный резонанс»
    # При триггере комбо «Пар» — добрать 1 карту из колоды.
    # EffectCalculator выставляет флаг _steam_combo_triggered на combat_manager.
    # ------------------------------------------------------------------
    def on_card_played_passive(self, card, combat_manager) -> None:
        if not combat_manager:
            return
        if getattr(combat_manager, '_steam_combo_triggered', False):
            combat_manager._steam_combo_triggered = False
            drawn = combat_manager.deck_manager.draw_cards(1)
            if drawn > 0:
                combat_manager.add_log_message(
                    " [МАГ] Стихийный резонанс: +1 карта из колоды!"
                )