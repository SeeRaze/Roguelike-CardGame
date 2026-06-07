# tests/test_rulestack.py
# Ядро RuleStack (фундамент «слома игры»): Scope/RuleMod/RuleStack.
# Проверяем диспетч: push/pop, порядок по priority, apply мутирует ctx, predicate-гейт,
# пустой стек = no-op. Чистая логика, без pygame.
from types import SimpleNamespace

from core.rules import RuleStack, RuleMod, Scope
from core.Creature import Creature
from core.EffectCalculator import EffectCalculator


def _mult_mod(id, factor, *, priority=0, predicate=None):
    """Тестовый мод: умножает ctx['v'] на factor в scope DAMAGE."""
    m = RuleMod(id, id, Scope.DAMAGE, priority=priority, predicate=predicate)
    m.apply = lambda ctx, f=factor: ctx.__setitem__("v", ctx["v"] * f)
    return m


def test_пустой_стек_не_меняет_ctx():
    rs = RuleStack()
    ctx = {"v": 10}
    assert rs.apply(Scope.DAMAGE, ctx)["v"] == 10


def test_push_и_active():
    rs = RuleStack()
    m = rs.push(_mult_mod("a", 2))
    assert m.id == "a"
    assert [x.id for x in rs.active()] == ["a"]


def test_pop_снимает_по_id():
    rs = RuleStack()
    rs.push(_mult_mod("a", 2))
    rs.push(_mult_mod("b", 3))
    assert rs.pop("a") is True
    assert [x.id for x in rs.active()] == ["b"]
    assert rs.pop("нет") is False


def test_apply_мутирует_ctx():
    rs = RuleStack()
    rs.push(_mult_mod("x2", 2))
    ctx = {"v": 5}
    rs.apply(Scope.DAMAGE, ctx)
    assert ctx["v"] == 10


def test_порядок_по_priority():
    """priority меньше = раньше. (×2 затем +1) ≠ (+1 затем ×2) — порядок виден."""
    rs = RuleStack()
    add1 = RuleMod("add", "add", Scope.DAMAGE, priority=20)
    add1.apply = lambda ctx: ctx.__setitem__("v", ctx["v"] + 1)
    mul2 = RuleMod("mul", "mul", Scope.DAMAGE, priority=10)
    mul2.apply = lambda ctx: ctx.__setitem__("v", ctx["v"] * 2)
    # Пушим в «неправильном» порядке — стек упорядочит по priority.
    rs.push(add1)
    rs.push(mul2)
    ctx = {"v": 5}
    rs.apply(Scope.DAMAGE, ctx)
    assert ctx["v"] == 11          # (5*2)+1, mul(prio10) раньше add(prio20)


def test_равный_priority_стабилен_по_порядку_добавления():
    rs = RuleStack()
    order = []
    a = RuleMod("a", "a", Scope.DAMAGE, priority=5); a.apply = lambda ctx: order.append("a")
    b = RuleMod("b", "b", Scope.DAMAGE, priority=5); b.apply = lambda ctx: order.append("b")
    rs.push(a); rs.push(b)
    rs.apply(Scope.DAMAGE, {})
    assert order == ["a", "b"]


def test_scope_изоляция():
    """Мод одного scope не срабатывает на чужом scope."""
    rs = RuleStack()
    rs.push(_mult_mod("dmg", 2))               # DAMAGE
    ctx = {"v": 5}
    rs.apply(Scope.COMBAT_START, ctx)          # другой scope → no-op
    assert ctx["v"] == 5
    rs.apply(Scope.DAMAGE, ctx)
    assert ctx["v"] == 10


def test_predicate_гейтит_применение():
    rs = RuleStack()
    rs.push(_mult_mod("only_player", 3,
                      predicate=lambda ctx: ctx.get("is_player")))
    ctx_enemy = {"v": 5, "is_player": False}
    rs.apply(Scope.DAMAGE, ctx_enemy)
    assert ctx_enemy["v"] == 5                 # predicate False → не применился
    ctx_player = {"v": 5, "is_player": True}
    rs.apply(Scope.DAMAGE, ctx_player)
    assert ctx_player["v"] == 15


def test_total_cost_суммирует_энтропию():
    rs = RuleStack()
    rs.push(RuleMod("a", "a", Scope.RUN, cost=2))
    rs.push(RuleMod("b", "b", Scope.RUN, cost=3))
    assert rs.total_cost() == 5


def test_clear_снимает_всё():
    rs = RuleStack()
    rs.push(_mult_mod("a", 2)); rs.push(_mult_mod("b", 3))
    rs.clear()
    assert rs.active() == []


# ─── Сквозная врезка: RuleStack DAMAGE-scope в EffectCalculator ───────────────


def _dmg_mult_mod(factor):
    """RuleMod DAMAGE-scope: умножает урон игрока на factor."""
    m = RuleMod("stake_dmg", "Ставка", Scope.DAMAGE,
                predicate=lambda ctx: ctx["is_player_attack"])
    m.apply = lambda ctx, f=factor: ctx.__setitem__("damage", int(ctx["damage"] * f))
    return m


def _cm_with_stack(player, rulestack):
    """Минимальный combat_manager + gm с rulestack для calculate_damage."""
    gm = SimpleNamespace(rulestack=rulestack, relics=[], stats={})
    return SimpleNamespace(player=player, gm=gm,
                           add_log_message=lambda _: None)


def test_damage_scope_удваивает_урон_игрока():
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    rs = RuleStack(); rs.push(_dmg_mult_mod(2))
    cm = _cm_with_stack(player, rs)
    dmg = EffectCalculator.calculate_damage(player, target, 10,
                                            game_manager=cm.gm, combat_manager=cm)
    assert dmg == 20


def test_пустой_стек_урон_не_трогает():
    """Базовый забег = пустой стек → регресс-нейтрально."""
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    cm = _cm_with_stack(player, RuleStack())
    dmg = EffectCalculator.calculate_damage(player, target, 10,
                                            game_manager=cm.gm, combat_manager=cm)
    assert dmg == 10


def test_отсутствие_rulestack_у_gm_инертно():
    """gm без rulestack (симулятор-стаб) → врезка no-op."""
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    gm = SimpleNamespace(relics=[], stats={})         # нет rulestack
    cm = SimpleNamespace(player=player, gm=gm, add_log_message=lambda _: None)
    dmg = EffectCalculator.calculate_damage(player, target, 10,
                                            game_manager=gm, combat_manager=cm)
    assert dmg == 10


def test_damage_scope_не_трогает_урон_врага():
    """predicate is_player_attack → удар врага по игроку не множится Ставкой."""
    player = Creature("Игрок", 50, 50)
    enemy  = Creature("Враг", 50, 50)
    rs = RuleStack(); rs.push(_dmg_mult_mod(2))
    cm = _cm_with_stack(player, rs)
    # attacker=enemy, не player → is_player_attack False
    dmg = EffectCalculator.calculate_damage(enemy, player, 10,
                                            game_manager=cm.gm, combat_manager=cm)
    assert dmg == 10


def test_gm_владеет_rulestack():
    """GameManager создаёт пустой RuleStack с первого фрейма."""
    from managers.GameManager import GameManager
    gm = GameManager()
    assert isinstance(gm.rulestack, RuleStack)
    assert gm.rulestack.active() == []
