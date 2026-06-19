# core/rules/stakes.py
# СТАВКИ / АНТЕ — авторские ограничения игрока ради глобальной награды (Balatro-stake /
# StS Ascension). Первый КОНТЕНТ поверх RuleStack: доказывает архитектуру слома на
# крошечной поверхности (спека _rulestack_design.md §6). Ставки = БАЗОВАЯ игра (опт-ин
# сложность с первого фрейма); автоматический push парадоксов — скрытый режим (позже).
#
# Ставка = именованный БАНДЛ RuleMod (ограничение + награда). Срез гоняет 2 слоя:
#   • DECKBUILD — одноразовый run-setup (обрезка колоды / правка игрока на старте);
#   • DAMAGE    — постоянный множитель урона игрока (живёт в стеке весь забег).
# Моды без per-run состояния (конфиг иммутабелен) → инстансы можно держать в реестре.
from core.rules.RuleStack import RuleMod, Scope

# Лимит карт стартовой колоды для Ставки «Аскет».
# Калибровка С46 (true ascension): ≤6 — суровая обрезка. Аскет БЕЗ урон-награды:
# награда за риск = слой Энтропии/очков позже, не урон в забеге (спека §9 п.1).
# NB: ось «лимит карт» структурно НЕ штраф (тонкая колода = консистентность) — классы
# с компактным стартером (Воин/Берсерк) её любят. Универсальный штраф — только ось HP.
ASCETIC_MAX_CARDS = 6
# Доля макс. HP, остающаяся при Ставке «Хрупкость» (универсальный ascension-штраф).
FRAGILE_HP_FRACTION = 0.30
# Урон-награда «Хрупкости»: частичная компенсация, НЕ покрывает HP-штраф (выживание падает).
FRAGILE_DAMAGE_MULT = 1.25

# ── ВОСХОЖДЕНИЕ (хардкор-режим, бонус L3 Грейда) ──────────────────────────────
# Бандл штрафов «true ascension» (StS Ascension / Balatro high stake), открыт на L3.
# Числа — старт-калибровка (после альфа-теста). Часть штрафов — RuleMod (враги/HP),
# часть (золото/Опыт) живёт в RewardManager/GameManager через is_hardcore_active().
HARDCORE_STAKE_ID       = "hardcore"
HARDCORE_MIN_GRADE      = 3       # гейт: Ставка доступна только с Грейда L3 «Архитектор»
HARDCORE_ENEMY_DMG_MULT = 1.25    # враги бьют сильнее
HARDCORE_HP_FRACTION    = 0.75    # макс. HP игрока урезан
HARDCORE_GOLD_MULT      = 0.5     # золота с наград меньше (RewardManager)
HARDCORE_XP_MULT        = 1.5     # НАГРАДА: поток Опыта за бой больше (GameManager)


class _DamageMult(RuleMod):
    """DAMAGE-scope: множитель урона игрока (награда Ставки). Постоянный."""

    def __init__(self, stake_id, stake_name, factor):
        super().__init__(
            f"{stake_id}:dmg", f"{stake_name}: урон ×{factor:g}", Scope.DAMAGE,
            source="stake", predicate=lambda ctx: ctx.get("is_player_attack"),
        )
        self.factor = factor

    def apply(self, ctx):
        ctx["damage"] = int(ctx["damage"] * self.factor)


class _EnemyDamageMult(RuleMod):
    """DAMAGE-scope: множитель урона ВРАГА (штраф хардкора). Predicate ловит НЕ-
    игроцкие атаки (зеркало _DamageMult, который бьёт только по атакам игрока)."""

    def __init__(self, stake_id, stake_name, factor):
        super().__init__(
            f"{stake_id}:edmg", f"{stake_name}: урон врагов ×{factor:g}", Scope.DAMAGE,
            source="stake", predicate=lambda ctx: not ctx.get("is_player_attack"),
        )
        self.factor = factor

    def apply(self, ctx):
        ctx["damage"] = int(ctx["damage"] * self.factor)


