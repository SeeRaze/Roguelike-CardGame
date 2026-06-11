# core/relics/advanced/shield.py
# Реликвии темы «щит и стойкость».
from core.relics.base import Relic
from core.rarity import Rarity


class ДМСБазовый(Relic):
    """+5 к макс. HP. Младшее звено страховой HP-линейки (старшее — ДМС
    платиновый пакет, +25). Дешёвый ранний источник max HP (economy-axis-trinity)."""

    def __init__(self):
        super().__init__(
            "ДМС (базовый пакет)",
            "Базовый медполис: максимальный запас здоровья +5.",
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


class ДМСПлатиновый(Relic):
    """+25 к макс. HP. Старшее звено страховой HP-линейки (младшее — ДМС
    (базовый пакет), +5 COMMON, задаёт паттерн). Дешёвый РАННИЙ источник max HP,
    НЕ гейтнутый боссом (HP-ось, economy-axis-trinity)."""

    GAIN = 25

    def __init__(self):
        super().__init__(
            "ДМС (платиновый пакет)",
            f"Платиновый медполис: максимальный запас здоровья +{self.GAIN}.",
            Rarity.UNCOMMON,
        )
        self._applied = False

    def on_combat_start(self, combat_manager):
        if not self._applied:
            combat_manager.player.max_hp += self.GAIN
            combat_manager.player.hp = min(
                combat_manager.player.hp + self.GAIN,
                combat_manager.player.max_hp
            )
            self._applied = True
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': Макс. HP +{self.GAIN}!"
            )


class Антивирус(Relic):
    """В начале боя игрок получает Шипы 3 (отражает урон атакующему)."""

    def __init__(self):
        super().__init__(
            "Антивирус",
            "В начале каждого боя антивирус ставит защиту: Шипы 3.",
            Rarity.COMMON,
        )

    def on_combat_start(self, combat_manager):
        combat_manager.player.add_status("thorns", 3, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': Шипы 3!"
        )


class Кэш(Relic):
    """АКТИВНАЯ. Один раз за бой: щит не сбрасывается в начале следующего хода."""

    def __init__(self):
        super().__init__(
            "Кэш",
            "АКТИВНАЯ. Один раз за бой: закэшировать щит —\nон не сбрасывается в начале следующего хода.",
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
            saved = getattr(combat_manager.player, '_cache_held_shield', 0)
            if saved > 0:
                combat_manager.player.shield = saved
                combat_manager.add_log_message(
                    f"[Реликвия] '{self.name}': щит {saved} сохранён!"
                )
            self._shield_hold = False
            combat_manager.player._cache_held_shield = 0
