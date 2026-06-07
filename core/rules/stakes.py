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
ASCETIC_MAX_CARDS = 10
# Доля макс. HP, остающаяся при Ставке «Хрупкость».
FRAGILE_HP_FRACTION = 0.5


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


class Stake:
    """Именованная Ставка — бандл RuleMod (ограничение + награда). Активация пушит
    моды в RuleStack забега и применяет одноразовый DECKBUILD run-setup сразу."""

    def __init__(self, id, name, description, mods):
        self.id          = id
        self.name        = name
        self.description = description
        self._mods       = mods

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
    ascetic = Stake(
        "ascetic", "Аскет",
        f"Стартовая колода не больше {ASCETIC_MAX_CARDS} карт. Зато урон ×1.5.",
        [_TrimDeck("ascetic", "Аскет", ASCETIC_MAX_CARDS),
         _DamageMult("ascetic", "Аскет", 1.5)],
    )
    fragile = Stake(
        "fragile", "Хрупкость",
        "Максимальное здоровье вдвое меньше. Зато урон ×2.",
        [_HalfMaxHp("fragile", "Хрупкость", FRAGILE_HP_FRACTION),
         _DamageMult("fragile", "Хрупкость", 2.0)],
    )
    return {s.id: s for s in (ascetic, fragile)}


# Реестр доступных Ставок (id -> Stake).
STAKES = _build_stakes()
