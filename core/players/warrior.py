from core.players.base import Player
from core.players.abilities import WarriorAbility
from core.cards import (
    create_strike, create_defend, create_heavy_blade, create_retribution,
    create_steel_barricade,
)


def get_warrior_deck():
    return [
        create_strike(), create_strike(), create_strike(), create_strike(),
        create_defend(), create_defend(), create_defend(), create_defend(),
        create_heavy_blade(),
        create_retribution(),       # классовая: щит → урон (защита = атака)
        create_steel_barricade(),   # классовая: движок кат.4 (несгораемый щит)
    ]


class Warrior(Player):
    def __init__(self):
        super().__init__(
            name="Воин",
            max_hp=90,
            max_energy=3,
            gold=100,
            starter_deck_factory=get_warrior_deck,
        )
        self.active_ability = WarriorAbility()

    def on_turn_start_passive(self, combat_manager) -> None:
        # Пассивный хил: 3 HP в начале хода (боевой дух танка).
        healed = self.heal(3, combat_manager)
        if healed > 0 and combat_manager:
            combat_manager.add_log_message(
                f" [ВОИН] Боевой дух: +{healed} HP в начале хода."
            )
        # ДИСЦИПЛИНА (ступень «Соблюдай»): если Воин начал ход со щитом (держал строй
        # с прошлого хода — этот хук зовётся ДО сброса щита), копит +1 Дисциплины.
        # Каждый стак = +1 к урону всех атак (EffectCalculator шаг 2d) → защита
        # компаундит в атаку. Стабильный накопитель яруса 1 (без побочек).
        if self.shield > 0:
            self.add_status("discipline", 1, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f" [ВОИН] Дисциплина: строй держится, +1 (всего {self.discipline})."
                )
        carry = int(self.shield * 0.5)
        self._passive_shield_carry = carry
        if carry > 0 and combat_manager:
            combat_manager.add_log_message(
                f" [ВОИН] Железный задел: {carry} щита перенесено на новый ход."
            )