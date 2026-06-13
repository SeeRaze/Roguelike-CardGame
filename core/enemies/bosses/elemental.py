# core/enemies/bosses/elemental.py
# Интеграционный ад — босс этажа 60. Барьер: нестабильная интеграция.
# Механика: «Стабильная сборка» (поглощает flat-урон) чередуется с фазой Инцидента
# (всё развалилось — coffee: +40% входящего урона). Только burst-билды пробивают
# зелёную сборку и используют окно инцидента. Класс-ID VoidElemental сохранён.
import random
from core.enemies.bosses.base import BossBase


class VoidElemental(BossBase):
    """Босс этажа 60 — нестабильная интеграция («Интеграционный ад»).

    Цикл из двух фаз: Стабильная сборка (босс набирает щит, атакует слабо — «всё
    зелёное») → Инцидент (сборка развалилась: босс получает +40% урона через coffee,
    атакует сильно). Фаза 1 включает ещё и defend; фаза 2 короче и агрессивнее.

    Щит сборки растёт с этажом: VOID_SHIELD_BASE + floor // 10. На этаже 60
    это ~14 щита за фазу — flat-DPS билды не пробивают, а burst (комбо/
    детонации/форж-теги) проходят и бьют сильнее в окно Инцидента.

    Мягкие обходы:
    - Все классы с кат.4 движками: форж-теги ×mult, комбо, детонации
    - Вайб-кодер: Эхо × детонация = burst в окно Инцидента
    - Союзники дают стабильный DPS в обе фазы
    """

    PHASE_THRESHOLD = 0.4
    VOID_SHIELD_BASE = 8   # базовый щит «стабильной сборки» (+ floor // 10)

    _TITLES = [
        "Интеграционный ад",
        "Слияние веток",
        "Прод-инцидент",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        # spawn_floor ставится EnemySpawner'ом после конструктора.
        # По умолчанию 60 (типичный floor для этого босса).
        self.spawn_floor = 60
        # Флаг: босс в фазе Инцидента (вход. урон +40% через coffee).
        self._exposed = False

    # ── Вычисляемые свойства ─────────────────────────────────────────────

    @property
    def void_shield_amount(self) -> int:
        """Размер щита «стабильной сборки» в текущем бою (растёт с этажом)."""
        return self.VOID_SHIELD_BASE + self.spawn_floor // 10

    # ── Хук начала хода ──────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Определить фазу цикла: Стабильная сборка или Инцидент."""
        phase = self.current_phase
        cycle_len = 2 if phase == 2 else 3
        pos = self.turn_count % cycle_len

        if pos == 0:
            # ── Стабильная сборка ──
            extra = 2 if phase == 2 else 0
            shield = self.void_shield_amount + extra
            self.gain_shield(shield, combat_manager)
            self._exposed = False
            self.coffee = 0       # закрыть окно инцидента (coffee персистит, не распадается)
            if combat_manager:
                combat_manager.add_log_message(
                    f"[ИНТЕГРАЦИЯ] Сборка зелёная: +{shield} щита."
                )
        elif pos == 1:
            # ── Инцидент ── (окно бёрста: вход. урон ×1.4 через coffee)
            self.coffee = 2       # +20%/стак → ×1.4 (EffectCalculator шаг 4)
            self._exposed = True
            if combat_manager:
                combat_manager.add_log_message(
                    "[ИНТЕГРАЦИЯ] Сборка развалилась — ИНЦИДЕНТ (вход. урон +40%)!"
                )
        else:
            # pos == 2 (defend turn, phase 1 only)
            self._exposed = False
            self.coffee = 0

    # ── Боевая логика ───────────────────────────────────────────────────

    @staticmethod
    def random_title() -> str:
        return random.choice(VoidElemental._TITLES)

    def choose_intent(self):
        phase = self.current_phase
        cycle_len = 2 if phase == 2 else 3
        pos = self.turn_count % cycle_len

        if pos == 0:
            # Стабильная сборка: слабая атака
            self.set_intent("attack", int(self.base_test_damage * 0.7))
        elif pos == 1:
            # Инцидент: сильная атака
            self.set_intent("attack", int(self.base_test_damage * 1.4))
        else:
            # pos == 2: defend (только в фазе 1)
            self.set_intent("defend", self.base_test_shield)
