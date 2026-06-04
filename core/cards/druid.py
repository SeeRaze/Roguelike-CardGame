# core/cards/druid.py
# Классовая карта-движок Друида. Идентичность класса — «яд». Друид растит
# Вирулентность (+N к каждому наложению яда) за каждый сыгранный скилл (пассив
# Druid.on_card_played_passive), а его яд ЗАГНИВАЕТ (не убывает на враге) —
# вместе это движок кат.4: чем дольше бой, тем сильнее dot.
#
# VirulenceEffect — карта-катализатор, дающая Вирулентность напрямую (стартовый
# разгон движка, по аналогии с MasteryEffect Мага / FrenzyEffect Разбойника).
from core.cards.base import Card
from core.rarity import Rarity


class VirulenceEffect:
    """Накладывает Вирулентность на игрока — +N к будущим наложениям Яда.
    Прямой бустер движка Друида (обычно virulence копится по +1 за скилл)."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.add_status("virulence", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Вирулентность +{amount} (всего: {player.virulence})."
            )


def create_virulent_strain():
    """«Вирулентный штамм» — Вирулентность 2(3). Чистый энейблер движка Друида:
    разгоняет компаунд яда без ожидания серии скиллов."""
    return Card(
        name="Вирулентный штамм",
        cost=1,
        card_type="skill",
        description="Вирулентность 2(3): +N к каждому наложению Яда до конца боя.",
        effects=[VirulenceEffect(2, 3)],
        rarity=Rarity.UNCOMMON,
    )
