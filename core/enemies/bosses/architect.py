# core/enemies/bosses/architect.py
# Архитектор Башни — финальный босс этажа 100. Ворота: полный компаунд.
# Три фазы, высокие статы. Victory lap: если билд прошёл эт.80 — пройдёт и здесь.
import random
from core.enemies.base import IntentAttack
from core.enemies.bosses.base import BossBase


class TowerArchitect(BossBase):
    """Босс этажа 100 — финальный экзамен (полный компаунд).

    Три фазы по HP:
    - Фаза 1 (>66%): умеренные атаки, защита каждый 3-й ход.
    - Фаза 2 (33-66%): тяжёлые атаки (×1.3), +1 Слабость за каждый удар.
    - Фаза 3 (<33%): отчаянные атаки (×1.6), без защиты.

    Высокие базовые статы (×2.2 HP / ×1.3 dmg / ×1.8 shield от EnemySpawner)
    делают бой затяжным — проверка всего билда сразу.

    Мягкие обходы: если пройден эт.80 — билд работает. Специфических классовых
    обходов не требуется (victory lap).
    """

    PHASE1_THRESHOLD = 2 / 3   # >66% HP
    PHASE2_THRESHOLD = 1 / 3   # 33-66% HP

    _TITLES = [
        "Архитектор Башни",
        "Владыка Шпиля",
        "Создатель",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)

    # ── Трёхфазная система ───────────────────────────────────────────────

    @property
    def current_phase(self) -> int:
        """Переопределено: 3 фазы по третям HP."""
        if self.max_hp <= 0:
            return 1
        frac = self.hp / self.max_hp
        if frac > self.PHASE1_THRESHOLD:
            return 1
        elif frac > self.PHASE2_THRESHOLD:
            return 2
        else:
            return 3

    # ── Боевая логика ───────────────────────────────────────────────────

    @staticmethod
    def random_title() -> str:
        return random.choice(TowerArchitect._TITLES)

    def choose_intent(self):
        phase = self.current_phase

        if phase == 1:
            # Умеренные атаки, защита каждый 3-й ход.
            if self.turn_count % 3 == 2:
                self.set_intent("defend", self.base_test_shield)
            else:
                self.set_intent("attack", self.base_test_damage)

        elif phase == 2:
            # Тяжёлые атаки, без защиты.
            self.set_intent("attack", int(self.base_test_damage * 1.3))

        else:  # phase == 3
            # Отчаянные атаки, максимальный урон.
            self.set_intent("attack", int(self.base_test_damage * 1.6))

    def execute_intent(self, player, combat_manager=None):
        """Фаза 2: каждая атака накладывает +1 Слабость."""
        super().execute_intent(player, combat_manager)
        if self.current_phase == 2 and isinstance(self.intent, IntentAttack):
            player.weak += 1
            if combat_manager:
                combat_manager.add_log_message(
                    "[АРХИТЕКТОР] Ваша защита трещит под натиском: +1 Слабость."
                )
