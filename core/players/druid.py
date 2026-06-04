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
    # Балансировка пассива «Токсичный круговорот» (см. on_heal_passive).
    POISON_FRACTION     = 0.5   # доля хила, переходящая в яд
    POISON_CAP_PER_TURN = 4     # максимум яда от пассива за один ход

    def __init__(self):
        super().__init__(
            name="Друид",
            max_hp=70,
            max_energy=3,
            gold=100,
            starter_deck_factory=get_druid_deck,
        )
        self.active_ability = DruidAbility()

    def on_turn_start_passive(self, combat_manager) -> None:
        # Сброс бюджета яда на новый ход (тормоз против бесконечного накопления).
        self._poison_budget = self.POISON_CAP_PER_TURN

    def on_heal_passive(self, healed_amount: int, combat_manager) -> None:
        if not combat_manager or healed_amount <= 0:
            return
        enemy = getattr(combat_manager, 'enemy', None)
        if not (enemy and enemy.hp > 0):
            return

        # Яд = доля хила, но не больше остатка бюджета за этот ход.
        budget = getattr(self, '_poison_budget', self.POISON_CAP_PER_TURN)
        gain   = min(max(1, int(healed_amount * self.POISON_FRACTION)), budget)
        if gain <= 0:
            return
        self._poison_budget = budget - gain

        enemy.add_status('poison', gain, combat_manager)
        combat_manager.add_log_message(
            f" [ДРУИД] Токсичный круговорот: враг получает +{gain} яда!"
        )