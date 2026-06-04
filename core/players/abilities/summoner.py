# core/players/abilities/summoner.py
from core.players.ability import ClassAbility
from core.Summon import Summon


class SummonerAbility(ClassAbility):
    """
    «Подкрепление»
    Призывает Волка-союзника (HP 12, Атака 4) на поле боя.
    Один раз за бой.
    """

    def __init__(self):
        super().__init__(
            name="Подкрепление",
            description="Призвать Волка (HP 12, Атака 4) в помощь.\nОдин раз за бой.",
        )

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        wolf = Summon(name="Волк (подкрепление)", hp=12, attack_power=4,
                      owner=combat_manager.player)
        combat_manager.allies.append(wolf)
        self._used = True
        combat_manager.add_log_message(
            f"[ПРИЗЫВАТЕЛЬ] Подкрепление: призван {wolf.name} "
            f"(HP {wolf.hp}, Атака {wolf.attack_power})!"
        )
        return True
