# core/relics/advanced/epic_legendary.py
# Высокотировый контент — мощные ВНУТРИБОЕВЫЕ движки (EPIC) и «Проклятые
# Артефакты»-джокеры (LEGENDARY: меняют правила игры ценой трейдоффа).
# Все — на ДОЛГОЖИВУЩИХ примитивах (echo/barrier/щит/×урон/изгнание карт), без
# привязки к конкретным классам (классы переписывают — см. [[class-redesign-incoming]]).
from core.relics.base import Relic
from core.rarity import Rarity


class ЭхоВечности(Relic):
    """В начале каждого хода игрок получает Эхо 1 (следующая разыгранная карта
    срабатывает повторно). Универсальный ретриггер-движок: удваивает первую карту
    каждого хода независимо от класса/архетипа. Эхо — внутрибоевой статус
    (сбрасывается между боями), поэтому это движок ТЕМПА, а не компаунда по забегу."""

    def __init__(self):
        super().__init__(
            "Эхо Вечности",
            "В начале каждого хода вы получаете Эхо 1:\n"
            "следующая сыгранная карта срабатывает дважды.",
            Rarity.EPIC,
        )

    def on_turn_start(self, combat_manager):
        combat_manager.player.add_status("echo", 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': Эхо 1 — следующая карта сработает дважды!"
        )


class НесокрушимыйБастион(Relic):
    """Каждый раз, когда игрок получает щит, половина этого щита дублируется в
    Барьер (несгораемый — не сбрасывается в начале хода). Оборонный движок:
    обычный щит сгорает каждый ход, а Барьер копится → стена растёт от любой
    карты защиты. Половина (а не весь) — чтобы не превращать каждый блок в
    перманент мгновенно (баланс оборонного компаунда)."""

    # Доля полученного щита, уходящая в несгораемый Барьер.
    BARRIER_FRACTION = 0.5

    def __init__(self):
        super().__init__(
            "Несокрушимый Бастион",
            "Половина полученного щита превращается в Барьер\n"
            "(несгораемый щит — не сбрасывается между ходами).",
            Rarity.EPIC,
        )

    def on_shield_gained(self, amount, creature, combat_manager=None):
        if combat_manager is None or creature is not combat_manager.player:
            return
        bonus = int(amount * self.BARRIER_FRACTION)
        if bonus <= 0:
            return
        # add_status("barrier") НЕ дёргает gain_shield → без рекурсии on_shield_gained.
        creature.add_status("barrier", bonus, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': +{bonus} Барьера (несгораемый)!"
        )
