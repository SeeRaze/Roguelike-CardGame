from core.Creature import Creature


class Player(Creature):
    """Базовый каркас игрока. Содержит общую логику для всех классов."""

    def __init__(self, name, max_hp, max_energy, gold, starter_deck_factory):
        super().__init__(name=name, hp=max_hp, max_hp=max_hp)

        self.max_energy = max_energy
        self.energy     = max_energy
        self.gold       = gold

        self._starter_deck_factory  = starter_deck_factory
        self._extra_starter_cards: list = []

        # Активная способность класса -- устанавливается в подклассах
        self.active_ability = None

        # Стая, переживающая бои (Призыватель): выжившие союзники переносятся
        # между боями. Заполняется CombatManager при победе, восстанавливается
        # при старте следующего боя. Потолок переноса — в CombatManager.
        self.persistent_allies: list = []

    def get_starter_deck(self) -> list:
        return self._starter_deck_factory() + list(self._extra_starter_cards)

    def add_to_starter_deck(self, card) -> None:
        self._extra_starter_cards.append(card)

    def reset_energy(self) -> None:
        self.energy = self.max_energy

    # Боевые статусы игрока, сбрасываемые между боями (НЕ переносятся по забегу).
    # Внутрибоевые движки кат.4 (barrier/mastery/echo) живут только в одном бою —
    # их компаунд внутрибоевой; персистентность между боями — отдельный слой.
    _COMBAT_RESET_KEYS = (
        "weak", "vulnerable", "wet", "ignited", "poison", "shock", "shatter",
        "strength", "thorns", "regen", "bleed", "vampire",
        "echo", "barrier", "mastery",
    )

    def reset_combat_statuses(self) -> None:
        """Обнулить боевое состояние игрока между боями: щит + все статусы.
        Зовётся из GameManager (реальная игра) и balance runner (симуляция)."""
        self.shield = 0
        for key in self._COMBAT_RESET_KEYS:
            self.statuses[key] = 0

    def use_energy(self, amount: int) -> None:
        self.energy = max(self.energy - amount, 0)
        print(
            f" [ЭНЕРГИЯ] Потрачено {amount}. Осталось: {self.energy}/{self.max_energy}"
        )

    # ------------------------------------------------------------------
    # Хуки классовых пассивок -- переопределяются в подклассах
    # ------------------------------------------------------------------

    def on_turn_start_passive(self, combat_manager) -> None:
        pass

    def on_card_played_passive(self, card, combat_manager) -> None:
        pass

    def on_heal_passive(self, healed_amount: int, combat_manager) -> None:
        pass