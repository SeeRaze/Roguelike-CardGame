# core/enemies/bosses/keeper.py
# Цейтнот — босс этажа 80. Барьер: уходящее время.
# Механика: растущий заряд времени (урон ×) + перенос срока — отхил 15% max HP
# каждые 3 хода. Без персистентного слоя (форж-теги/грейд) DPS не перегоняет
# «перенос срока». Класс-идентификатор TimeKeeper сохранён (инфра/реестр).
import random
from core.enemies.base import IntentHeal
from core.enemies.bosses.base import BossBase


class TimeKeeper(BossBase):
    """Босс этажа 80 — уходящее время («Цейтнот»).

    Каждый ход: _temporal_charge++ (срок поджимает). Урон атаки =
    base × (1 + 0.15 × charge). Каждый 3-й ход: Перенос срока — отхил 15% max HP.
    Фаза 2: +2 Токсичность игроку при каждом переносе.

    Без персистентных множителей (Повышение грейда ×1.25^N, форж-теги ×mult)
    DPS игрока не перегоняет «перенос срока» → бой затягивается → заряд растёт →
    смерть. С персистентным слоем: burst × отхил → победа.

    Мягкие обходы:
    - Все классы с Повышение грейда: ×1.25^4 ≈ ×2.44 урона
    - Форж-теги (×mult слоты): пробивают перенос
    - Стажёр: игнорирует Токсичность через Казнь на лоу-HP
    """

    PHASE_THRESHOLD = 0.5
    TEMPORAL_DMG_PER_CHARGE = 0.15   # +15% урона за каждый заряд (срок поджимает)
    TEMPORAL_HEAL_PCT = 0.15         # 15% max HP за Перенос срока

    _TITLES = [
        "Цейтнот",
        "Горящие сроки",
        "Код-фриз",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        self._temporal_charge = 0

    # ── Заряд времени ────────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Каждый ход: заряд +1. Урон растёт, бой затягивать нельзя."""
        self._temporal_charge += 1
        if combat_manager:
            combat_manager.add_log_message(
                f"[ЦЕЙТНОТ] Срок поджимает: заряд {self._temporal_charge}."
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
            # Перенос срока: отхил + (фаза 2) Токсичность.
            heal_amount = int(self.max_hp * self.TEMPORAL_HEAL_PCT)
            self.set_intent("heal", heal_amount)

    def execute_intent(self, player, combat_manager=None):
        """Переопределено для Переноса срока: хил + опц. Токсичность в фазе 2."""

        intent = self.intent

        if isinstance(intent, IntentHeal):
            self.turn_count += 1
            heal_amount = intent.value
            # Запомнить фазу ДО хила: иначе хил может вытолкнуть из фазы 2
            # и Токсичность не наложится.
            was_phase2 = (self.current_phase == 2)
            self.heal(heal_amount, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f"[ЦЕЙТНОТ] Перенос срока: +{heal_amount} HP."
                )
            # Фаза 2: +2 Токсичность игроку
            if was_phase2:
                player.tox += 2
                if combat_manager:
                    combat_manager.add_log_message(
                        "[ЦЕЙТНОТ] Перенос срока выматывает вас: +2 Токсичность."
                    )
        else:
            # Стандартная обработка для attack/defend
            super().execute_intent(player, combat_manager)
