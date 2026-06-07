# core/enemies/bosses/keeper.py
# Хранитель Времени — босс этажа 80. Ворота: персистентный скейлинг.
# Механика: растущий временной заряд (урон ×) + отхил 15% max HP каждые 3 хода.
# Без персистентного слоя (Корона/форж-теги) DPS не перегоняет отхил.
import random
from core.enemies.base import IntentHeal
from core.enemies.bosses.base import BossBase


class TimeKeeper(BossBase):
    """Босс этажа 80 — проверка персистентного/run-long скейлинга.

    Каждый ход: _temporal_charge++. Урон атаки = base × (1 + 0.15 × charge).
    Каждый 3-й ход: Temporal Shift — отхил 15% max HP. Фаза 2: +2 Слабость
    игроку при каждом Shift.

    Без персистентных множителей (Корона Вознесения ×1.25^N, форж-теги ×mult)
    DPS игрока не перегоняет отхил → бой затягивается → заряд растёт → смерть.
    С персистентным слоем: burst × отхил → победа.

    Мягкие обходы:
    - Все классы с Корона Вознесения: ×1.25^4 ≈ ×2.44 урона
    - Форж-теги (×mult слоты): пробивают отхил
    - Берсерк: игнорирует Слабость через Казнь на лоу-HP
    """

    PHASE_THRESHOLD = 0.5
    TEMPORAL_DMG_PER_CHARGE = 0.15   # +15% урона за каждый заряд
    TEMPORAL_HEAL_PCT = 0.15         # 15% max HP за Temporal Shift

    _TITLES = [
        "Хранитель Времени",
        "Повелитель Мгновений",
        "Страж Вечности",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        self._temporal_charge = 0

    # ── Временной заряд ──────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Каждый ход: заряд +1. Урон растёт, бой затягивать нельзя."""
        self._temporal_charge += 1
        if combat_manager:
            combat_manager.add_log_message(
                f"[ХРАНИТЕЛЬ] Временной заряд: {self._temporal_charge}."
            )

    # ── Боевая логика ───────────────────────────────────────────────────

    @staticmethod
    def random_title() -> str:
        return random.choice(TimeKeeper._TITLES)

    def choose_intent(self):
        step = self.turn_count % 3
        dmg_mult = 1.0 + self.TEMPORAL_DMG_PER_CHARGE * self._temporal_charge

        if step == 0:
            self.set_intent("attack", int(self.base_test_damage * dmg_mult))
        elif step == 1:
            self.set_intent("defend", self.base_test_shield)
        else:
            # Temporal Shift: отхил + (фаза 2) Слабость.
            heal_amount = int(self.max_hp * self.TEMPORAL_HEAL_PCT)
            self.set_intent("heal", heal_amount)

    def execute_intent(self, player, combat_manager=None):
        """Переопределено для Temporal Shift: хил + опц. Слабость в фазе 2."""

        intent = self.intent

        if isinstance(intent, IntentHeal):
            self.turn_count += 1
            heal_amount = intent.value
            # Запомнить фазу ДО хила: иначе хил может вытолкнуть из фазы 2
            # и Weak не наложится.
            was_phase2 = (self.current_phase == 2)
            self.heal(heal_amount, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f"[ХРАНИТЕЛЬ] Временной сдвиг: +{heal_amount} HP."
                )
            # Фаза 2: +2 Слабость игроку
            if was_phase2:
                player.weak += 2
                if combat_manager:
                    combat_manager.add_log_message(
                        "[ХРАНИТЕЛЬ] Временной сдвиг искажает вас: +2 Слабость."
                    )
        else:
            # Стандартная обработка для attack/defend
            super().execute_intent(player, combat_manager)
