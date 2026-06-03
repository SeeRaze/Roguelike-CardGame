from core.players.base import Player
from core.players.abilities import DruidAbility
from core.cards import (
    create_strike, create_defend,
    create_bandage, create_regenerate, create_vitality,
    create_poison_stab, create_toxic_cloud,
)


def get_druid_deck():
    return [
        create_strike(), create_strike(),
        create_defend(), create_defend(),
        create_bandage(), create_bandage(),
        create_regenerate(),
        create_vitality(),
        create_poison_stab(),
        create_toxic_cloud(),
    ]


class Druid(Player):
    def __init__(self):
        super().__init__(
            name="Друид",
            max_hp=70,
            max_energy=3,
            gold=100,
            starter_deck_factory=get_druid_deck,
        )
        self.active_ability = DruidAbility()

    def on_heal_passive(self, healed_amount: int, combat_manager) -> None:
        if not combat_manager or healed_amount <= 0:
            return
        enemy = getattr(combat_manager, 'enemy', None)
        if enemy and enemy.hp > 0:
            enemy.add_status('poison', healed_amount, combat_manager)
            combat_manager.add_log_message(
                f" [ДРУИД] Токсичный круговорот: враг получает "
                f"+{healed_amount} яда!"
            )