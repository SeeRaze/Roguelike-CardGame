# core/enemies/elites/plague.py
# Чумной Гнойник — элита-контра обороне.
# Механика (С58-фолд): в начале своего хода вешает Legacy-код игроку; ЕСЛИ у игрока
# есть щит — наложение УДВАИВАЕТСЯ И добавляется Токс, отчего Legacy ПРОБИВАЕТ щит
# (Кислотный дождь). Черепаха-билд под бронёй копит разъедающий код. Обход:
# агрессия (не сидеть под щитом), снятие/игнор DoT, бёрст.
import random
from core.enemies.elites.base import EliteBase


class PlaguePustule(EliteBase):
    """Элита-контра обороне.

    Начало хода (on_turn_start): +PLAGUE_POISON Legacy-кода игроку; при наличии щита
    у игрока — ×2 И +Токс (щит не спасает, а провоцирует Кислотный дождь — Legacy
    сквозь броню). Боевая логика — атака/защита; основная угроза — стакающийся DoT.

    Мягкие обходы:
    - Агрессивные билды: не накапливают щит → одинарный Legacy без пробития, успевают убить
    - Снятие/блок стихий (Маг): гасит DoT
    - Бёрст/высокий DPS: убивают до того, как DoT станет смертельным
    """

    PLAGUE_POISON = 3   # базовое наложение Legacy-кода за ход (×2 +Токс при щите)
    PLAGUE_TOX = 2      # стаки Токса при щите → Legacy пробивает броню (Кислотный дождь)

    _TITLES = [
        "Чумной Гнойник",
        "Носитель Мора",
        "Гнилостный Раздуватель",
    ]

    @staticmethod
    def random_title() -> str:
        return random.choice(PlaguePustule._TITLES)

    # ── Хук реакции ──────────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Вешает Legacy-код игроку. Щит игрока удваивает наложение И добавляет
        Токс → Legacy пробивает щит (Кислотный дождь). Контра обороне."""
        amount = self.PLAGUE_POISON
        shielded = getattr(player, "shield", 0) > 0
        if shielded:
            amount *= 2
            player.add_status("legacy", amount, combat_manager)
            player.add_status("tox", self.PLAGUE_TOX, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f"[ЧУМНОЙ ГНОЙНИК] Ваш щит вскипает кислотой: +{amount} "
                    f"Legacy-кода (×2) СКВОЗЬ броню."
                )
        else:
            player.add_status("legacy", amount, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f"[ЧУМНОЙ ГНОЙНИК] +{amount} Legacy-кода."
                )

    # ── Боевая логика ───────────────────────────────────────────────────

    def choose_intent(self):
        # Чередует защиту и атаку; основной урон наносит яд из on_turn_start.
        if self.turn_count % 2 == 0:
            self.set_intent("attack", self.base_test_damage)
        else:
            self.set_intent("defend", self.base_test_shield)
