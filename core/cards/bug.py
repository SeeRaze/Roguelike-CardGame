# core/cards/bug.py
# СЛОЙ БАГОВ / ТЕХНИЧЕСКОГО ДОЛГА (ярус 1, минимальная форма — С59).
#
# Баг — несыгрываемая карта-долг (модель StS Wound): занимает слот руки, дилютит
# добор, но play_card_by_index её НЕ разыгрывает (флаг unplayable). Ярус 1 = ЧИСТАЯ
# ДИЛЮЦИЯ без укуса (онбординг); −HP/−энергия = ярус 2+.
#
# Три глагола слоя (ярус 1 = два из трёх в коробке):
#   ACCRUE — мощь оставляет долг: сильная карта навешивает Баг в КОЛОДУ ЗАБЕГА
#            (gm.current_deck — персист между боями, настоящий долг). AccrueBugEffect.
#   DEBUG  — counterplay: вычистить Баг (из руки + перманентно из колоды). DebugBugEffect.
#   REFACTOR (баги → ресурс) — ярус 2+, тут нет.
#
# Баг НЕ драфтится (вне GENERIC_FACTORIES/наград) — только навешивается через ACCRUE.
# Зарегистрирован в RAW_FACTORIES (card_id='bug') ради сейв/загрузки current_deck.
from core.cards.base import Card
from core.rarity import Rarity


def create_bug():
    """«Баг» — несыгрываемая карта-долг (ярус 1). Чистая дилюция: занимает слот руки,
    но сыграть нельзя. Counterplay — DEBUG (карта «Код-ревью»). Персист в gm.current_deck
    (живёт между боями, пока не задебажишь)."""
    return Card(
        name="Баг",
        cost=0,
        card_type="status",
        description="Несыгрываемо. Засоряет руку. Задебажь (Код-ревью), чтобы убрать.",
        effects=[],
        rarity=Rarity.COMMON,
        unplayable=True,
    )


class AccrueBugEffect:
    """ACCRUE — мощь оставляет долг: навесить N Багов в КОЛОДУ ЗАБЕГА (gm.current_deck).
    Долг АВТОРСКИЙ (рискнул ради силы), персистит между боями: всплывёт в добор при
    reset_deck следующего боя. NO-OP без gm/current_deck (синтетический бой в тестах)."""

    def __init__(self, count=1, upgrade_count=None):
        self.count = count
        # Прокачка пока не меняет число долга (баланс — капстоун); upgrade_count
        # принят ради единообразия фабрик/будущей ковки.
        self.upgrade_count = upgrade_count if upgrade_count is not None else count

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None:
            return
        gm = getattr(combat_manager, 'gm', None)
        deck = getattr(gm, 'current_deck', None) if gm else None
        if deck is None:
            return
        n = self.upgrade_count if is_upgraded else self.count
        for _ in range(n):
            deck.append(create_bug())
        combat_manager.add_log_message(
            f" -> [ДОЛГ] Навешано Багов: {n} (всплывут в колоде забега)."
        )


class DebugBugEffect:
    """DEBUG — counterplay слоя багов: изгнать до N Багов из РУКИ и удалить их
    ПЕРМАНЕНТНО из колоды забега (gm.current_deck), чтобы долг не вернулся следующим
    боем. Бьёт только по картам-Багам (unplayable); обычные карты не трогает.
    NO-OP, если Багов в руке нет."""

    def __init__(self, count=1, upgrade_count=None):
        self.count = count
        self.upgrade_count = upgrade_count if upgrade_count is not None else count

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None:
            return
        n = self.upgrade_count if is_upgraded else self.count
        hand = combat_manager.deck_manager.hand
        gm = getattr(combat_manager, 'gm', None)
        deck = getattr(gm, 'current_deck', None) if gm else None

        removed = 0
        for card in list(hand):
            if removed >= n:
                break
            if getattr(card, 'unplayable', False):
                hand.remove(card)
                # Перманентное удаление из колоды забега: иначе reset_deck вернул бы
                # Баг в добор следующего боя (изгнание не годится — exile_pile тоже
                # возвращается в пул). Тот же объект в руке и в current_deck.
                if deck is not None and card in deck:
                    deck.remove(card)
                removed += 1

        if removed > 0:
            combat_manager.add_log_message(
                f" -> [DEBUG] Задебажено Багов: {removed} (удалены из колоды забега)."
            )
        else:
            combat_manager.add_log_message(" -> [DEBUG] Багов в руке нет.")
