# Карты вампиризма: накладывают статус-бафф на игрока.
# Кэш-хит триггерится в Creature.take_damage при каждой атаке игрока.

from core.cards.base import Card, DamageEffect
from core.rarity import Rarity


class VampireBuffEffect:
    """Накладывает статус кэш-хита на игрока."""
    def __init__(self, base_val, upgrade_val):
        self.base_val    = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.add_status("cache_hit", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Кэш-хит +{amount}. Итого: {player.statuses['cache_hit']}."
            )


def create_drain():
    """Базовый вампирский удар + бафф вампиризма."""
    return Card(
        name="Высасывание",
        cost=1,
        card_type="attack",
        description="Урон 6 (9). Кэш-хит +4 (6).",
        effects=[DamageEffect(6, 9), VampireBuffEffect(4, 6)],
        rarity=Rarity.UNCOMMON,
    )


def create_blood_feast():
    """Тяжёлый удар с мощным вампиризмом. Изгнание."""
    return Card(
        name="Кровавый Пир",
        cost=2,
        card_type="attack",
        description="Урон 18 (24). Кэш-хит +10 (15). Изгнание.",
        effects=[DamageEffect(18, 24), VampireBuffEffect(10, 15)],
        rarity=Rarity.RARE,
        exile=True,
    )


def create_life_tap():
    """Слабый удар, но чистый вампиризм без урона."""
    return Card(
        name="Жизнеотвод",
        cost=1,
        card_type="attack",
        description="Урон 4 (6). Кэш-хит +6 (9).",
        effects=[DamageEffect(4, 6), VampireBuffEffect(6, 9)],
        rarity=Rarity.COMMON,
    )