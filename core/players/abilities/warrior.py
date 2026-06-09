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
            name="Откат релиза",
            description="Накопленную защиту — врагу в откат:\n"
                        "урон = 50% текущего щита.\nОдин раз за бой.",
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

        # Живой враг с учётом перехвата (в группе enemies[0] может быть трупом).
        target = combat_manager.get_target_enemy()
        if target is None:
            return False

        dmg = max(1, shield // 2)
        target.take_damage(dmg, attacker=combat_manager.player,
                            combat_manager=combat_manager)
        self._used = True
        combat_manager.add_log_message(
            f"[ТЕСТИРОВЩИК] Откат релиза: {dmg} урона врагу (50% от {shield} щита)!"
        )
        return True
