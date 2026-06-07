# tests/test_fusion.py
# Чистый механизм Card Fusion (§2 этап 1): fuse_cards / fused_cost / higher_rarity.
from core.fusion import fuse_cards, fused_cost, higher_rarity, FUSED_COST_FLOOR
from core.cards.base import Card, DamageEffect, ShieldEffect
from core.rarity import Rarity


def _card(name, cost, ctype="attack", effects=None, rarity=Rarity.COMMON, exile=False):
    return Card(name=name, cost=cost, card_type=ctype,
                description=f"desc {name}", effects=effects or [DamageEffect(5, 7)],
                rarity=rarity, exile=exile)


# ── стоимость ────────────────────────────────────────────────────────────────────

def test_fused_cost_max_с_полом():
    assert fused_cost(_card("A", 1), _card("B", 3)) == 3   # max
    assert fused_cost(_card("A", 2), _card("B", 2)) == 2
    assert fused_cost(_card("A", 0), _card("B", 0)) == FUSED_COST_FLOOR  # пол убивает 0-абуз
    assert fused_cost(_card("A", 0), _card("B", 3)) == 3


def test_fused_cost_никогда_не_выше_дороже_источника():
    """Гарантия играбельности: Глитч не дороже самой дорогой из двух карт."""
    for a in range(0, 4):
        for b in range(0, 4):
            c = fused_cost(_card("A", a), _card("B", b))
            assert c <= max(a, b) or c == FUSED_COST_FLOOR


# ── редкость (Rarity = Enum строк, НЕ упорядочен) ─────────────────────────────────

def test_higher_rarity_по_тиру_не_по_строке():
    assert higher_rarity(Rarity.COMMON, Rarity.EPIC) == Rarity.EPIC
    assert higher_rarity(Rarity.RARE, Rarity.UNCOMMON) == Rarity.RARE
    # "common" > "uncommon" по алфавиту — проверяем, что НЕ строкой сравниваем
    assert higher_rarity(Rarity.COMMON, Rarity.UNCOMMON) == Rarity.UNCOMMON


# ── слияние ──────────────────────────────────────────────────────────────────────

def test_эффекты_конкатенируются():
    a = _card("Удар", 1, effects=[DamageEffect(6, 8)])
    b = _card("Защита", 1, "defend", effects=[ShieldEffect(5, 7)])
    g = fuse_cards(a, b)
    assert len(g.effects) == 2
    assert g.effects[0] is a.effects[0]   # порядок a, затем b; переиспользование по ссылке
    assert g.effects[1] is b.effects[0]


def test_слияние_не_мутирует_источники():
    a = _card("Удар", 1, effects=[DamageEffect(6, 8)])
    b = _card("Яд", 2, effects=[DamageEffect(3, 4)])
    fuse_cards(a, b)
    assert len(a.effects) == 1 and len(b.effects) == 1
    assert a.cost == 1 and b.cost == 2


def test_глитч_метаданные():
    a = _card("Удар", 1, "attack", rarity=Rarity.COMMON)
    b = _card("Бастион", 3, "defend", rarity=Rarity.RARE)
    g = fuse_cards(a, b)
    assert g.name == "Удар+Бастион"
    assert g.cost == 3                       # max(1,3)
    assert g.rarity == Rarity.RARE           # выше из двух
    assert g.card_type == "attack"           # типы разные → attack
    assert g.is_fused is True
    assert g.fused_from == ("Удар", "Бастион")
    assert g.upgraded is False               # прокачка сброшена


def test_тип_общий_если_совпадает():
    g = fuse_cards(_card("A", 1, "defend", effects=[ShieldEffect(5, 7)]),
                   _card("B", 1, "defend", effects=[ShieldEffect(3, 4)]))
    assert g.card_type == "defend"


def test_имя_без_апгрейд_суффикса():
    a = _card("Удар", 1); a.upgrade()        # имя становится "Удар+"
    g = fuse_cards(a, _card("Яд", 1))
    assert g.name == "Удар+Яд"               # суффикс прокачки убран


def test_изгнание_наследуется_если_у_любого():
    g = fuse_cards(_card("A", 1, exile=True), _card("B", 1, exile=False))
    assert g.exile is True
    g2 = fuse_cards(_card("A", 1, exile=False), _card("B", 1, exile=False))
    assert g2.exile is False


def test_глитч_играбелен_как_карта():
    """Слитая карта — обычный Card: apply прогоняет ОБА набора эффектов (урон + щит)
    на реальных игроке/враге."""
    from core.players.warrior import Warrior
    from core.enemies.cultist import Cultist
    a = _card("Удар", 1, effects=[DamageEffect(6, 8)])
    b = _card("Защита", 1, "defend", effects=[ShieldEffect(5, 7)])
    g = fuse_cards(a, b)
    p = Warrior()
    e = Cultist("Цель", 50, 50)
    shield_before = p.shield
    g.apply(p, e, None)
    assert e.hp < 50                      # урон прошёл
    assert p.shield > shield_before       # щит прошёл