class _TrimDeck(RuleMod):
    """DECKBUILD-scope: обрезать стартовую колоду до max_cards (ограничение «Аскет»)."""

    def __init__(self, stake_id, stake_name, max_cards):
        super().__init__(
            f"{stake_id}:trim", f"{stake_name}: ≤{max_cards} карт", Scope.DECKBUILD,
            source="stake",
        )
        self.max_cards = max_cards

    def apply(self, ctx):
        deck = ctx.get("deck")
        if deck is not None and len(deck) > self.max_cards:
            del deck[self.max_cards:]          # мутируем колоду на месте


class _HalfMaxHp(RuleMod):
    """DECKBUILD-scope (run-setup): урезать макс. HP игрока, один раз на старте забега."""

    def __init__(self, stake_id, stake_name, fraction):
        super().__init__(
            f"{stake_id}:hp", f"{stake_name}: ½ макс. HP", Scope.DECKBUILD,
            source="stake",
        )
        self.fraction = fraction

    def apply(self, ctx):
        p = ctx.get("player")
        if p is None:
            return
        p.max_hp = max(1, int(p.max_hp * self.fraction))
        p.hp = min(p.hp, p.max_hp)


class _EnableDebt(RuleMod):
    """DECKBUILD-scope (run-setup): открыть ДОЛГ ресурсов на игроке на весь забег (§4).

    Ставит флаги energy_overdraft/hp_overdraft → CombatManager (гейт энергии в минус) и
    Creature (пол HP в минус) пускают ресурсы за 0 (power now, pay later). Это и есть
    «живая активация» долга: до Ставки долг существовал только в симуляторе. Флаг живёт
    на player (переживает бои забега). Долг — ТОЛ, не наказание: риск = сам движок."""

    def __init__(self, stake_id, stake_name):
        super().__init__(
            f"{stake_id}:debt", f"{stake_name}: долг ресурсов", Scope.DECKBUILD,
            source="stake",
        )

    def apply(self, ctx):
        p = ctx.get("player")
        if p is None:
            return
        p.energy_overdraft = True
        p.hp_overdraft = True


class Stake:
    """Именованная Ставка — бандл RuleMod (ограничение + награда). Активация пушит
    моды в RuleStack забега и применяет одноразовый DECKBUILD run-setup сразу."""

    def __init__(self, id, name, description, mods, min_grade=0):
        self.id          = id
        self.name        = name
        self.description = description
        self._mods       = mods
        # Гейт по Грейду: Ставка показывается в Хабе только при current_grade >=
        # min_grade (0 = доступна всем с первого фрейма). Хардкор = L3.
        self.min_grade   = min_grade

    def mods(self):
        return list(self._mods)

    def activate(self, game_manager):
        """Применить Ставку к забегу: запушить моды в RuleStack + применить СВОИ
        одноразовые DECKBUILD-моды (run-setup: обрезка колоды / правка игрока).

        ВАЖНО: применяем именно СВОЙ DECKBUILD-мод напрямую, а НЕ rs.apply(DECKBUILD)
        над всем стеком — иначе при активации второй Ставки одноразовые DECKBUILD-моды
        ранее добавленной Ставки сработали бы ПОВТОРНО (двойное урезание HP/колоды).
        DAMAGE-моды просто живут в стеке и работают весь забег."""
        rs  = game_manager.rulestack
        ctx = {
            "deck":         game_manager.current_deck,
            "player":       game_manager.player,
            "game_manager": game_manager,
        }
        for m in self._mods:
            rs.push(m)
            if m.scope == Scope.DECKBUILD and (m.predicate is None or m.predicate(ctx)):
                m.apply(ctx)


