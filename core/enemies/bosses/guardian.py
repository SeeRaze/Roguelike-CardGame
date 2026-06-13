# core/enemies/bosses/guardian.py
# Демо-день — босс этажа 20. Первый суд над проектом: показать, что вообще есть.
# Механика: эскалация урона каждый цикл — чем дольше тянешь/увиливаешь от показа,
# тем выше ожидания и строже спрос. Классы без сустейна не вытягивают долгий
# «показ»; хил/щит/союзники-танки проходят. Класс-ID ThresholdGuardian сохранён.
import random
from core.enemies.bosses.base import BossBase


class ThresholdGuardian(BossBase):
    """Босс этажа 20 — первый суд над проектом («Демо-день»).

    Механика эскалации: каждый 3-й ход (defend) увеличивает множитель атаки на 0.4.
    Атака = base_dmg × (1 + 0.4 × escalation), capped ×3 — тянешь демо, ожидания
    растут. Фаза 2 (HP < 40%): дедлайн настал, отчаянная отгрузка без эскалации/защиты.

    Мягкие обходы:
    - Сустейн (Вайб-кодер): переживает растущий спрос
    - Щитовик (Тестировщик): блокирует удары
    - Стажёр: DPS-гонка (закрывает демо до эскалации)
    - Союзники поглощают удары (случайный таргетинг)
    """

    PHASE_THRESHOLD = 0.4
    ESCALATION_PER_CYCLE = 0.4   # +40% к урону за каждый defend (рост ожиданий)
    MAX_ESCALATION_MULT = 3.0     # кап множителя урона

    _TITLES = [
        "Демо-день",
        "Приёмка",
        "Сдача проекта",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        self._escalation = 0

    # ── Боевая логика ───────────────────────────────────────────────────

    @property
    def _dmg_mult(self) -> float:
        """Текущий множитель урона от эскалации, capped."""
        return min(self.MAX_ESCALATION_MULT,
                   1.0 + self.ESCALATION_PER_CYCLE * self._escalation)

    @staticmethod
    def random_title() -> str:
        return random.choice(ThresholdGuardian._TITLES)

    def choose_intent(self):
        phase = self.current_phase

        if phase == 2:
            # Фаза 2 (HP < 40%): отчаянные атаки, без эскалации и защиты.
            self.set_intent("attack", self.base_test_damage)

        else:
            step = self.turn_count % 3

            if step == 0 or step == 1:
                # Два удара с текущим множителем эскалации.
                dmg = int(self.base_test_damage * self._dmg_mult)
                self.set_intent("attack", dmg)
            else:
                # step == 2: защита + рост эскалации (ожидания растут).
                self.set_intent("defend", self.base_test_shield)
                self._escalation += 1
