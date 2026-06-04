# core/cards/mage.py
# Классовые карты Мага. Идентичность класса — «стихии и комбо»: Маг вешает
# стихийные статусы и детонирует их через комбо-реестр (core/ComboRegistry.py).
# «Закипание» — энейблер ПАР: вешает Мокрый и Горение разом, чтобы следующая
# атака сработала с ×2.0 урона.
from core.cards.base import Card, DamageEffect, StatusEffect
from core.rarity import Rarity


def create_boil():
    """«Закипание» — вешает Мокрый (3) и Горение (3) на цель + урон 5.
    Улучшение: урон 6, статусы по 4 хода. Стоит 1 энергии: сетап стоит дёшево,
    оставляя энергию на атаку-детонатор ПАР в тот же ход."""
    return Card(
        name="Закипание",
        cost=1,
        card_type="attack",
        description="Урон 5(6). Вешает Мокрый 3(4) и Горение 3(4). "
                    "Сетап для комбо ПАР.",
        effects=[
            DamageEffect(5, 6),
            StatusEffect("wet", 3, 4),
            StatusEffect("ignited", 3, 4),
        ],
        rarity=Rarity.UNCOMMON,
    )
