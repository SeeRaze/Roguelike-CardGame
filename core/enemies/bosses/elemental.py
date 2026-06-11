# core/enemies/bosses/elemental.py
# Элементаль Пустоты — босс этажа 60. Ворота: мультипликативный урон.
# Механика: Щит Пустоты (поглощает flat-урон) чередуется с фазой Уязвимости
# (×1.5 входящего урона). Только burst-билды пробивают щит и используют окно.
import random
from core.enemies.bosses.base import BossBase


class VoidElemental(BossBase):
    """Босс этажа 60 — проверка мультипликативного урона.

    Цикл из двух фаз: Щит Пустоты (босс набирает щит, атакует слабо) →
    Уязвимость (босс получает ×1.5 урона, атакует сильно). Фаза 1 включает
    ещё и defend; фаза 2 короче и агрессивнее.

    Щит Пустоты растёт с этажом: VOID_SHIELD_BASE + floor // 10. На этаже 60
    это ~14 щита за фазу — flat-DPS билды не пробивают, а burst (комбо/
    детонации/форж-теги) проходят и бьют ×1.5 в окно Уязвимости.

    Мягкие обходы:
    - Все классы с кат.4 движками: форж-теги ×mult, комбо, детонации
    - Маг: Эхо × детонация = burst в окно Уязвимости
    - Союзники дают стабильный DPS в обе фазы
    """

    PHASE_THRESHOLD = 0.4
    VOID_SHIELD_BASE = 8   # базовый щит Пустоты (+ floor // 10)

    _TITLES = [
        "Элементаль Пустоты",
        "Ядро Бездны",
        "Искажённый Элементаль",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        # spawn_floor ставится EnemySpawner'ом после конструктора.
        # По умолчанию 60 (типичный floor для этого босса).
        self.spawn_floor = 60
        # Флаг: босс в фазе Уязвимости (игрок бьёт ×1.5).
        self._exposed = False

    # ── Вычисляемые свойства ─────────────────────────────────────────────

    @property
    def void_shield_amount(self) -> int:
        """Размер Щита Пустоты в текущем бою (растёт с этажом)."""
        return self.VOID_SHIELD_BASE + self.spawn_floor // 10

    # ── Хук начала хода ──────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Определить фазу цикла: Щит Пустоты или Уязвимость."""
        phase = self.current_phase
        cycle_len = 2 if phase == 2 else 3
        pos = self.turn_count % cycle_len

        if pos == 0:
            # ── Щит Пустоты ──
            extra = 2 if phase == 2 else 0
            shield = self.void_shield_amount + extra
            self.gain_shield(shield, combat_manager)
            self._exposed = False
            if combat_manager:
                combat_manager.add_log_message(
                    f"[ЭЛЕМЕНТАЛЬ] Щит Пустоты: +{shield}."
                )
        elif pos == 1:
            # ── Уязвимость ──
            self.vulnerable = 1   # Игрок бьёт ×1.5 (EffectCalculator шаг 4)
            self._exposed = True
            if combat_manager:
                combat_manager.add_log_message(
                    "[ЭЛЕМЕНТАЛЬ] Щит Пустоты рассеян — Элементаль УЯЗВИМ!"
                )
        else:
            # pos == 2 (defend turn, phase 1 only)
            self._exposed = False

    # ── Боевая логика ───────────────────────────────────────────────────

    @staticmethod
    def random_title() -> str:
        return random.choice(VoidElemental._TITLES)

    def choose_intent(self):
        phase = self.current_phase
        cycle_len = 2 if phase == 2 else 3
        pos = self.turn_count % cycle_len

        if pos == 0:
            # Щит Пустоты: слабая атака
            self.set_intent("attack", int(self.base_test_damage * 0.7))
        elif pos == 1:
            # Уязвимость: сильная атака
            self.set_intent("attack", int(self.base_test_damage * 1.4))
        else:
            # pos == 2: defend (только в фазе 1)
            self.set_intent("defend", self.base_test_shield)
