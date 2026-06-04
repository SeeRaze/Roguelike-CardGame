# tests/test_air_cards.py
# Карты стихии «Воздух» (механика Поток / FlowEffect) + интеграция в каталог.
# Поток — НЕ статус, а эффект-кирпич: снижает temp_cost случайных карт в руке.
from core.cards.air import (
    FlowEffect, SpreadEffect,
    create_gust, create_updraft, create_whirlwind, create_sirocco,
)
from core.cards.base import Card, DamageEffect
from core.cards.catalog import GENERIC_FACTORIES, get_pool_for_class
from core.rarity import Rarity


# ── Лёгкий стаб боя для FlowEffect (нужны только рука + флаг + лог) ───────────
class _DeckStub:
    def __init__(self, hand):
        self.hand = hand


class _FlowCombat:
    def __init__(self, hand, being_played=None):
        self.deck_manager = _DeckStub(hand)
        self._card_being_played = being_played
        self.log = []

    def add_log_message(self, m):
        self.log.append(m)


def _card(name="Карта", cost=2):
    return Card(name, cost, "attack", "...", [DamageEffect(3, 5)])


# ═══════════════════════════════════════════════════════════
# FlowEffect — снижение temp_cost
# ═══════════════════════════════════════════════════════════

def test_flow_снижает_стоимость_одной_карты():
    hand = [_card("A"), _card("B"), _card("C")]
    cm = _FlowCombat(hand)
    FlowEffect(1, 1).execute(None, None, cm, is_upgraded=False)
    reduced = [c for c in hand if getattr(c, "temp_cost", c.cost) < c.cost]
    assert len(reduced) == 1
    assert reduced[0].temp_cost == 1          # 2 - 1


def test_flow_исключает_разыгрываемую_карту():
    played = _card("Разыгрываемая")
    cm = _FlowCombat([played], being_played=played)
    FlowEffect(1, 1).execute(None, None, cm, is_upgraded=False)
    # Единственная карта в руке — сама разыгрываемая → удешевлять некого.
    assert not hasattr(played, "temp_cost")


def test_flow_не_опускает_стоимость_ниже_нуля():
    c = _card("Дешёвая", cost=1)
    cm = _FlowCombat([c])
    FlowEffect(3, 3).execute(None, None, cm, is_upgraded=False)   # 3 удешевления
    assert c.temp_cost == 0                   # 1 → 0, не уходит в минус


def test_flow_делает_несколько_удешевлений():
    hand = [_card("A", cost=3), _card("B", cost=3)]
    cm = _FlowCombat(hand)
    FlowEffect(2, 2).execute(None, None, cm, is_upgraded=False)
    total_reduction = sum(c.cost - getattr(c, "temp_cost", c.cost) for c in hand)
    assert total_reduction == 2               # суммарно сняли 2 стоимости


def test_flow_улучшенный_снижает_больше():
    hand = [_card("A", cost=3), _card("B", cost=3), _card("C", cost=3)]
    cm = _FlowCombat(hand)
    FlowEffect(2, 3).execute(None, None, cm, is_upgraded=True)    # улучш. = 3
    total_reduction = sum(c.cost - getattr(c, "temp_cost", c.cost) for c in hand)
    assert total_reduction == 3


def test_flow_без_боя_не_падает():
    FlowEffect(1, 1).execute(None, None, None, is_upgraded=False)   # не бросает


# ═══════════════════════════════════════════════════════════
# Карты Воздуха
# ═══════════════════════════════════════════════════════════

def test_порыв_ветра_наносит_урон(make_combat, make_creature):
    # FlowEffect без deck_manager — no-op; проверяем урон.
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    cm = make_combat(player=player, enemy=enemy)
    create_gust().apply(player, enemy, cm)
    assert enemy.hp == 46          # урон 4


def test_вихрь_наносит_урон(make_combat, make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    cm = make_combat(player=player, enemy=enemy)
    create_whirlwind().apply(player, enemy, cm)
    assert enemy.hp == 43          # урон 7


def test_восходящий_поток_удешевляет_две_карты():
    updraft = create_updraft()
    hand = [updraft, _card("A", cost=2), _card("B", cost=2)]
    cm = _FlowCombat(hand, being_played=updraft)
    updraft.apply(None, None, cm)
    total_reduction = sum(c.cost - getattr(c, "temp_cost", c.cost)
                          for c in hand if c is not updraft)
    assert total_reduction == 2    # 2 удешевления среди НЕ-разыгрываемых
    assert not hasattr(updraft, "temp_cost")    # сама себя не трогает


def test_восходящий_поток_редкость_uncommon():
    assert create_updraft().rarity == Rarity.UNCOMMON


# ═══════════════════════════════════════════════════════════
# Интеграция: каталог
# ═══════════════════════════════════════════════════════════

def test_карты_воздуха_в_общем_пуле():
    assert create_gust in GENERIC_FACTORIES
    assert create_updraft in GENERIC_FACTORIES
    assert create_whirlwind in GENERIC_FACTORIES


def test_карты_воздуха_доступны_любому_классу():
    pool = get_pool_for_class("Mage")
    assert create_gust in pool


def test_карта_воздуха_показывает_ключевое_слово_поток():
    from ui.cards.keywords import get_card_keywords
    keys = [k for k, _ in get_card_keywords(create_updraft())]
    assert "flow" in keys


def test_классификатор_относит_карту_воздуха_к_air():
    from ui.cards.classifier import classify_card
    assert classify_card(create_updraft()) == "air"
    assert classify_card(create_gust()) == "air"      # урон + Поток → всё равно air


# ═══════════════════════════════════════════════════════════
# SpreadEffect / «Суховей» — распространение Горения и Яда
# ═══════════════════════════════════════════════════════════

def test_spread_разносит_половину_горения_и_яда(make_combat, make_creature):
    target = make_creature("Цель", 50, 50)
    e2     = make_creature("Враг2", 50, 50)
    e3     = make_creature("Враг3", 50, 50)
    target.ignited = 4
    target.poison = 6
    cm = make_combat(player=make_creature("Игрок", 50, 50), enemy=target)
    cm.enemies = [target, e2, e3]
    SpreadEffect().execute(cm.player, target, cm, is_upgraded=False)
    # На остальных — половина (4//2=2 горения, 6//2=3 яда); цель не тронута.
    assert e2.ignited == 2 and e2.poison == 3
    assert e3.ignited == 2 and e3.poison == 3
    assert target.ignited == 4 and target.poison == 6   # источник сохраняет стаки


def test_spread_без_статусов_ничего_не_делает(make_combat, make_creature):
    target = make_creature("Цель", 50, 50)
    e2     = make_creature("Враг2", 50, 50)
    cm = make_combat(player=make_creature("Игрок", 50, 50), enemy=target)
    cm.enemies = [target, e2]
    SpreadEffect().execute(cm.player, target, cm, is_upgraded=False)
    assert e2.ignited == 0 and e2.poison == 0


def test_суховей_в_общем_пуле():
    assert create_sirocco in GENERIC_FACTORIES


def test_суховей_показывает_ключевые_слова():
    from ui.cards.keywords import get_card_keywords
    keys = [k for k, _ in get_card_keywords(create_sirocco())]
    assert "spread" in keys and "flow" in keys
