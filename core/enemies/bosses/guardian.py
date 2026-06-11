# core/enemies/bosses/guardian.py
# Страж Порога — босс этажа 20. Ворота: защита/хил.
# Механика: эскалация урона каждый цикл. Классы без сустейна не вытягивают
# долгий бой; классы с хилом/щитом/союзниками-танками проходят.
import random
from core.enemies.bosses.base import BossBase


class ThresholdGuardian(BossBase):
    """Босс этажа 20 — проверка защиты/восстановления.

    Механика эскалации: каждый 3-й ход (defend) увеличивает множитель атаки на 0.4.
    Атака = base_dmg × (1 + 0.4 × escalation), capped ×3.
    Фаза 2 (HP < 40%): отчаянные атаки без эскалации и защиты.

    Мягкие обходы:
    - Хил-классы (Маг-сустейн): переживают растущий урон
    - Щитовики (Воин): блокируют удары
    - Берсерк: DPS-гонка (убивает до эскалации)
    - Союзники поглощают удары (случайный таргетинг)
    """

    PHASE_THRESHOLD = 0.4
    ESCALATION_PER_CYCLE = 0.4   # +40% к урону за каждый defend
    MAX_ESCALATION_MULT = 3.0     # кап множителя урона

    _TITLES = [
        "Страж Порога",
        "Вратник Бездны",
        "Хранитель Первого Круга",
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
                # step == 2: защита + рост эскалации.
                self.set_intent("defend", self.base_test_shield)
                self._escalation += 1
