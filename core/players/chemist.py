from core.players.base import Player
from core.players.abilities import ChemistAbility
from core.cards import (
    create_strike, create_defend, create_coffee_spill, create_voltage_spike,
    create_poison_stab,
)

# Приток Реагента в начало хода (ТОРМОЗ/баланс-ручка класса, _balance_knobs.md).
# Решение юзера (С51): фикс N/ход (как энергия) — простой, предсказуемый, движок
# Нестабильности раскручивается ровно. Стартовое число — калибровка тройки отдельным
# шагом ПОСЛЕ среза.
REAGENT_PER_TURN = 1


def get_chemist_deck():
    """Модульная стартовая колода: простое СЫРЬЁ под слияние (низкая база, разные
    стихии → эмерджентные Глитч-комбо при конкатенации эффектов)."""
    return [
        create_strike(), create_strike(), create_strike(),
        create_defend(), create_defend(),
        create_coffee_spill(),   # Разлитый кофе — сырьё стихии (усилитель)
        create_voltage_spike(),  # Короткое замыкание — сырьё стихии (детонатор)
        create_poison_stab(),    # Legacy-код — сырьё стихии (DoT)
    ]


class Chemist(Player):
    """«Химик Дефектов / Глитч-Мастер» — класс на Card Fusion (§2,
    [[class-concepts-ideas]], _card_fusion_design.md).

    «Варишь карты, не играешь»: на лету сплавляешь две карты руки в Глитч-карту
    (`CombatManager.fuse_hand_cards`), которой нет в пулах. ТОРМОЗ — ресурс Реагент
    (приток фикс/ход). Движок-пассив «Нестабильность» (этап 3): +1 за каждый фьюжн за
    бой, слитые карты получают +Нестабильность к числам — внутрибоевой компаунд кат.4.

    `fusion_enabled=True` открывает доступ к слиянию (гейт как positioning_enabled).
    Ярус 2 (анлок за достижения, [[class-tier-progression]])."""

    def __init__(self):
        super().__init__(
            name="Химик",
            max_hp=70,
            max_energy=3,
            gold=100,
            starter_deck_factory=get_chemist_deck,
        )
        self.active_ability = ChemistAbility()
        # Класс ВКЛЮЧАЕТ слияние всегда — это его механика (не Ставка/опт-ин рана).
        self.fusion_enabled = True
        self.reagent_per_turn = REAGENT_PER_TURN

    def reset_combat_statuses(self) -> None:
        """Между боями: общий сброс + обнуление Реагента (внутрибоевой ресурс, как и
        Нестабильность — копится в пределах одного боя, не переносится)."""
        super().reset_combat_statuses()
        self.reagent = 0

    def on_fusion(self, glitch_card, combat_manager) -> None:
        """Хук СЛИЯНИЯ (зовётся из CombatManager.fuse_hand_cards): пассив-движок
        «Нестабильность» — +1 за каждый фьюжн за бой. Стак даёт +N к урону Глитч-карт
        (EffectCalculator шаг 2e) → поздний бой = чудовищные Глитчи (потолок класса,
        внутрибоевой компаунд кат.4, сброс между боями)."""
        self.add_status("instability", 1, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" [ХИМИК] Нестабильность растёт: {self.instability}."
            )
