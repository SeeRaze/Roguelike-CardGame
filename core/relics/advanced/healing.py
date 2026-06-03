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


class СтараяПиявка(Relic):
    """Прямой хил увеличивается на +2 HP."""

    def __init__(self):
        super().__init__(
            "Старая Пиявка",
            "Любой хил игрока увеличивается на +2 HP.",
            Rarity.COMMON,
        )

    def on_heal(self, healed_amount, creature):
        bonus = min(2, creature.max_hp - creature.hp)
        if bonus > 0:
            creature.hp += bonus
            print(f"[Реликвия] 'Старая Пиявка': +{bonus} HP бонус к хилу!")


class ЗасохшийКлевер(Relic):
    """В начале боя дает игроку 1 Регенерацию."""

    def __init__(self):
        super().__init__(
            "Засохший Клевер",
            "В начале каждого боя получаете Регенерацию 1.",
            Rarity.COMMON,
        )

    def on_combat_start(self, combat_manager):
        combat_manager.player.add_status("regen", 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': Регенерация 1!"
        )
