from core.Creature import Creature


class Player(Creature):
    """Базовый каркас игрока. Содержит общую логику для всех классов."""

    def __init__(self, name, max_hp, max_energy, gold, starter_deck_factory):
        super().__init__(name=name, hp=max_hp, max_hp=max_hp)

        self.max_energy = max_energy
        self.energy     = max_energy
        self.gold       = gold

        self._starter_deck_factory = starter_deck_factory
        # Дополнительные карты, добавленные в ходе забега (реликвии, события).
        # Подмешиваются в стартовую деку при get_starter_deck().
        self._extra_starter_cards: list = []

    def get_starter_deck(self) -> list:
        """Возвращает стартовую деку + любые добавленные карты."""
        return self._starter_deck_factory() + list(self._extra_starter_cards)

    def add_to_starter_deck(self, card) -> None:
        """Добавляет карту в стартовую деку (для реликвий/событий)."""
        self._extra_starter_cards.append(card)

    def reset_energy(self) -> None:
        self.energy = self.max_energy

    def use_energy(self, amount: int) -> None:
        self.energy = max(self.energy - amount, 0)
        print(
            f" [ЭНЕРГИЯ] Потрачено {amount}. Осталось: {self.energy}/{self.max_energy}"
        )