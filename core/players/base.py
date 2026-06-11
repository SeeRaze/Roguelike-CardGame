from core.Creature import Creature
from core.forge import INITIAL_LEVEL_CAP


class Player(Creature):
    """Базовый каркас игрока. Содержит общую логику для всех классов."""

    # Позиционка (§3): зеркальная раскладка партии. Дефолт False = герой во ФРОНТЕ,
    # союзники в ТЫЛУ. Класс типа призывателя ставит True → инверсия (саммоны
    # танкуют во фронте, герой в тылу). Читается assign_party_ranks при старте боя.
    mirrored_layout = False

    def __init__(self, name, max_hp, max_energy, gold, starter_deck_factory):
        super().__init__(name=name, hp=max_hp, max_hp=max_hp)

        self.max_energy = max_energy
        self.energy     = max_energy
        self.gold       = gold

        self._starter_deck_factory  = starter_deck_factory
        self._extra_starter_cards: list = []

        # Активная способность класса -- устанавливается в подклассах
        self.active_ability = None

        # Союзники, переживающие бои: выжившие переносятся между боями.
        # Заполняется CombatManager при победе, восстанавливается при старте
        # следующего боя. Потолок переноса — в CombatManager. (Дремлющий
        # фундамент: производителя-карты призыва нет с С59, инфра под будущие классы.)
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

        # ── CARD FUSION (§2, фундамент Химика) ─────────────────────────────────
        # Гейт ДОСТУПА к слиянию карт в руке (как positioning_enabled у позиционки):
        # дефолт False → механизм core/fusion.py существует, но для всех классов
        # инертен. Химик ставит True. `reagent` — ресурс-ТОРМОЗ слияния (приток
        # фикс/ход, тратится на фьюжн); инертен без fusion_enabled.
        self.fusion_enabled = False
        self.reagent        = 0

    def get_starter_deck(self) -> list:
        return self._starter_deck_factory() + list(self._extra_starter_cards)

    def add_to_starter_deck(self, card) -> None:
        self._extra_starter_cards.append(card)

    def reset_energy(self) -> None:
        self.energy = self.max_energy

    def gain_energy(self, amount: int) -> None:
        """Прибавить энергию в текущем ходу (рамп/бурст). Допускает ВРЕМЕННЫЙ выход за
        max_energy (бурст-ход) — энергия всё равно сбрасывается в max в начале хода.
        Источники: карта «Перерыв», реакция «Аппаратный сбой». Кап источника (напр.
        +3/ход у Аппаратного сбоя) — на стороне ВЫЗЫВАЮЩЕГО, не здесь."""
        if amount > 0:
            self.energy += amount

    # Боевые статусы игрока, сбрасываемые между боями (НЕ переносятся по забегу).
    # Внутрибоевые движки кат.4 (barrier/mastery/echo) живут только в одном бою —
    # их компаунд внутрибоевой; персистентность между боями — отдельный слой.
    _COMBAT_RESET_KEYS = (
        "strength", "firewall", "regen", "vampire",
        "echo", "barrier", "mastery", "discipline",
        "instability",
        # Новые стихии-дебаффы (С58) — внутрибоевые, сбрасываются между боями.
        "legacy", "coffee", "shortcircuit", "tox", "leak", "decomp", "stunned",
        "heal_block",
    )

    def reset_combat_statuses(self) -> None:
        """Обнулить боевое состояние игрока между боями: щит + все статусы.
        Зовётся из GameManager (реальная игра) и balance runner (симуляция)."""
        self.shield = 0
        for key in self._COMBAT_RESET_KEYS:
            self.statuses[key] = 0

    def use_energy(self, amount: int, allow_debt: bool = False) -> None:
        # allow_debt=True (долговой движок §7): энергия может уйти В МИНУС (овердрафт).
        # Дефолт False → клампинг на 0 (обычная игра, регресс-нейтрально).
        self.energy = self.energy - amount if allow_debt else max(self.energy - amount, 0)
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

    def on_combat_won(self, combat_manager) -> None:
        """Хук ПОБЕДЫ в бою (все враги мертвы) — переопределяется в подклассах.
        По умолчанию NO-OP. Берсерк («Отрицание Смерти») конвертирует здесь |минус HP| → FP
        (death-spiral кормит ковку). Зовётся ОДИН раз при победе из _check_victory (живая
        игра) и из бот-цикла (симулятор)."""
        pass