from core.players.base import Player
from core.players.abilities import RogueAbility
from core.cards import (
    create_strike, create_defend,
    create_neutralize, create_lacerate,
    create_open_wound, create_bloodlust,
)


def get_rogue_deck():
    return [
        create_strike(), create_strike(), create_strike(),
        create_defend(), create_defend(),
        create_neutralize(),
        create_lacerate(),
        create_open_wound(),
        create_bloodlust(),     # классовая: движок кат.4 (Кровожадность)
    ]


class Rogue(Player):
    def __init__(self):
        super().__init__(
            name="Разбойник",
            max_hp=40,
            max_energy=3,
            gold=120,
            starter_deck_factory=get_rogue_deck,
        )
        self.active_ability = RogueAbility()

    def on_card_played_passive(self, card, combat_manager) -> None:
        # «Кровожадность»: каждая сыгранная АТАКА растит frenzy на 1 (кат.4 движок).
        # frenzy усиливает все будущие наложения Кровотечения (BleedEffect),
        # превращая темп атак в нарастающий dot-урон.
        if card is None or not combat_manager:
            return
        if card.card_type == "attack":
            self.add_status("frenzy", 1, combat_manager)
            combat_manager.add_log_message(
                f" [РАЗБОЙНИК] Кровожадность растёт: {self.frenzy}."
            )