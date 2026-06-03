# core/relics/advanced/shield.py
# Реликвии темы «щит и стойкость».
from core.relics.base import Relic
from core.rarity import Rarity


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
