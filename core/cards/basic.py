from core.cards.base import (
    Card, DamageEffect, ShieldEffect, DetonateEffect, TacticalMoveEffect,
)
from core.rarity import Rarity

def create_strike():
    return Card("Удар", 1, "attack", "Наносит 6 (9) чистейшего урона.", [DamageEffect(6, 9)])

def create_defend():
    return Card("Защита", 1, "defense", "Дает 5 (8) базового щита.", [ShieldEffect(5, 8)])

def create_heavy_blade():
    return Card("Тяжелый Клинок", 2, "attack", "Мощный рубящий удар на 14 (20) урона.", [DamageEffect(14, 20)])

def create_iron_wall():
    return Card("Железная Стена", 2, "defense", "Непробиваемый барьер на 12 (18) щита.", [ShieldEffect(12, 18)])

def create_catalyst():
    """«Катализатор» — нейтральный универсальный детонатор: подрывает любые готовые
    стихийные детонации на цели (Электро-взрыв, Термовзрыв, Лава, Кислота — см.
    core/DetonationRegistry.py). Сам урона не наносит — это «спусковой крючок» комбо."""
    return Card(
        "Катализатор", 1, "skill",
        "Детонация: подрывает готовые стихийные комбо на цели.",
        [DetonateEffect()],
        rarity=Rarity.UNCOMMON,
    )

def create_tactical_reposition():
    """«Перестроение» — носитель эффекта [Tactical_Move]: атомарно переворачивает
    СТРОЙ партии (фронт↔тыл). Делает позиционку управляемой ценой ДЕЙСТВИЯ (карта),
    а не бесплатной кнопкой. НЕ в случайном пуле наград (catalog) — осознанная
    выдача/комбо-механика; бот её не драфтит → baseline безопасен."""
    return Card(
        "Перестроение", 1, "skill",
        "Манёвр: меняет местами фронт и тыл вашей партии.",
        [TacticalMoveEffect()],
        rarity=Rarity.UNCOMMON,
    )

