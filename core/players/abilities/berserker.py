# core/players/abilities/berserker.py
from core.players.ability import ClassAbility


class BerserkerAbility(ClassAbility):
    """
    «Кровавая ярость»
    Берсерк наносит себе урон сквозь щит (10% макс HP, мин 1).
    Взамен получает Ярость = нанесённый урон * 2.
    Один раз за бой.
    """

    def __init__(self):
        super().__init__(
            name="Кровавая ярость",
            description="Нанести себе 10% макс HP сквозь щит.\n"
                        "Ярость = урон * 2.\n"
                        "Один раз за бой.",
        )

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        player = combat_manager.player
        self_dmg = max(1, player.max_hp // 10)

        # Урон сквозь щит -- напрямую в HP
        player.hp = max(0, player.hp - self_dmg)
        strength_gain = self_dmg * 2

        player.strength += strength_gain
        self._used = True

        combat_manager.add_log_message(
            f"[БЕРСЕРК] Кровавая ярость: -{self_dmg} HP себе, "
            f"+{strength_gain} Ярости!"
        )

        if player.hp <= 0:
            combat_manager.add_log_message(
                "[!] Берсерк пал от собственной ярости..."
            )
        return True
