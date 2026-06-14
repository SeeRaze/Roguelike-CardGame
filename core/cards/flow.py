# core/cards/flow.py
# Движок «ПОТОК» — НЕЙТРАЛЬНАЯ темпо-механика (эффект-кирпич `FlowEffect`).
# Стихия «Воздух» вырезана (канон = 6 стихий, не расширяем), но сам движок Потока
# СОХРАНЁН как переиспользуемый кирпич: при наполнении общего пула (Блок 2) его можно
# органично внедрить в нейтральную карту. Пока КАРТ с Потоком нет — живёт только эффект.
#
# Поток — НЕ статус существа, а эффект: при розыгрыше карты снижает стоимость случайной
# карты в руке на 1 (до конца хода) через `temp_cost`; `DeckManager.discard_hand`
# чистит temp_cost в конце хода.
import random


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


def create_in_the_flow():
    """«В потоке» — оживляет движок Потока (С65, Блок 2): cost0 темпо-карта. Войти в
    поток = удешевить 2(3) случайные карты в руке на 1 + добрать 1. Нейтральный
    носитель FlowEffect (после выреза ВОЗДУХА движок жил без карт). LOCKED."""
    from core.cards.base import Card, DrawEffect
    from core.rarity import Rarity
    return Card(
        name="В потоке",
        cost=0,
        card_type="skill",
        description="Поток 2(3): удешевляет случайные карты в руке на 1. Добор 1.",
        effects=[
            FlowEffect(2, 3),
            DrawEffect(1, 1),
        ],
        rarity=Rarity.UNCOMMON,
    )
