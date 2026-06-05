from core.Creature import Creature
from core.forge import INITIAL_LEVEL_CAP


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

        # ── КОВКА КАРТ (Сессия 39.5, _upgrade_design.md §2-3) ──────────────────
        # Мета-прокачка живёт в ЕДИНОМ плоском словаре игрока (uid → запись), а не
        # на объектах карт (sim-friendly, чистый рендер). Состояние персистентно
        # ВЕСЬ забег — НЕ сбрасывается reset_combat_statuses (как persistent_allies).
        self.deck_forge_state: dict = {}   # _fuid -> {"level": int, "slots": [..]}
        self.forge_points    = 0           # валюта ковки FP (приток за бои/боссов)
        self.forge_level_cap = INITIAL_LEVEL_CAP   # кап уровня карты (снимается боссами)
        self._forge_uid_next = 0           # счётчик выдачи uid инстансам карт
        self.atk_mult        = 1.0         # компаунд-множитель урона (Заточка; шаг 8)

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
        "echo", "barrier", "mastery", "frenzy", "virulence",
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