def _build_stakes():
    # Аскет — ЧИСТОЕ ограничение (true ascension): без урон-награды, награда = Энтропия позже.
    ascetic = Stake(
        "ascetic", "Аскет",
        f"Стартовая колода не больше {ASCETIC_MAX_CARDS} карт. Суровое испытание.",
        [_TrimDeck("ascetic", "Аскет", ASCETIC_MAX_CARDS)],
    )
    # Хрупкость — HP-штраф с частичной урон-компенсацией (net выживание всё равно падает).
    fragile = Stake(
        "fragile", "Хрупкость",
        f"Максимальное здоровье — лишь {FRAGILE_HP_FRACTION:.0%}. "
        f"Взамен урон ×{FRAGILE_DAMAGE_MULT:g}.",
        [_HalfMaxHp("fragile", "Хрупкость", FRAGILE_HP_FRACTION),
         _DamageMult("fragile", "Хрупкость", FRAGILE_DAMAGE_MULT)],
    )
    # Кровавый Кредит — открывает ДОЛГ (овердрафт энергии и HP) на весь забег: можно
    # уходить в минус ради множителя урона ценой близости к смерти. Риск = сам движок
    # (power now, pay later), без доп. урон-награды. Живая активация долга (§4, С49).
    blood_credit = Stake(
        "blood_credit", "Кровавый Кредит",
        "Можно уходить в МИНУС по энергии и здоровью: глубина долга множит урон, но "
        "приближает смерть. Сила сейчас — расплата потом.",
        [_EnableDebt("blood_credit", "Кровавый Кредит")],
    )
    # Восхождение — хардкор-бандл (L3 Грейд). Штрафы: враги бьют сильнее + макс. HP
    # урезан (RuleMod), золото меньше (RewardManager). Награда: Опыт ×N (GameManager).
    # Золото/Опыт enforce'ятся через is_hardcore_active(), а не RuleMod — у дропа/Опыта
    # пока нет точек врезки RuleStack (вшит только Scope.DAMAGE).
    hardcore = Stake(
        HARDCORE_STAKE_ID, "Восхождение",
        f"ХАРДКОР (Грейд L3+): враги бьют ×{HARDCORE_ENEMY_DMG_MULT:g}, ваш максимум "
        f"HP — {HARDCORE_HP_FRACTION:.0%}, золота с наград ×{HARDCORE_GOLD_MULT:g}. "
        f"Взамен Опыт за бой ×{HARDCORE_XP_MULT:g}.",
        [_EnemyDamageMult(HARDCORE_STAKE_ID, "Восхождение", HARDCORE_ENEMY_DMG_MULT),
         _HalfMaxHp(HARDCORE_STAKE_ID, "Восхождение", HARDCORE_HP_FRACTION)],
        min_grade=HARDCORE_MIN_GRADE,
    )
    return {s.id: s for s in (ascetic, fragile, blood_credit, hardcore)}


# Реестр доступных Ставок (id -> Stake).
STAKES = _build_stakes()


def is_hardcore_active(game_manager) -> bool:
    """Активна ли Ставка «Восхождение» в текущем забеге — по модам в RuleStack.

    Источник истины — реально запушенные моды (не отдельный флаг): золото/Опыт
    enforce'ятся в RewardManager/GameManager, читая это. game_manager без rulestack
    (sim-стаб) → False."""
    rs = getattr(game_manager, "rulestack", None)
    if rs is None:
        return False
    return any(m.id.startswith(f"{HARDCORE_STAKE_ID}:") for m in rs.active())


def hardcore_gold_multiplier(game_manager) -> float:
    """Множитель золота с наград: при активном хардкоре ×HARDCORE_GOLD_MULT,
    иначе 1.0. Применяется в RewardManager (у дропа нет точки врезки RuleStack)."""
    return HARDCORE_GOLD_MULT if is_hardcore_active(game_manager) else 1.0


def hardcore_xp_multiplier(game_manager) -> float:
    """Множитель потока Опыта за бой (НАГРАДА хардкора): при активном хардкоре
    ×HARDCORE_XP_MULT, иначе 1.0. Применяется в GameManager.distribute_combat_rewards."""
    return HARDCORE_XP_MULT if is_hardcore_active(game_manager) else 1.0
