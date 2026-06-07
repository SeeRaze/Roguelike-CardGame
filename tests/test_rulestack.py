# tests/test_rulestack.py
# Ядро RuleStack (фундамент «слома игры»): Scope/RuleMod/RuleStack.
# Проверяем диспетч: push/pop, порядок по priority, apply мутирует ctx, predicate-гейт,
# пустой стек = no-op. Чистая логика, без pygame.
from core.rules import RuleStack, RuleMod, Scope


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
