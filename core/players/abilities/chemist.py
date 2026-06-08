# core/players/abilities/chemist.py
from core.players.ability import ClassAbility


class ChemistAbility(ClassAbility):
    """«Сингулярность» (ЗАГЛУШКА, этап 2 = сим-first срез).

    Пик-способность Химика: раз/бой слить ВСЮ руку в одну Глитч-карту
    (_card_fusion_design.md, столп 3). НЕ реализована в этом срезе — решение юзера
    (С51): отложена на отдельную веху. Слот живёт здесь, чтобы у Химика был
    active_ability (UI/бот вызывают .activate/.is_ready единообразно); пока is_ready
    всегда False → способность не активируется ни в живой игре, ни в симе."""

    def __init__(self):
        super().__init__(
            name="Сингулярность",
            description="(скоро) Слить всю руку в одну Глитч-карту. Раз за бой.",
        )

    def is_ready(self) -> bool:
        return False  # заглушка: пик-способность ещё не реализована

    def activate(self, combat_manager) -> bool:
        return False
