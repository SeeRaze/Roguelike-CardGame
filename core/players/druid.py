from core.players.base import Player
from core.players.abilities import DruidAbility
from core.cards import (
    create_strike, create_defend,
    create_bandage, create_regenerate, create_vitality,
    create_poison_stab, create_toxic_cloud, create_virulent_strain,
)


def get_druid_deck():
    return [
        create_strike(), create_strike(),
        create_defend(), create_defend(),
        create_bandage(),
        create_regenerate(),
        create_vitality(),
        create_poison_stab(),
        create_toxic_cloud(),
        create_virulent_strain(),   # классовая: движок кат.4 (Вирулентность)
    ]


class Druid(Player):
    # Балансировка пассива «Токсичный круговорот» (см. on_heal_passive).
    POISON_FRACTION     = 0.3   # доля хила, переходящая в яд
    POISON_CAP_PER_TURN = 3     # максимум яда от пассива за один ход

    def __init__(self):
        super().__init__(
            name="Друид",
            max_hp=65,
            max_energy=3,
            gold=100,
            starter_deck_factory=get_druid_deck,
        )
        self.active_ability = DruidAbility()

    def on_turn_start_passive(self, combat_manager) -> None:
        # Сброс бюджета яда на новый ход (тормоз против бесконечного накопления).
        self._poison_budget = self.POISON_CAP_PER_TURN

    def on_card_played_passive(self, card, combat_manager) -> None:
        # «Вирулентность»: каждый сыгранный СКИЛЛ растит virulence на 1 (движок
        # кат.4). virulence усиливает все будущие наложения Яда (PoisonEffect),
        # а яд Друида загнивает (не убывает на враге) — вместе нарастающий dot.
        if card is None or not combat_manager:
            return
        if card.card_type == "skill":
            self.add_status("virulence", 1, combat_manager)
            combat_manager.add_log_message(
                f" [ДРУИД] Вирулентность растёт: {self.virulence}."
            )

    def on_heal_passive(self, healed_amount: int, combat_manager) -> None:
        # «Токсичный круговорот»: часть исцеления Друид ЖЕРТВУЕТ — отдаёт это
        # HP обратно и превращает в яд на враге. Чистое лечение снижается
        # (sustain слабее), зато враг травится. Тема «жизнь ↔ яд» сохранена.
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

        # Жертва: возвращаем часть полученного HP (net-лечение режется).
        self.hp = max(1, self.hp - gain)

        enemy.add_status('poison', gain, combat_manager)
        combat_manager.add_log_message(
            f" [ДРУИД] Токсичный круговорот: жертвует {gain} HP → "
            f"враг получает +{gain} яда!"
        )