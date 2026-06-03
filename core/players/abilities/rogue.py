# core/players/abilities/rogue.py
from core.players.ability import ClassAbility


class RogueAbility(ClassAbility):
    """
    «Вскрытие»
    Удваивает текущее кровотечение на враге.
    Взамен: -1 энергия в следующем ходу.
    Один раз за бой.
    """

    def __init__(self):
        super().__init__(
            name="Вскрытие",
            description="Удвоить кровотечение на враге.\n-1 энергия в следующем ходу.\nОдин раз за бой.",
        )
        self._penalty_pending = False

    def on_combat_start(self, combat_manager) -> None:
        super().on_combat_start(combat_manager)
        self._penalty_pending = False

    def on_turn_start(self, combat_manager) -> None:
        if self._penalty_pending:
            combat_manager.player.energy = max(
                0, combat_manager.player.energy - 1
            )
            combat_manager.add_log_message(
                "[РАЗБОЙНИК] Вскрытие: -1 энергия (штраф прошлого хода)."
            )
            self._penalty_pending = False

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        bleed = combat_manager.enemy.bleed
        if bleed <= 0:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': у врага нет кровотечения!"
            )
            return False

        combat_manager.enemy.bleed *= 2
        self._used            = True
        self._penalty_pending = True
        combat_manager.add_log_message(
            f"[РАЗБОЙНИК] Вскрытие: кровотечение {bleed} -> "
            f"{combat_manager.enemy.bleed}! -1 энергия в следующем ходу."
        )
        return True
