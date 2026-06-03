# tests/test_players.py
# Проверяем игроков: базовый Player (статы, энергия, колода)
# и классовые пассивы (Warrior, Mage, Druid).
from core.Creature import Creature
from core.players.base import Player
from core.players.warrior import Warrior
from core.players.mage import Mage
from core.players.druid import Druid
from core.players.rogue import Rogue
from core.players.berserker import Berserker
from core.cards import create_strike


# Заглушка-фабрика колоды для тестов
def _test_deck():
    return [create_strike(), create_strike()]


# ═══════════════════════════════════════════════════════════
# Player — базовая логика
# ═══════════════════════════════════════════════════════════

def test_создание_игрока_инициализирует_все_поля():
    p = Player("Тест", max_hp=100, max_energy=5, gold=50,
               starter_deck_factory=_test_deck)
    assert p.name == "Тест"
    assert p.hp == 100
    assert p.max_hp == 100
    assert p.max_energy == 5
    assert p.energy == 5              # полная энергия при старте
    assert p.gold == 50
    assert p.active_ability is None


def test_get_starter_deck_возвращает_колоду_из_фабрики():
    p = Player("Тест", max_hp=100, max_energy=5, gold=50,
               starter_deck_factory=_test_deck)
    deck = p.get_starter_deck()
    assert len(deck) == 2
    assert deck[0].name == "Удар"


def test_add_to_starter_deck_добавляет_карту():
    p = Player("Тест", max_hp=100, max_energy=5, gold=50,
               starter_deck_factory=_test_deck)
    p.add_to_starter_deck(create_strike())
    deck = p.get_starter_deck()
    assert len(deck) == 3             # 2 фабричных + 1 добавленная


def test_reset_energy_восстанавливает_до_максимума():
    p = Player("Тест", max_hp=100, max_energy=5, gold=50,
               starter_deck_factory=_test_deck)
    p.energy = 1
    p.reset_energy()
    assert p.energy == 5


def test_use_energy_тратит_энергию():
    p = Player("Тест", max_hp=100, max_energy=5, gold=50,
               starter_deck_factory=_test_deck)
    p.use_energy(2)
    assert p.energy == 3


def test_use_energy_не_уходит_ниже_нуля():
    p = Player("Тест", max_hp=100, max_energy=5, gold=50,
               starter_deck_factory=_test_deck)
    p.use_energy(10)
    assert p.energy == 0


# ═══════════════════════════════════════════════════════════
# Конкретные классы — статы и экипировка
# ═══════════════════════════════════════════════════════════

def test_воин_имеет_правильные_статы():
    w = Warrior()
    assert w.name == "Воин"
    assert w.max_hp == 80
    assert w.max_energy == 3
    assert w.gold == 100
    assert w.active_ability is not None


def test_маг_имеет_правильные_статы():
    m = Mage()
    assert m.name == "Маг"
    assert m.max_hp == 55
    assert m.max_energy == 3
    assert m.gold == 90
    assert m.active_ability is not None


def test_друид_имеет_правильные_статы():
    d = Druid()
    assert d.name == "Друид"
    assert d.max_hp == 70
    assert d.max_energy == 3
    assert d.gold == 100
    assert d.active_ability is not None


def test_разбойник_имеет_4_энергии():
    r = Rogue()
    assert r.max_energy == 4


def test_берсерк_имеет_60_hp():
    b = Berserker()
    assert b.max_hp == 60


# ═══════════════════════════════════════════════════════════
# Warrior — пассив «Железный задел» (перенос 30% щита)
# ═══════════════════════════════════════════════════════════

def test_воин_переносит_щит_в_следующий_ход(make_combat):
    w = Warrior()
    w.shield = 20
    cm = make_combat(player=w)
    w.on_turn_start_passive(cm)
    assert w._passive_shield_carry == 6     # int(20 * 0.3)


def test_воин_без_щита_переносит_ноль(make_combat):
    w = Warrior()
    w.shield = 0
    cm = make_combat(player=w)
    w.on_turn_start_passive(cm)
    assert w._passive_shield_carry == 0


def test_воин_пишет_в_лог_о_переносе(make_combat):
    w = Warrior()
    w.shield = 10
    cm = make_combat(player=w)
    w.on_turn_start_passive(cm)
    assert any("Железный задел" in msg for msg in cm.log)


# ═══════════════════════════════════════════════════════════
# Mage — пассив «Стихийный резонанс» (+1 карта при комбо ПАР)
# ═══════════════════════════════════════════════════════════

def test_маг_добирает_карту_при_комбо_пар(make_combat):
    m = Mage()
    cm = make_combat(player=m)
    # Имитируем: в колоде есть карты, комбо-флаг поднят
    cm._steam_combo_triggered = True
    from managers.DeckManager import DeckManager
    cm.deck_manager = DeckManager(m.get_starter_deck())
    before = len(cm.deck_manager.hand)
    m.on_card_played_passive(None, cm)
    after = len(cm.deck_manager.hand)
    assert cm._steam_combo_triggered is False  # флаг сброшен
    assert after == before + 1                 # +1 карта в руку


def test_маг_без_комбо_не_добирает(make_combat):
    m = Mage()
    cm = make_combat(player=m)
    cm._steam_combo_triggered = False
    from managers.DeckManager import DeckManager
    cm.deck_manager = DeckManager(m.get_starter_deck())
    before = len(cm.deck_manager.hand)
    m.on_card_played_passive(None, cm)
    after = len(cm.deck_manager.hand)
    assert after == before                    # ничего не изменилось


# ═══════════════════════════════════════════════════════════
# Druid — пассив «Токсичный круговорот» (хил → яд на врага)
# ═══════════════════════════════════════════════════════════

def test_друид_при_хиле_травит_врага(make_combat):
    d = Druid()
    cm = make_combat(player=d)
    cm.enemy.poison = 1
    d.on_heal_passive(5, cm)
    assert cm.enemy.poison == 6            # было 1 + хил 5


def test_друид_не_травит_при_нулевом_хиле(make_combat):
    d = Druid()
    cm = make_combat(player=d)
    cm.enemy.poison = 1
    d.on_heal_passive(0, cm)
    assert cm.enemy.poison == 1            # без изменений


def test_друид_не_травит_мёртвого_врага(make_combat):
    d = Druid()
    cm = make_combat(player=d)
    cm.enemy.hp = 0                        # враг мёртв
    cm.enemy.poison = 1
    d.on_heal_passive(5, cm)
    assert cm.enemy.poison == 1            # без изменений
