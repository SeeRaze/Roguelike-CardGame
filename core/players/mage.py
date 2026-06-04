from core.players.base import Player
from core.players.abilities import MageAbility
from core.cards import (
    create_strike, create_defend, create_ignite, create_splash, create_boil,
    create_arcane_focus,
)


def get_mage_deck():
    return [
        create_strike(), create_strike(),
        create_defend(), create_defend(), create_defend(),
        create_ignite(),
        create_splash(),
        create_boil(),            # классовая: энейблер ПАР (Мокрый+Горение разом)
        create_arcane_focus(),    # классовая: движок кат.4 (мастерство стихий)
    ]


class Mage(Player):
    def __init__(self):
        super().__init__(
            name="Маг",
            max_hp=70,
            max_energy=3,
            gold=90,
            starter_deck_factory=get_mage_deck,
        )
        self.active_ability = MageAbility()

    def on_card_played_passive(self, card, combat_manager) -> None:
        if not combat_manager:
            return
        if getattr(combat_manager, '_combo_triggered', False):
            combat_manager._combo_triggered = False
            # Мастерство стихий: каждое комбо усиливает ВСЕ будущие атаки (кат.4).
            self.add_status("mastery", 1, combat_manager)
            drawn = combat_manager.deck_manager.draw_cards(1)
            if drawn > 0:
                combat_manager.add_log_message(
                    " [МАГ] Стихийный резонанс: +1 карта из колоды!"
                )
            healed = self.heal(7, combat_manager)
            if healed > 0:
                combat_manager.add_log_message(
                    f" [МАГ] Стихийный резонанс: +{healed} HP, "
                    f"Мастерство {self.mastery}!"
                )