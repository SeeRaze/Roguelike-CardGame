# core/enemies/elites/spell_eater.py
# Пожиратель Заклинаний — элита-контра колодам-пулемётам.
# Механика: +щит за КАЖДУЮ разыгранную игроком карту. Чем больше дешёвых карт за
# ход, тем толще броня → колоды, спамящие много карт, буксуют. Обход: тяжёлые
# единичные удары, урон сквозь щит (яд/Казнь), Декомпиляция (анти-щит).
import random
from core.enemies.elites.base import EliteBase


class SpellEater(EliteBase):
    """Элита-контра колодам-пулемётам.

    Реакция на розыгрыш (on_card_played): +SHIELD_PER_CARD щита за каждую карту.
    Боевая логика: преимущественно атакует (защита растёт сама от карт игрока).

    Мягкие обходы:
    - Берсерк/бёрст: один тяжёлый удар пробивает накопленный щит
    - Яд/Кровь/Казнь: урон сквозь щит игнорирует броню
    - Декомпиляция (decomp): анти-щит, не даёт набирать броню
    """

    SHIELD_PER_CARD = 4   # +щита за каждую сыгранную игроком карту

    _TITLES = [
        "Пожиратель Заклинаний",
        "Поглотитель Чар",
        "Рунный Голем",
    ]

    @staticmethod
    def random_title() -> str:
        return random.choice(SpellEater._TITLES)

    # ── Хук реакции ──────────────────────────────────────────────────────

    def on_card_played(self, card, player, combat_manager) -> None:
        """Каждая сыгранная игроком карта → +щит. Спам карт кормит его броню."""
        self.gain_shield(self.SHIELD_PER_CARD, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f"[ПОЖИРАТЕЛЬ ЗАКЛИНАНИЙ] +{self.SHIELD_PER_CARD} щита "
                f"за разыгранную карту."
            )

    # ── Боевая логика ───────────────────────────────────────────────────

    def choose_intent(self):
        # Каждый 3-й ход — лёгкая защита, остальные — атака (основная угроза —
        # накопленный от карт игрока щит, поэтому intent простой).
        if self.turn_count % 3 == 2:
            self.set_intent("defend", self.base_test_shield)
        else:
            self.set_intent("attack", self.base_test_damage)
