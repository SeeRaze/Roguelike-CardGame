# core/enemies/elites/base.py
# Базовый класс элитного врага — расширяет Enemy хуками реакций.
# Паттерн полностью повторяет BossBase, но БЕЗ фазовой системы (элитки проще
# боссов) и с флагом is_elite вместо is_boss. CombatManager проверяет наличие
# хуков через hasattr (duck-typing, как у реликвий) — жёсткий импорт не нужен.
from core.enemies.base import Enemy


class EliteBase(Enemy):
    """Базовый каркас для всех элитных врагов-контр билдам.

    Элитки — это рядовые враги с УНИКАЛЬНОЙ механикой, наказывающей конкретный
    архетип билда (колоды-пулемёты / оборона / хил / DoT). В отличие от боссов:
    - нет фазовой системы (current_phase) — механика одна на весь бой;
    - is_elite=True (а не is_boss) → RewardManager даёт улучшенную награду,
      EnemySpawner накладывает стат-множители элиты (×1.5 HP и т.д.).

    Хуки (переопределяются в подклассах, CombatManager зовёт через hasattr):
    - on_card_played(card, player, cm): реакция на розыгрыш карты игроком.
    - on_turn_start(player, cm): обновление состояния перед choose_intent().
    """

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        # Флаг is_elite используется RewardManager (лучшая редкость реликвии) и
        # выставляется также EnemySpawner.build_enemy; дублируем здесь для тех,
        # кто создаёт элитку напрямую (тесты).
        self.is_elite = True

    # ── Хуки реакций (hasattr duck-typing для CombatManager) ─────────────

    def on_card_played(self, card, player, combat_manager) -> None:
        """Вызывается после розыгрыша карты игроком (в play_card_by_index).
        Переопредели для реакций: +щит за карту (Пожиратель Заклинаний)."""
        pass

    def on_turn_start(self, player, combat_manager) -> None:
        """Вызывается в начале хода врага, перед choose_intent().
        Переопредели для: наложения яда (Гнойник), детекта хила (Мясник),
        пожирания DoT (Пожиратель Скверны)."""
        pass
