from core.players.base import Player
from core.players.abilities import WarriorAbility
from core.cards import (
    create_commit, create_code_review, create_push_to_prod,
    create_punishing_formation, create_shield_wall,
)


def get_warrior_deck():
    # Де-рельсенный стартер (С56): 2 спендера Дисциплины-учителя, БЕЗ в-стартере
    # генератора стаков (кроме пассива «держи строй») → не замкнутый луп. Возмездие/
    # Failover/Стойка (старая ось + билдер) — в драфт-пуле класса (catalog).
    # С60 (задача 4): флат → пол цикла разработки 1:1 (Удар→Коммит, Защита→Код-ревью,
    # Тяж.Клинок→Пуш в прод). Числа идентичны, у Пуша в прод райдер ACCRUE (+1 Баг).
    return [
        create_commit(), create_commit(), create_commit(), create_commit(),
        create_code_review(), create_code_review(), create_code_review(), create_code_review(),
        create_push_to_prod(),
        create_punishing_formation(),   # Дисц → бурст (роль Возмездия)
        create_shield_wall(),           # Дисц → щит-стена (ось выживаемости)
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
                f" [ТЕСТИРОВЩИК] Боевой дух: +{healed} HP в начале хода."
            )
        # ДИСЦИПЛИНА (ступень «Соблюдай»): если Воин начал ход со щитом (держал строй
        # с прошлого хода — этот хук зовётся ДО сброса щита), копит +1 Дисциплины.
        # Каждый стак = +1 к урону всех атак (EffectCalculator шаг 2d) → защита
        # компаундит в атаку. Стабильный накопитель яруса 1 (без побочек).
        if self.shield > 0:
            self.add_status("discipline", 1, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f" [ТЕСТИРОВЩИК] Дисциплина: строй держится, +1 (всего {self.discipline})."
                )
        carry = int(self.shield * 0.5)
        self._passive_shield_carry = carry
        if carry > 0 and combat_manager:
            combat_manager.add_log_message(
                f" [ТЕСТИРОВЩИК] Железный задел: {carry} щита перенесено на новый ход."
            )