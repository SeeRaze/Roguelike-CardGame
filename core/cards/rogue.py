# core/cards/rogue.py
# Классовые карты Разбойника. Идентичность — «кровь и темп»: Разбойник копит
# Кровожадность (frenzy) за сыгранные атаки, конвертируя темп в растущий
# dot-урон через Кровотечение (BleedEffect усиливается на player.frenzy).
#
# Движок кат.4: больше атак → выше frenzy → каждое наложение Кровотечения сильнее.
from core.cards.base import Card, DamageEffect
from core.cards.debuff.bleed import BleedEffect
from core.rarity import Rarity


class FrenzyEffect:
    """Накладывает Кровожадность (frenzy) на игрока — +N к будущим Кровотечениям.
    Прямой бустер движка Разбойника (обычно frenzy копится по +1 за атаку)."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.add_status("frenzy", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Кровожадность +{amount} (всего: {player.frenzy})."
            )


def create_bloodlust():
    """«Жажда крови» — Кровожадность 2(3). Чистый энейблер движка: разгоняет
    frenzy без ожидания серии атак."""
    return Card(
        name="Жажда крови",
        cost=1,
        card_type="skill",
        description="Кровожадность 2(3): +N к будущим наложениям Кровотечения.",
        effects=[FrenzyEffect(2, 3)],
        rarity=Rarity.UNCOMMON,
    )


def create_serrated_edge():
    """«Зубчатый клинок» — урон 3(5) + Кровотечение 2(3) + Кровожадность 1.
    Гибрид: бьёт, кровит и растит движок. С накопленным frenzy кровотечение
    конвертирует темп в высокий dot."""
    return Card(
        name="Зубчатый клинок",
        cost=1,
        card_type="attack",
        description="Урон 3(5). Кровотечение 2(3) + Кровожадность 1.",
        effects=[
            DamageEffect(3, 5),
            BleedEffect(2, 3),
            FrenzyEffect(1, 1),
        ],
        rarity=Rarity.RARE,
    )
