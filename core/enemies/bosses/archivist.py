# core/enemies/bosses/archivist.py
# Скоуп-крип — босс этажа 40. Барьер: разрастание объёма проекта.
# Механика: +щит за каждую сыгранную карту (каждая «фича» раздувает скоуп) +
# Токсичность за толстую колоду. Раздутые билды штрафуются; «тонкие» проходят легче.
# Класс-идентификатор OblivionArchivist сохранён (инфра/реестр).
import random
from core.enemies.bosses.base import BossBase


class OblivionArchivist(BossBase):
    """Босс этажа 40 — барьер разрастания объёма («Скоуп-крип»).

    Реакция на розыгрыш (on_card_played): +2 щита за каждую карту (+3 в фазе 2) —
    каждая добавленная «фича» раздувает скоуп. Начало хода (on_turn_start): если
    суммарный размер колоды (стопка + рука + сброс) > 15 — +1 Токсичность игроку
    (раздутые требования душат). В фазе 2 Токсичность накладывается всегда.

    Мягкие обходы:
    - Вайб-кодер: естественно тонкая колода (меньше Shield-накачки)
    - Тестировщик/Стажёр: персистентный щит / Казнь игнорируют вражеский щит
    - Союзники танкуют, DPS не снижается от Токсичности
    """

    PHASE_THRESHOLD = 0.5
    SHIELD_PER_CARD_P1 = 2   # +щита за карту в фазе 1
    SHIELD_PER_CARD_P2 = 3   # +щита за карту в фазе 2
    DECK_SIZE_LIMIT   = 15   # порог «раздутой» колоды

    _TITLES = [
        "Скоуп-крип",
        "Расползание требований",
        "Раздутый бэклог",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)

    # ── Хуки реакций ─────────────────────────────────────────────────────

    def on_card_played(self, card, player, combat_manager) -> None:
        """Каждая сыгранная карта → +щит боссу. Каждая «фича» раздувает скоуп."""
        gain = self.SHIELD_PER_CARD_P2 if self.current_phase == 2 \
               else self.SHIELD_PER_CARD_P1
        self.gain_shield(gain, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f"[СКОУП-КРИП] +{gain} щита: ещё одна фича раздувает объём."
            )

    def on_turn_start(self, player, combat_manager) -> None:
        """Раздутая колода (или фаза 2) → Токсичность игроку."""
        if combat_manager:
            dm = combat_manager.deck_manager
            # Сумма: стопка + рука + сброс. Изгнанные карты вне боя — не считаем.
            deck_size = len(dm.draw_pile) + len(dm.hand) + len(dm.discard_pile)
        else:
            deck_size = 99  # без боя (тесты) — считаем раздутой

        if deck_size > self.DECK_SIZE_LIMIT or self.current_phase == 2:
            player.tox += 1
            if combat_manager:
                if deck_size > self.DECK_SIZE_LIMIT:
                    combat_manager.add_log_message(
                        f"[СКОУП-КРИП] Раздутый объём ({deck_size} карт) "
                        f"душит вас: +1 Токсичность."
                    )
                else:
                    combat_manager.add_log_message(
                        "[СКОУП-КРИП] Требования расползаются: +1 Токсичность."
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
