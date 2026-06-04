# core/relics/advanced/damage.py
# Реликвии темы «урон и ослабление врага».
from core.relics.base import Relic
from core.rarity import Rarity


class ПроклятаяКорона(Relic):
    def __init__(self):
        super().__init__(
            "Проклятая Корона",
            "Урон атаками x2. Цена удаления карт x2. Золото из наград исчезает.",
            Rarity.LEGENDARY,
        )

    def on_damage_calculated(self, base_dmg, is_player_attack=True):
        if is_player_attack:
            return base_dmg * 2
        return base_dmg


class ЗаточенныйОсколок(Relic):
    def __init__(self):
        super().__init__(
            "Заточенный Осколок",
            "Первая атака в каждом бою наносит +3 урона.",
            Rarity.COMMON,
        )
        self._used_this_combat = False

    def on_combat_start(self, combat_manager):
        self._used_this_combat = False

    def on_damage_calculated(self, base_dmg, is_player_attack=True):
        if is_player_attack and not self._used_this_combat:
            self._used_this_combat = True
            return base_dmg + 3
        return base_dmg


class СвинцовыйНабалдашник(Relic):
    """Первая атака в ходу гарантированно накладывает Слабость 1."""

    def __init__(self):
        super().__init__(
            "Свинцовый Набалдашник",
            "Первая атака в каждом ходу накладывает Слабость 1 на врага.",
            Rarity.UNCOMMON,
        )
        self._used_this_turn = False

    def on_card_played(self, card, combat_manager):
        if self._used_this_turn:
            return
        if card.card_type == "attack":
            combat_manager.enemy.add_status("weak", 1, combat_manager)
            self._used_this_turn = True
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': Слабость 1 на врага!"
            )

    def on_turn_start(self, combat_manager):
        self._used_this_turn = False


class ТрофейныйКлык(Relic):
    """При убийстве врага: +1 Сила до конца боя."""

    def __init__(self):
        super().__init__(
            "Трофейный Клык",
            "Каждый раз, когда вы убиваете врага,\nполучаете +1 Силы до конца боя.",
            Rarity.UNCOMMON,
        )

    def on_kill(self, enemy, combat_manager):
        combat_manager.player.strength += 1
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': +1 Сила (текущая: {combat_manager.player.strength})!"
        )


class БерсеркМедальон(Relic):
    """При убийстве врага: +1 Энергия."""

    def __init__(self):
        super().__init__(
            "Берсерк-Медальон",
            "Каждый раз, когда вы убиваете врага,\nвосстанавливаете +1 Энергию.",
            Rarity.RARE,
        )

    def on_kill(self, enemy, combat_manager):
        combat_manager.player.energy += 1
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': +1 Энергия!"
        )
