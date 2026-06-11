# core/relics/advanced/bleed_poison.py
# Реликвии темы Legacy-код (накладывание/усиление DoT на враге). «Яд» влит в
# Legacy при сносе старых стихий (С58); «Кровотечение» влито в Legacy при
# консолидации статусов (С59) — единственный DoT в сеттинге = Legacy-код.
from core.relics.base import Relic
from core.rarity import Rarity


class СборщикМусора(Relic):
    """При разыгрывании карты с Изгнанием: +1 Энергия + Legacy-код 2 на врага."""

    def __init__(self):
        super().__init__(
            "Сборщик мусора",
            "Сборщик мусора освобождает ресурс: разыгрывая карту с Изгнанием — +1 Энергия и Legacy-код 2 на врага.",
            Rarity.UNCOMMON,
        )

    def on_card_played(self, card, combat_manager):
        if getattr(card, 'exile', False):
            combat_manager.player.energy += 1
            # Цель — ЖИВОЙ враг (в групповом бою enemies[0] может быть трупом).
            target = combat_manager.get_target_enemy()
            if target is None:
                return
            target.add_status("legacy", 2, combat_manager)
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': +1 Энергия, Legacy-код 2 на врага!"
            )


class ЗомбиПроцесс(Relic):
    """Legacy-код не убывает в конце хода (процесс не умирает → DoT копится).
    Логика «не убывает» — в Creature.tick_statuses (проверка по имени реликвии)."""

    def __init__(self):
        super().__init__(
            "Зомби-процесс",
            "Процесс не умирает: Legacy-код на враге в конце хода не убывает (копится).",
            Rarity.RARE,
        )


class GitBlame(Relic):
    """В начале каждого боя вешает Legacy-код 3 на врага."""

    def __init__(self):
        super().__init__(
            "git blame",
            "git blame нашёл предка-виновника: в начале каждого боя враг получает Legacy-код 3.",
            Rarity.UNCOMMON,
        )

    def on_combat_start(self, combat_manager):
        combat_manager.enemy.add_status("legacy", 3, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': враг получает Legacy-код 3!"
        )


class Санитайзер(Relic):
    """При получении щита -- враг получает 1 Legacy-код."""

    def __init__(self):
        super().__init__(
            "Санитайзер",
            "Санитайзер колет инъекции: когда вы получаете щит,\nвраг получает 1 Legacy-код.",
            Rarity.UNCOMMON,
        )

    def on_shield_gained(self, amount, creature, combat_manager=None):
        if combat_manager is None:
            return
        # Цель — ЖИВОЙ враг (щит мог быть получен уже после смерти enemies[0]).
        target = combat_manager.get_target_enemy()
        if target is None:
            return
        target.add_status("legacy", 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': враг получает Legacy-код 1!"
        )
