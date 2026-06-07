from managers.DeckManager import DeckManager
from core.forge import TriggerGuard
from managers.combat import (
    CardPlayMixin,
    DefeatMixin,
    PositioningMixin,
    ResolutionMixin,
    TurnPhaseMixin,
)


class CombatManager(
    PositioningMixin, CardPlayMixin, TurnPhaseMixin, ResolutionMixin, DefeatMixin
):
    """Менеджер боя, адаптированный под графический движок Pygame.
    Поддерживает как одного врага, так и группу (self.enemies — список).

    Оркестратор: инфра (жизненный цикл боя, лог, предохранитель глубины) живёт здесь;
    поведение — в когезивных миксинах `managers/combat/` (С49, разбор god-object)."""

    # Потолок ПЕРЕНОСА стаи между боями (Призыватель). Внутри боя призыв не
    # ограничен — лимит только на то, сколько выживших уносится в следующий бой.
    # Без него стая копилась бы вечно → бесконечный снежный ком.
    # ГЛАВНАЯ ручка баланса Призывателя: теперь враги бьют СЛУЧАЙНУЮ цель
    # (игрок/союзник, см. Enemy._choose_attack_target), поэтому стая ещё и
    # ТАНКует — потолок прямо задаёт живучесть. Свип с новым таргетингом
    # (медиана этажа смерти / wr50): cap6=43/6% · cap8=46/22% · cap10=54/68%.
    # cap6 ставит медиану вровень с Берсерком (42), не делая класс топ-1.
    MAX_PERSISTENT_ALLIES = 6

    def __init__(self, player, enemies, starting_deck, game_manager=None):
        self.gm = game_manager
        self.player = player
        # Приводим к списку: если передали одного врага — заворачиваем
        if isinstance(enemies, list):
            self.enemies = enemies
        else:
            self.enemies = [enemies]
        self.allies: list = []          # призванные союзники
        self._restore_persistent_allies()
        self.deck_manager = DeckManager(starting_deck)
        self.turn_count = 1
        # Счётчик сыгранных карт за текущий ход (предикаты тегов: first/nth card).
        self.cards_played_this_turn = 0

        self.combat_log = []
        self._elemental_blocked  = False
        self._combo_triggered = False
        # Транзиенты розыгрыша (Сессия 39): разыгрываемая карта + СНИМОК состояния
        # на момент намерения (§10.6) — предикаты тегов читают снимок, не живое поле.
        self._card_being_played = None
        self._play_snapshot = None
        # Предохранитель глубины триггеров (§10.2): считает ВСЕ ретриггеры (Эхо) +
        # детонации суммарно за один розыгрыш карты, обрывает на MAX_TRIGGER_DEPTH —
        # анти-∞-цикл и анти-переполнение чисел в реал-тайме. Сброс на каждом розыгрыше.
        self._trigger_guard = TriggerGuard()

        self.add_log_message("=== БОЙ НАЧАЛСЯ ===")

        # Хук on_combat_start -- реликвии
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_combat_start(self)

        # Хук on_combat_start -- активная способность
        ability = getattr(self.player, 'active_ability', None)
        if ability:
            ability.on_combat_start(self)

        self.start_turn_phase()

        # Позиционка (§5): инициализация строя на старте боя — ПОСЛЕ on_combat_start
        # и start_turn_phase, чтобы саммоны старта боя тоже встали в строй. Сбрасывает
        # рантайм-строй к классовому дефолту (флип Манёвра не переносится между боями)
        # + первичная расстановка. NO-OP без флага positioning_enabled (baseline зелёный).
        self._init_positioning()

    # --- Обратная совместимость: старый код читает self.enemy ---
    @property
    def enemy(self):
        """Первый враг в списке (для совместимости со старым кодом)."""
        return self.enemies[0] if self.enemies else None

    @enemy.setter
    def enemy(self, value):
        if self.enemies:
            self.enemies[0] = value
        else:
            self.enemies.append(value)

    def add_log_message(self, message):
        self.combat_log.append(message)
        if len(self.combat_log) > 6:
            self.combat_log.pop(0)

    def _guarded_action(self, label, fn):
        """Верхнеуровневое реакционное действие фазы врага (тик статусов, намерение
        врага, действие союзника). Сбрасывает глубину гарда В НОЛЬ перед вызовом —
        каждое такое действие самостоятельно (своё событие), и одно не должно «съесть»
        бюджет следующего. Внутри действия рекурсия (тик → хук → тик) по-прежнему
        ограничена потолком через вложенные _guarded. Возвращает результат fn()."""
        self._trigger_guard.depth = 0
        return self._guarded(label, fn)

    def _guarded(self, label, fn):
        """Выполнить реакционный вызов `fn()` под предохранителем глубины (§10.2).

        Возвращает результат fn(), либо None если потолок глубины достигнут (каскад
        оборван). Единая точка для ВСЕХ реакционных путей вне первичного apply:
        post-хуки розыгрыша (реликвии/враги), тики статусов, действия союзников —
        чтобы взаимно-рекурсивная цепочка (будущий хук, играющий эффект, который
        снова дёргает хук) гарантированно завершилась, а не зациклилась/переполнила
        числа. Порядок задаёт ReactionOrder, конечность — этот гард (ортогонально).

        `label` — человекочитаемая метка для лога обрыва."""
        guard = self._trigger_guard
        if not guard.enter():
            self.add_log_message(
                f"[ПРЕДОХРАНИТЕЛЬ] Каскад триггеров оборван ({label}, глубина)."
            )
            return None
        try:
            return fn()
        finally:
            guard.exit()