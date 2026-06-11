# core/players/abilities/mage.py
from core.players.ability import ClassAbility


class MageAbility(ClassAbility):
    """
    «Стихийный барьер»
    Блокирует наложение стихий на врага на 1 ход.
    Взамен: щит = сумма всех стихийных стаков на поле * 3.
    Один раз за бой.

    Стихийные статусы: coffee, legacy (половинки ХОТФИКСа).
    Флаг _elemental_blocked проверяется в Creature.add_status.
    """

    ELEMENTAL_STATUSES = ("coffee", "legacy")

    def __init__(self):
        super().__init__(
            name="Try-Except",
            description="Оборачиваешь ход в try-except:\n"
                        "стихии на врага блокируются на 1 ход,\n"
                        "щит = сумма стихийных стаков * 3.\n"
                        "Один раз за бой.",
        )

    def on_combat_start(self, combat_manager) -> None:
        super().on_combat_start(combat_manager)

    def on_turn_start(self, combat_manager) -> None:
        """Снимаем блок в начале следующего хода."""
        if getattr(combat_manager, '_elemental_blocked', False):
            combat_manager._elemental_blocked = False
            combat_manager.add_log_message(
                "[ВАЙБ-КОДЕР] Try-Except: блок стихий снят."
            )

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        # Считаем сумму стихийных стаков на обоих существах
        total = 0
        for creature in (combat_manager.player, combat_manager.enemy):
            for key in self.ELEMENTAL_STATUSES:
                total += max(0, getattr(creature, key, 0))

        shield_gain = total * 3
        combat_manager._elemental_blocked = True
        self._used = True

        if shield_gain > 0:
            combat_manager.player.gain_shield(shield_gain, combat_manager)
            combat_manager.add_log_message(
                f"[ВАЙБ-КОДЕР] Try-Except: +{shield_gain} щита "
                f"(стаки {total} * 3)! Стихии заблокированы на 1 ход."
            )
        else:
            combat_manager.add_log_message(
                "[ВАЙБ-КОДЕР] Try-Except: стихий нет, щит не получен. "
                "Стихии заблокированы на 1 ход."
            )
        return True
