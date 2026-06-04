# core/cards/air.py
# Карты стихии «Воздух» (механика Поток). Поток — НЕ статус существа, а эффект-
# кирпич `FlowEffect`: при розыгрыше карты он снижает стоимость случайной карты
# в руке на 1 (до конца хода). Переиспользует систему `temp_cost` (та же, что у
# скидки Разбойника); `DeckManager.discard_hand` чистит temp_cost в конце хода.
#
# Архетип — ТЕМПО/ЭНЕРГИЯ: дешёвые карты, каждая удешевляет следующую, позволяя
# разыграть за ход больше, чем хватает энергии.
#
# Трио:
#   «Порыв ветра»     — дешёвый темпо-удар: урон + удешевление.
#   «Восходящий поток» — чистый энейблер: 2(3) удешевления за карту.
#   «Вихрь»           — гибрид: крупный урон + удешевление.
import random

from core.cards.base import Card, DamageEffect
from core.rarity import Rarity


class FlowEffect:
    """Поток: снижает `temp_cost` на 1 у `count` случайных карт в руке.
    base_val/upgrade_val — сколько удешевлений сделать. Разыгрываемую карту
    исключаем (она ещё в руке во время apply — см. CombatManager._card_being_played).
    Скидка живёт до конца хода: discard_hand() сбрасывает temp_cost."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None:
            return
        deck = getattr(combat_manager, 'deck_manager', None)
        if deck is None:
            return

        count = self.upgrade_val if is_upgraded else self.base_val
        being_played = getattr(combat_manager, '_card_being_played', None)

        for _ in range(count):
            candidates = [
                c for c in deck.hand
                if c is not being_played
                and getattr(c, 'temp_cost', c.cost) > 0
            ]
            if not candidates:
                break
            card = random.choice(candidates)
            current = getattr(card, 'temp_cost', card.cost)
            card.temp_cost = max(0, current - 1)
            combat_manager.add_log_message(
                f" -> Поток: {card.name} дешевле на 1 (={card.temp_cost})."
            )


def create_gust():
    """«Порыв ветра» — урон 4(6) + Поток (1 удешевление). Дешёвый темпо-удар."""
    return Card(
        name="Порыв ветра",
        cost=1,
        card_type="attack",
        description="Урон 4(6). Поток: случайная карта в руке дешевле на 1.",
        effects=[
            DamageEffect(4, 6),
            FlowEffect(1, 1),
        ],
    )


def create_updraft():
    """«Восходящий поток» — Поток ×2(3). Чистый энейблер темпа за 1 энергии:
    удешевляет 2(3) случайных карты, раскручивая ход."""
    return Card(
        name="Восходящий поток",
        cost=1,
        card_type="skill",
        description="Поток ×2(3): столько случайных карт в руке дешевле на 1.",
        effects=[
            FlowEffect(2, 3),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_whirlwind():
    """«Вихрь» — урон 7(9) + Поток (удешевление 1(2)). Гибрид: бьёт и разгоняет ход."""
    return Card(
        name="Вихрь",
        cost=2,
        card_type="attack",
        description="Урон 7(9). Поток: удешевляет 1(2) случайных карты в руке на 1.",
        effects=[
            DamageEffect(7, 9),
            FlowEffect(1, 2),
        ],
        rarity=Rarity.UNCOMMON,
    )
