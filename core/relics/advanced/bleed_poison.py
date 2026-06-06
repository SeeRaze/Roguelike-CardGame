# core/relics/advanced/bleed_poison.py
# Реликвии темы «кровь и яд» (Кровотечение / Яд).
from core.relics.base import Relic
from core.rarity import Rarity


class ОкровавленныйШприц(Relic):
    """При разыгрывании карты с Изгнанием: +1 Энергия + Яд 2 на врага."""

    def __init__(self):
        super().__init__(
            "Окровавленный Шприц",
            "Разыгрывая карту с Изгнанием: +1 Энергия и Яд 2 на врага.",
            Rarity.UNCOMMON,
        )

    def on_card_played(self, card, combat_manager):
        if getattr(card, 'exile', False):
            combat_manager.player.energy += 1
            # Цель — ЖИВОЙ враг (в групповом бою enemies[0] может быть трупом).
            target = combat_manager.get_target_enemy()
            if target is None:
                return
            target.poison += 2
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': +1 Энергия, Яд 2 на врага!"
            )


class ГнилойКлык(Relic):
    """Кровотечение не сбрасывается полностью — уменьшается вдвое.
    Логика уполовинивания — в Creature.tick_statuses (проверка по имени реликвии)."""

    def __init__(self):
        super().__init__(
            "Гнилой Клык",
            "Кровотечение не сбрасывается в конце хода, а уменьшается вдвое.",
            Rarity.RARE,
        )


class ФлаконСЖелчью(Relic):
    """В начале каждого боя вешает Яд 3 на врага."""

    def __init__(self):
        super().__init__(
            "Флакон с Желчью",
            "В начале каждого боя враг получает Яд 3.",
            Rarity.UNCOMMON,
        )

    def on_combat_start(self, combat_manager):
        combat_manager.enemy.poison += 3
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': враг отравлен на 3!"
        )


class ШипастаяБроня(Relic):
    """При получении щита -- враг получает 1 Кровотечение."""

    def __init__(self):
        super().__init__(
            "Шипастая Броня",
            "Каждый раз, когда вы получаете щит,\nвраг получает 1 Кровотечение.",
            Rarity.UNCOMMON,
        )

    def on_shield_gained(self, amount, creature, combat_manager=None):
        if combat_manager is None:
            return
        # Цель — ЖИВОЙ враг (щит мог быть получен уже после смерти enemies[0]).
        target = combat_manager.get_target_enemy()
        if target is None:
            return
        target.add_status("bleed", 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': враг получает Кровотечение 1!"
        )
