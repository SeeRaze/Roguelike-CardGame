# core/cards/summon.py
# Карты призыва: создают существо-союзника (Summon) на поле боя.
from core.cards.base import Card
from core.Summon import Summon
from core.rarity import Rarity


class SummonEffect:
    """Эффект призыва: создаёт Summon и добавляет в combat_manager.allies."""

    def __init__(self, summon_class, name, hp, attack_power):
        self.summon_class = summon_class
        self.name         = name
        self.hp           = hp
        self.attack_power = attack_power

    def execute(self, player, enemy, combat_manager, is_upgraded):
        hp = self.hp + 5 if is_upgraded else self.hp
        atk = self.attack_power + 2 if is_upgraded else self.attack_power
        ally = self.summon_class(
            name=self.name, hp=hp, attack_power=atk, owner=player
        )
        # Добавляем союзника в бой
        if combat_manager and hasattr(combat_manager, 'allies'):
            combat_manager.allies.append(ally)
        if combat_manager:
            combat_manager.add_log_message(
                f"[ПРИЗЫВ] {ally.name} (HP:{ally.hp}, Атака:{ally.attack_power})"
            )


def create_summon_wolf():
    """Базовый призыв волка-союзника."""
    return Card(
        name="Призвать Волка",
        cost=2,
        card_type="skill",
        description="Призывает Волка (HP 15, Атака 5). Улучшение: HP 20, Атака 7.",
        effects=[SummonEffect(Summon, "Волк", 15, 5)],
        rarity=Rarity.COMMON,
    )


def create_summon_golem():
    """Мощный призыв голема-защитника."""
    return Card(
        name="Призвать Голема",
        cost=3,
        card_type="skill",
        description="Призывает Голема (HP 30, Атака 8). Улучшение: HP 35, Атака 10.",
        effects=[SummonEffect(Summon, "Голем", 30, 8)],
        rarity=Rarity.UNCOMMON,
    )
