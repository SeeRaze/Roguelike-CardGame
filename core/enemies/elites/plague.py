# core/enemies/elites/plague.py
# Чумной Гнойник — элита-контра обороне.
# Механика: в начале своего хода вешает Яд игроку; ЕСЛИ у игрока есть щит — яд
# УДВАИВАЕТСЯ. Яд тикает сквозь щит → черепаха-билд, сидящий под бронёй, копит
# отравление. Обход: агрессия (не сидеть под щитом), снятие/игнор яда, бёрст.
import random
from core.enemies.elites.base import EliteBase


class PlaguePustule(EliteBase):
    """Элита-контра обороне.

    Начало хода (on_turn_start): +PLAGUE_POISON Яда игроку; при наличии щита у
    игрока — ×2 (щит не спасает от яда, а провоцирует его). Боевая логика —
    атака/защита; основная угроза — стакающийся яд.

    Мягкие обходы:
    - Агрессивные билды: не накапливают щит → одинарный яд, успевают убить
    - Снятие/блок стихий (Маг): гасит яд
    - Бёрст/высокий DPS: убивают до того, как яд станет смертельным
    """

    PLAGUE_POISON = 3   # базовое наложение Яда за ход (×2 при щите игрока)

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
        """Вешает Яд игроку. Щит игрока удваивает наложение (контра обороне)."""
        amount = self.PLAGUE_POISON
        shielded = getattr(player, "shield", 0) > 0
        if shielded:
            amount *= 2
        player.add_status("poison", amount, combat_manager)
        if combat_manager:
            if shielded:
                combat_manager.add_log_message(
                    f"[ЧУМНОЙ ГНОЙНИК] Ваш щит вскипает гноем: +{amount} Яда (×2)."
                )
            else:
                combat_manager.add_log_message(
                    f"[ЧУМНОЙ ГНОЙНИК] +{amount} Яда."
                )

    # ── Боевая логика ───────────────────────────────────────────────────

    def choose_intent(self):
        # Чередует защиту и атаку; основной урон наносит яд из on_turn_start.
        if self.turn_count % 2 == 0:
            self.set_intent("attack", self.base_test_damage)
        else:
            self.set_intent("defend", self.base_test_shield)
