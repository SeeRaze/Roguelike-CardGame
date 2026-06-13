# core/enemies/elites/devourer.py
# Авторефакторинг — элита-контра DoT/стихийным билдам.
# Механика: в начале хода «вычищает» накопленные НА СЕБЕ стаки Legacy-кода,
# суммарно до DEVOUR_CAP за ход, и конвертирует вычищенное в лечение (рефакторинг
# техдолга = система здоровее). Стакающие Legacy-DoT билды кормят его. Кап →
# тяжёлый DoT всё равно дожимает, но медленнее (контра, не глухая стена).
# Обход: прямой урон/бёрст, перебить капом стаков, союзники-танки.
# Класс-идентификатор CorruptionDevourer сохранён (инфра/реестр).
import random
from core.enemies.elites.base import EliteBase

# Статусы-DoT, которые Авторефакторинг вычищает (в порядке приоритета).
_DEVOURABLE = ("legacy",)


class CorruptionDevourer(EliteBase):
    """Элита-контра DoT/стихийным билдам («Авторефакторинг»).

    Начало хода (on_turn_start): суммарно до DEVOUR_CAP стаков Legacy-кода с СЕБЯ
    → снимает их и лечится на вычищенное (рефакторинг убирает техдолг). Боевая
    логика — атака/защита.

    Мягкие обходы:
    - Прямой урон/бёрст: не зависит от DoT → кап нерелевантен
    - Превысить кап: стакать Legacy быстрее, чем DEVOUR_CAP/ход
    - Союзники-танки: держат удар, пока чистый урон идёт
    """

    DEVOUR_CAP = 8   # макс. стаков Legacy, вычищаемых (и лечащих) за один ход

    _TITLES = [
        "Авторефакторинг",
        "Линтер-автофикс",
        "Чистильщик кода",
    ]

    @staticmethod
    def random_title() -> str:
        return random.choice(CorruptionDevourer._TITLES)

    # ── Хук реакции ──────────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Вычищает свои Legacy-стаки (до cap), конвертирует в лечение."""
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
                    f"[АВТОРЕФАКТОРИНГ] Вычищает {consumed} legacy-кода "
                    f"и лечится на {consumed} HP."
                )

    # ── Боевая логика ───────────────────────────────────────────────────

    def choose_intent(self):
        if self.turn_count % 3 == 2:
            self.set_intent("defend", self.base_test_shield)
        else:
            self.set_intent("attack", self.base_test_damage)
