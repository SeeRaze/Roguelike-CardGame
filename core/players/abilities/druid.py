# core/players/abilities/druid.py
from core.players.ability import ClassAbility


class DruidAbility(ClassAbility):
    """
    «Токсичный взрыв»
    Снимает весь яд с врага, наносит этот урон разом.
    Друид получает Регенерацию = половина снятого яда.
    Один раз за бой.
    """

    def __init__(self):
        super().__init__(
            name="Токсичный взрыв",
            description="Снять весь яд с врага, нанести разом.\n"
                        "Регенерация = половина снятого яда.\n"
                        "Один раз за бой.",
        )

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        poison = combat_manager.enemy.poison
        if poison <= 0:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': у врага нет яда!"
            )
            return False

        combat_manager.enemy.poison = 0
        combat_manager.enemy.take_damage(
            poison, attacker=combat_manager.player,
            combat_manager=combat_manager
        )

        regen_gain = max(1, poison // 2)
        combat_manager.player.add_status("regen", regen_gain, combat_manager)

        self._used = True
        combat_manager.add_log_message(
            f"[ДРУИД] Токсичный взрыв: {poison} урона врагу! "
            f"+{regen_gain} Регенерации Друиду."
        )
        return True
