# core/relics/advanced/healing.py
# Реликвии темы «исцеление и регенерация».
from core.relics.base import Relic
from core.rarity import Rarity


class СердцеТитана(Relic):
    """В конце боя исцеляет на 20% от недостающего HP."""

    def __init__(self):
        super().__init__(
            "Сердце Титана",
            "В конце каждого боя восстанавливает 20% недостающего HP.",
            Rarity.RARE,
        )

    def on_combat_end(self, player, combat_manager=None):
        missing = player.max_hp - player.hp
        if missing > 0:
            heal_amount = max(1, int(missing * 0.20))
            player.heal(heal_amount, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f"[Реликвия] '{self.name}': восстановлено {heal_amount} HP!"
                )


class СнекБар(Relic):
    """Прямой хил игрока увеличивается на +2 HP (в пределах недостающего HP)."""

    def __init__(self):
        super().__init__(
            "Снек-бар",
            "Печеньки на кухне: любой хил игрока увеличивается на +2 HP.",
            Rarity.COMMON,
        )

    def on_heal(self, healed_amount, creature, combat_manager=None):
        bonus = min(2, creature.max_hp - creature.hp)
        if bonus > 0:
            creature.hp += bonus
            # В бою пишем в общий лог; вне боя (отдых/событие) канала нет.
            if combat_manager is not None:
                combat_manager.add_log_message(
                    f"[Реликвия] '{self.name}': +{bonus} HP бонус к хилу!"
                )


class ФоновоеИндексирование(Relic):
    """В начале боя дает игроку 3 Регенерации.

    Калибровка: реген убывает на 1 за тик, поэтому Регенерация 1 лечила суммарно
    лишь 1 HP — ниже порога полезности даже для обычного. 3 = 3+2+1 = 6 HP/бой."""

    def __init__(self):
        super().__init__(
            "Фоновое индексирование",
            "Индексатор молотит в фоне: в начале каждого боя получаете Регенерацию 3.",
            Rarity.COMMON,
        )

    def on_combat_start(self, combat_manager):
        combat_manager.player.add_status("regen", 3, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': Регенерация 3!"
        )
