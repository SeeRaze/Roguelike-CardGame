# managers/balance/economy.py
# Шаг №6 фреймворка баланса (balance-curve-framework): «Экономика/дроп —
# регулятор скорости сборки компаунда». До этого симулятор НЕ видел золото и
# удаление карт (runner: «Удаление/апгрейд не моделируем») → прореживание колоды
# нельзя было крутить как рычаг.
#
# Объём (решение пользователя, C3): моделируем ТОЛЬКО золото + удаление.
# Покупка карт во многом дублирует уже существующий драфт → не моделируем
# (минимум дисперсии, чистейший сигнал). Трата — РАЗ В АКТ (рядом с костром).
#
# Удаление = главный НОВЫЙ рычаг: прореживание слабейших карт ускоряет добор
# ключевых (компаунд собирается быстрее). Параллель к BotPolicy: политика
# между-боевых экономических решений, ВЫКЛючена по умолчанию в runner
# (economy=None) — A/B «с экономикой / без» остаётся чистым.
import random

from managers.balance.builds import _card_score, _card_themes, _deck_themes


def gold_reward(floor: int, is_elite: bool, has_crown: bool) -> int:
    """Золото за выжитый бой — зеркало RewardManager.build_rewards (та же
    формула). «Проклятая Корона» обнуляет золото (осознанный размен: урон вместо
    экономики) → у Корона-билдов нет средств на прореживание (важная синергия)."""
    if has_crown:
        return 0
    gold = random.randint(20, 35) + floor * 3
    if is_elite:
        gold = int(gold * 1.5)
    return gold


class EconomyPolicy:
    """Политика экономики бота: копит золото после боёв, раз в акт тратит его на
    удаление слабейших карт. Константы класса = РЫЧАГИ скорости прореживания
    (крутить для тюнинга «гонки» сборки компаунда).

    Без состояния (золото/removal_count живут на gm) → один инстанс безопасно
    переиспользуется для обеих метрик (wall и ceiling)."""

    # Сколько удалений максимум за один акт. Главный рычаг скорости прореживания:
    # 1 = осторожный темп (один магазин на акт, одно удаление), больше = агрессивнее.
    MAX_REMOVALS_PER_ACT = 1
    # Не прореживать колоду ниже этого размера (иначе нечем играть).
    MIN_DECK_SIZE = 5

    def on_combat_won(self, gm, floor: int, is_elite: bool = False) -> None:
        """Начислить золото за выжитый бой (зеркало распределения наград)."""
        gm.player_gold += gold_reward(floor, is_elite, _has_crown(gm))

    def between_acts(self, gm, deck: list, class_name: str) -> None:
        """Раз в акт: пока по карману и колода не оголена — удалять слабейшую
        (предпочтительно нетематичную) карту. Цена удаления растёт с каждым
        разом (gm.get_removal_price) → траты сами себя ограничивают."""
        themes = _deck_themes(deck)
        for _ in range(self.MAX_REMOVALS_PER_ACT):
            if len(deck) <= self.MIN_DECK_SIZE:
                break
            price = gm.get_removal_price()
            if gm.player_gold < price:
                break
            target = _removal_target(deck, themes)
            if target is None:
                break
            deck.remove(target)
            gm.player_gold   -= price
            gm.removal_count += 1


def _has_crown(gm) -> bool:
    return any(r.name == "Проклятая Корона" for r in gm.relics)


def _removal_target(deck: list, themes: set):
    """Кандидат на удаление = слабейшая карта (по _card_score); при РАВНОЙ силе
    режем нетематичную (не ломаем архетип). Сила — первичный ключ: прореживание
    чаффа всегда выгодно в игре с лимитом добора, поэтому порог не нужен —
    режем самое слабое звено."""
    if not deck:
        return None

    def keyf(card):
        on_theme = 1 if (_card_themes(card) & themes) else 0
        return (_card_score(card), on_theme)

    return min(deck, key=keyf)
