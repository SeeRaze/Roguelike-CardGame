# core/enemies/bosses/architect.py
# Заказчик — финальный босс этажа 100. Высший вердикт проекту — и зеркало твоих
# собственных ранних амбиций/надежд на него. Три фазы (нарастающий поток правок),
# высокие статы. Victory lap: прошёл эт.80 — пройдёшь и здесь. Внешний судья;
# мост к Демиургу (встреча с самим собой). Класс-ID TowerArchitect сохранён.
import random
from core.enemies.base import IntentAttack
from core.enemies.bosses.base import BossBase


class TowerArchitect(BossBase):
    """Финальный босс этажа 100 — высший вердикт проекту («Заказчик»).

    Три фазы по HP (поток правок нарастает):
    - Фаза 1 (>66%): первое впечатление — умеренные правки, защита каждый 3-й ход.
    - Фаза 2 (33-66%): поток правок — тяжёлые удары (×1.3), +1 Токсичность за удар.
    - Фаза 3 (<33%): финальные требования — отчаянный накат (×1.6), без защиты.

    Высокие базовые статы (×2.2 HP / ×1.3 dmg / ×1.8 shield от EnemySpawner)
    делают бой затяжным — проверка всего билда сразу.

    Мягкие обходы: если пройден эт.80 — билд работает. Специфических классовых
    обходов не требуется (victory lap).
    """

    PHASE1_THRESHOLD = 2 / 3   # >66% HP
    PHASE2_THRESHOLD = 1 / 3   # 33-66% HP

    _TITLES = [
        "Заказчик",
        "Главный заказчик",
        "Стейкхолдер",
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
            # Умеренные правки, защита каждый 3-й ход.
            if self.turn_count % 3 == 2:
                self.set_intent("defend", self.base_test_shield)
            else:
                self.set_intent("attack", self.base_test_damage)

        elif phase == 2:
            # Поток правок: тяжёлые удары, без защиты.
            self.set_intent("attack", int(self.base_test_damage * 1.3))

        else:  # phase == 3
            # Финальные требования: отчаянный накат, максимальный урон.
            self.set_intent("attack", int(self.base_test_damage * 1.6))

    def execute_intent(self, player, combat_manager=None):
        """Фаза 2: каждый удар (правка) накладывает +1 Токсичность."""
        super().execute_intent(player, combat_manager)
        if self.current_phase == 2 and isinstance(self.intent, IntentAttack):
            player.tox += 1
            if combat_manager:
                combat_manager.add_log_message(
                    "[ЗАКАЗЧИК] Правки сыплются, защита трещит: +1 Токсичность."
                )
