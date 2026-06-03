# core/relics/advanced.py
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
            combat_manager.enemy.poison += 2
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': +1 Энергия, Яд 2 на врага!"
            )


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


class ГнилойКлык(Relic):
    """Кровотечение не сбрасывается полностью — уменьшается вдвое."""

    def __init__(self):
        super().__init__(
            "Гнилой Клык",
            "Кровотечение не сбрасывается в конце хода, а уменьшается вдвое.",
            Rarity.RARE,
        )
        self._intercepted = False

    def on_bleed_tick(self, bleed_dmg, creature, combat_manager):
        self._intercepted = True
        return bleed_dmg

    def on_turn_start(self, combat_manager):
        self._intercepted = False


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


class СчастливаяМонетка(Relic):
    """При открытии обычного сундука +10 золота."""

    def __init__(self):
        super().__init__(
            "Счастливая Монетка",
            "При открытии обычного сундука получаете +10 золота.",
            Rarity.COMMON,
        )

    def on_chest_opened(self, chest_type: str, game_manager):
        if chest_type == "common":
            game_manager.player_gold += 10
            print(f"[Реликвия] '{self.name}': +10 золота!")


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


class Заплатка(Relic):
    """Увеличивает максимальный HP на +5 при получении."""

    def __init__(self):
        super().__init__(
            "Заплатка",
            "Максимальный запас здоровья увеличивается на +5.",
            Rarity.COMMON,
        )
        self._applied = False

    def on_combat_start(self, combat_manager):
        if not self._applied:
            combat_manager.player.max_hp += 5
            combat_manager.player.hp = min(
                combat_manager.player.hp + 5,
                combat_manager.player.max_hp
            )
            self._applied = True
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': Макс. HP +5!"
            )


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
        combat_manager.enemy.add_status("bleed", 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': враг получает Кровотечение 1!"
        )


class ЖелезнаяВоля(Relic):
    """АКТИВНАЯ. Один раз за бой: щит не сбрасывается в начале следующего хода."""

    def __init__(self):
        super().__init__(
            "Железная Воля",
            "АКТИВНАЯ. Один раз за бой:\nщит не сбрасывается в начале следующего хода.",
            Rarity.RARE,
        )
        self.is_active    = True
        self._used        = False
        self._shield_hold = False

    def on_combat_start(self, combat_manager):
        self._used        = False
        self._shield_hold = False

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': уже использована в этом бою!"
            )
            return False
        if combat_manager.player.shield <= 0:
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': нет щита для сохранения!"
            )
            return False
        self._used        = True
        self._shield_hold = True
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': щит сохранится в следующем ходу!"
        )
        return True

    def on_turn_start(self, combat_manager):
        if self._shield_hold:
            saved = getattr(combat_manager.player, '_iron_will_shield', 0)
            if saved > 0:
                combat_manager.player.shield = saved
                combat_manager.add_log_message(
                    f"[Реликвия] '{self.name}': щит {saved} сохранён!"
                )
            self._shield_hold = False
            combat_manager.player._iron_will_shield = 0