# core/enemies/elites/devourer.py
# Пожиратель Скверны — элита-контра DoT/стихийным билдам.
# Механика: в начале хода «пожирает» накопленные НА СЕБЕ стаки DoT (яд+кровь+
# горение), суммарно до DEVOUR_CAP за ход, и конвертирует съеденное в лечение.
# Стакающие отравление/кровь/огонь билды (Друид/Разбойник/Маг) кормят его. Кап →
# тяжёлый DoT всё равно дожимает, но медленнее (контра, не глухая стена).
# Обход: прямой урон/бёрст, перебить капом стаков, союзники-танки.
import random
from core.enemies.elites.base import EliteBase

# Статусы-DoT, которые Пожиратель ест (в порядке приоритета поедания).
_DEVOURABLE = ("legacy", "bleed")


class CorruptionDevourer(EliteBase):
    """Элита-контра DoT/стихийным билдам.

    Начало хода (on_turn_start): суммарно до DEVOUR_CAP стаков яда/крови/горения
    с СЕБЯ → снимает их и лечится на съеденное. Боевая логика — атака/защита.

    Мягкие обходы:
    - Прямой урон/бёрст: не зависит от DoT → кап нерелевантен
    - Превысить кап: стакать DoT быстрее, чем DEVOUR_CAP/ход
    - Призыватель: союзники танкуют, пока чистый урон идёт
    """

    DEVOUR_CAP = 8   # макс. стаков DoT, поедаемых (и лечащих) за один ход

    _TITLES = [
        "Пожиратель Скверны",
        "Гнилостный Чревоугодник",
        "Поглотитель Порчи",
    ]

    @staticmethod
    def random_title() -> str:
        return random.choice(CorruptionDevourer._TITLES)

    # ── Хук реакции ──────────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Пожирает свои DoT-стаки (до cap), конвертирует в лечение."""
        budget = self.DEVOUR_CAP
        consumed = 0
        for key in _DEVOURABLE:
            if budget <= 0:
                break
            have = self.get_status(key)
            if have <= 0:
                continue
            take = min(have, budget)
            self.set_status(key, have - take)
            budget -= take
            consumed += take

        if consumed > 0:
            self.heal(consumed, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f"[ПОЖИРАТЕЛЬ СКВЕРНЫ] Пожирает {consumed} порчи "
                    f"и лечится на {consumed} HP."
                )

    # ── Боевая логика ───────────────────────────────────────────────────

    def choose_intent(self):
        if self.turn_count % 3 == 2:
            self.set_intent("defend", self.base_test_shield)
        else:
            self.set_intent("attack", self.base_test_damage)
