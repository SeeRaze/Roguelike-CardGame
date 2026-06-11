# core/enemies/bosses/archivist.py
# Архивариус Забвения — босс этажа 40. Ворота: чистота колоды.
# Механика: +щит за каждую сыгранную карту + Токсичность за толстую колоду.
# Классы без утилизации мусора получают штраф; «тонкие» билды проходят легче.
import random
from core.enemies.bosses.base import BossBase


class OblivionArchivist(BossBase):
    """Босс этажа 40 — проверка чистоты колоды.

    Реакция на розыгрыш (on_card_played): +2 щита за каждую карту (+3 в фазе 2).
    Начало хода (on_turn_start): если суммарный размер колоды (стопка + рука +
    сброс) > 15 — +1 Токсичность игроку. В фазе 2 Токсичность накладывается всегда.

    Мягкие обходы:
    - Маг: естественно тонкая колода (меньше Shield-накачки)
    - Воин/Берсерк: персистентный щит / Казнь игнорируют вражеский щит
    - Союзники танкуют, DPS не снижается от Токсичности
    """

    PHASE_THRESHOLD = 0.5
    SHIELD_PER_CARD_P1 = 2   # +щита за карту в фазе 1
    SHIELD_PER_CARD_P2 = 3   # +щита за карту в фазе 2
    DECK_SIZE_LIMIT   = 15   # порог «толстой» колоды

    _TITLES = [
        "Архивариус Забвения",
        "Писец Пустоты",
        "Хранитель Свитков",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)

    # ── Хуки реакций ─────────────────────────────────────────────────────

    def on_card_played(self, card, player, combat_manager) -> None:
        """Каждая сыгранная карта → +щит боссу. Плотные колоды кормят его."""
        gain = self.SHIELD_PER_CARD_P2 if self.current_phase == 2 \
               else self.SHIELD_PER_CARD_P1
        self.gain_shield(gain, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f"[АРХИВАРИУС] +{gain} щита за розыгрыш карты."
            )

    def on_turn_start(self, player, combat_manager) -> None:
        """Толстая колода (или фаза 2) → Токсичность игроку."""
        if combat_manager:
            dm = combat_manager.deck_manager
            # Сумма: стопка + рука + сброс. Изгнанные карты вне боя — не считаем.
            deck_size = len(dm.draw_pile) + len(dm.hand) + len(dm.discard_pile)
        else:
            deck_size = 99  # без боя (тесты) — считаем толстой

        if deck_size > self.DECK_SIZE_LIMIT or self.current_phase == 2:
            player.tox += 1
            if combat_manager:
                if deck_size > self.DECK_SIZE_LIMIT:
                    combat_manager.add_log_message(
                        f"[АРХИВАРИУС] Ваша толстая колода ({deck_size} карт) "
                        f"ослабляет вас: +1 Токсичность."
                    )
                else:
                    combat_manager.add_log_message(
                        "[АРХИВАРИУС] Близость забвения ослабляет вас: +1 Токсичность."
                    )

    # ── Боевая логика ───────────────────────────────────────────────────

    @staticmethod
    def random_title() -> str:
        return random.choice(OblivionArchivist._TITLES)

    def choose_intent(self):
        step = self.turn_count % 3
        if step == 0:
            self.set_intent("debuff", 1)            # +1 Токсичность
        elif step == 1:
            self.set_intent("defend", self.base_test_shield)
        else:
            self.set_intent("attack", self.base_test_damage)
