# core/enemies/bosses/base.py
# Базовый класс босса — расширяет Enemy фазовой системой и хуками реакций.
# Паттерн: hasattr duck-typing (как у реликвий) — CombatManager проверяет наличие
# хуков, не импортируя BossBase.
from core.enemies.base import Enemy


class BossBase(Enemy):
    """Базовый каркас для всех боссов-фильтров.

    Расширяет Enemy:
    - Фазовая система: current_phase (1/2 по умолчанию, 1/2/3 у Архитектора).
      Порог — PHASE_THRESHOLD (доля max_hp).
    - Хук on_card_played(card, player, cm): реакция на розыгрыш карты игроком.
    - Хук on_turn_start(player, cm): обновление состояния перед выбором намерения.

    CombatManager проверяет наличие хуков через hasattr — жёсткий импорт не нужен.
    """

    # Доля max_hp, ниже которой начинается фаза 2. Переопределяется в подклассах.
    PHASE_THRESHOLD = 0.5

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        # Флаг is_boss используется в CombatManager._check_enemy_death для
        # раздельной статистики убийств (обычные враги / боссы).
        self.is_boss = True

    # ── Фазовая система ──────────────────────────────────────────────────

    @property
    def current_phase(self) -> int:
        """Номер фазы по текущему HP. По умолчанию двухфазная: 1 (>50%), 2 (≤50%).
        Переопределяется для трёхфазных боссов (Архитектор)."""
        if self.max_hp <= 0:
            return 1
        if self.hp <= self.max_hp * self.PHASE_THRESHOLD:
            return 2
        return 1

    # ── Хуки реакций (hasattr duck-typing для CombatManager) ─────────────

    def on_card_played(self, card, player, combat_manager) -> None:
        """Вызывается после розыгрыша карты игроком (в play_card_by_index).
        Переопредели для реакций: +щит за карту (Скоуп-крип), etc."""
        pass

    def on_turn_start(self, player, combat_manager) -> None:
        """Вызывается в начале хода босса, перед choose_intent().
        Переопредели для: эскалации (Демо-день), проверки колоды (Скоуп-крип),
        стабильной сборки (Интеграционный ад), заряда времени (Цейтнот)."""
        pass
