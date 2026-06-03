# core/players/abilities/warrior.py
from core.players.ability import ClassAbility


class WarriorAbility(ClassAbility):
    """
    «Щитовой удар»
    Наносит врагу урон равный 50% текущего щита Воина.
    Один раз за бой.
    """

    def __init__(self):
        super().__init__(
            name="Щитовой удар",
            description="Нанести врагу урон = 50% текущего щита.\nОдин раз за бой.",
        )

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        shield = combat_manager.player.shield
        if shield <= 0:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': нет щита для удара!"
            )
            return False

        dmg = max(1, shield // 2)
        combat_manager.enemy.take_damage(dmg, attacker=combat_manager.player,
                                         combat_manager=combat_manager)
        self._used = True
        combat_manager.add_log_message(
            f"[ВОИН] Щитовой удар: {dmg} урона врагу (50% от {shield} щита)!"
        )
        return True
