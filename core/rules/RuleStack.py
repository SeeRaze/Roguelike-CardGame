# core/rules/RuleStack.py
# ФУНДАМЕНТ «СЛОМА ИГРЫ» — стек активных «правок правил» (data-driven).
# Полная спека: _rulestack_design.md (корень репо).
#
# Зачем: игра про авторство над собственным рулсетом (Ставки сейчас, Парадокс-режим
# позже). Чтобы «бесконечное безумие» не превратилось в неотлаживаемую кашу из
# if/else по всему движку, КАЖДАЯ правка правила = ДАННЫЕ (RuleMod) с приоритетом и
# областью срабатывания (Scope), а движок просто консультирует стек в точках врезки.
# Это обобщение паттерна, уже применённого в Status/Combo/Detonation/Forge-реестрах
# (упорядочены core/ReactionOrder.py, защищены core/forge.TriggerGuard) — с уровня
# БОЯ на уровень всего ЗАБЕГА.
#
# Чистый модуль: ТОЛЬКО структуры + диспетч. Без pygame, без боевой логики, без
# побочек на импорте. RuleMod.apply мутирует переданный ctx (как реакции мутируют урон).
#
# ── Связь с тремя столпами движка ─────────────────────────────────────────────
#   Order/Scope  — КОГДА и в каком порядке (этот файл: Scope + priority).
#   Guard/Бюджет — потолок/цена (TriggerGuard глубины + Энтропия, отдельный слой).
#   Stack        — что активно прямо сейчас (этот файл: RuleStack).
from enum import IntEnum


class Scope(IntEnum):
    """СЛОЙ, на котором правило вмешивается в игру. Движок зовёт
    `rulestack.apply(scope, ctx)` в соответствующей точке врезки (см. спеку §2.4).

    Значения с зазорами — под вставку будущих слоёв без переписывания остальных.
    Базовая игра = пустой стек: точки врезки вшиты С ПЕРВОГО ФРЕЙМА, при отсутствии
    модов apply() — no-op.
    """

    DECKBUILD    = 10   # старт забега: меняет стартовую колоду/правила
    RUN          = 20   # глобально на весь забег (множители цен/дропа/…)
    ROOM_ENTER   = 30   # вход в узел карты этажей
    COMBAT_START = 40   # начало боя (CombatManager.__init__)
    TURN_START   = 50   # начало хода игрока
    TURN_END     = 60   # конец хода игрока
    REACTION     = 70   # внутри боевого конвейера реакций (рядом с _guarded)
    DAMAGE       = 80   # расчёт урона (EffectCalculator, рядом с on_damage_calculated)
    ON_DEATH     = 90   # смерть игрока/врага (правки win-condition: Уроборос)


class RuleMod:
    """Атом слома: одна правка правила = данные с приоритетом и областью.

    Подклассы (или фабрики) переопределяют `apply(ctx)` — мутируют переданный
    контекст (например, ctx["damage"] *= 2). Один RuleMod живёт в ОДНОМ scope;
    составной эффект («Ставка») = БАНДЛ из нескольких RuleMod (см. core/rules/stakes.py).

    Поля:
      id        — стабильный идентификатор (для pop/дедупа/сериализации).
      name/desc — для игрока (RuleStack — это и UI: список активных правок).
      scope     — слой срабатывания (Scope).
      priority  — порядок ВНУТРИ scope (меньше = раньше; зазоры под вставку).
      source    — "stake" | "paradox" | "relic" | "committed" (откуда пришёл мод).
      cost      — Энтропия, которую мод держит активной (валюта слома; в срезе Ставок=0).
      predicate — опц. условие активности: predicate(ctx)->bool (как requires детонаций).
    """

    def __init__(self, id, name, scope, *, description="", priority=0,
                 source="", cost=0, predicate=None):
        self.id          = id
        self.name        = name
        self.description  = description
        self.scope       = scope
        self.priority    = priority
        self.source      = source
        self.cost        = cost
        self.predicate   = predicate

    def apply(self, ctx):
        """Переопределить в подклассе. Мутирует ctx и/или возвращает значение.
        База — no-op (нейтральный мод)."""
        return None

    def __repr__(self):
        return f"<RuleMod {self.id} scope={self.scope.name} prio={self.priority}>"


class RuleStack:
    """Носитель активных правок правил на ОДИН забег (живёт на GameManager).

    Базовая игра стартует пустой; источники (Ставки/парадоксы/реликвии) пушат моды.
    Движок в точках врезки зовёт apply(scope, ctx) — моды этого scope срабатывают
    по возрастанию priority (стабильно: при равном priority — порядок добавления).

    Энтропия (валюта слома, жёсткая) учитывается через cost модов: total_cost() —
    задел под бюджет; полная экономика Энтропии — отдельный слой (спека §5)."""

    def __init__(self):
        # Порядок добавления сохраняется → стабильная вторичная сортировка.
        self._mods: list = []

    def push(self, mod: RuleMod) -> RuleMod:
        """Добавить мод в стек. Возвращает его же (удобно для цепочек/тестов)."""
        self._mods.append(mod)
        return mod

    def pop(self, mod_id: str) -> bool:
        """Снять мод по id. True если что-то удалили."""
        before = len(self._mods)
        self._mods = [m for m in self._mods if m.id != mod_id]
        return len(self._mods) < before

    def clear(self) -> None:
        """Снять все моды (новый забег / сброс)."""
        self._mods.clear()

    def active(self) -> list:
        """Все активные моды в порядке добавления (для UI-списка)."""
        return list(self._mods)

    def total_cost(self) -> int:
        """Суммарная Энтропия, занятая активными модами (задел под бюджет)."""
        return sum(m.cost for m in self._mods)

    def mods_for(self, scope: Scope) -> list:
        """Активные моды данного scope, упорядоченные по priority (стабильно:
        равный priority → порядок добавления, т.к. sort стабилен)."""
        return sorted(
            (m for m in self._mods if m.scope == scope),
            key=lambda m: m.priority,
        )

    def apply(self, scope: Scope, ctx):
        """Прогнать ctx через все моды данного scope по порядку. Мод применяется,
        только если его predicate (если задан) пропускает ctx. Возвращает ctx
        (мутированный на месте). Пустой стек / нет модов scope → ctx без изменений."""
        for mod in self.mods_for(scope):
            if mod.predicate is None or mod.predicate(ctx):
                mod.apply(ctx)
        return ctx
