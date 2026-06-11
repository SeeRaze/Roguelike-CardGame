# tests/test_players.py
# Проверяем игроков: базовый Player (статы, энергия, колода)
# и классовые пассивы (Warrior, Mage).
from core.players.base import Player
from core.players.warrior import Warrior
from core.players.mage import Mage
from core.players.berserker import Berserker
from core.cards import create_strike, create_boil
from core.cards.catalog import CLASS_FACTORIES, get_pool_for_class


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
    assert w.max_hp == 90
    assert w.max_energy == 3
    assert w.gold == 100
    assert w.active_ability is not None


def test_маг_имеет_правильные_статы():
    m = Mage()
    assert m.name == "Маг"
    assert m.max_hp == 70
    assert m.max_energy == 3
    assert m.gold == 90
    assert m.active_ability is not None


def test_берсерк_имеет_60_hp():
    b = Berserker()
    assert b.max_hp == 60


def test_берсерк_стартдек_содержит_три_сигнатурки_учителя():
    # Стартер раскрывает пассив: 3 сигнатурки граней долга + generic-основа.
    deck = Berserker().get_starter_deck()
    names = [c.name for c in deck]
    assert "Кровавая ярость" in names      # грань долг→урон
    assert "Жажда крови" in names          # грань долг→FP
    assert "Кранч" in names                # грань добил-в-долге→второе дыхание (сустейн)
    assert "Безрассудный удар" not in names  # 4-я сигнатурка — в драфт-пул, не в стартер
    assert len(deck) == 9                   # состав не раздут (−1 strike под Кранч)
    assert names.count("Удар") == 2         # strike: было 3, уступил один Кранчу


# ═══════════════════════════════════════════════════════════
# Warrior — пассив «Железный задел» (перенос 50% щита)
# ═══════════════════════════════════════════════════════════

def test_воин_стартдек_содержит_два_спендера_дисциплины():
    # Де-рельсенный стартер (С56): 2 спендера-учителя + generic-основа, БЕЗ
    # в-стартере билдера/старой оси (они в драфт-пуле).
    deck = Warrior().get_starter_deck()
    names = [c.name for c in deck]
    assert "Карающий строй" in names        # грань Дисц → бурст
    assert "Стена щитов" in names           # грань Дисц → выживаемость
    assert "Возмездие" not in names         # старая ось → драфт-пул
    assert "Стальной заслон" not in names
    assert "Стойка" not in names            # билдер тоже в пул (нет замкнутого лупа)
    assert len(deck) == 11
    assert names.count("Удар") == 4
    assert names.count("Защита") == 4


def test_воин_переносит_щит_в_следующий_ход(make_combat):
    w = Warrior()
    w.shield = 20
    cm = make_combat(player=w)
    w.on_turn_start_passive(cm)
    assert w._passive_shield_carry == 10    # int(20 * 0.5)


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
    cm._combo_triggered = True
    from managers.DeckManager import DeckManager
    cm.deck_manager = DeckManager(m.get_starter_deck())
    before = len(cm.deck_manager.hand)
    m.on_card_played_passive(None, cm)
    after = len(cm.deck_manager.hand)
    assert cm._combo_triggered is False  # флаг сброшен
    assert after == before + 1                 # +1 карта в руку


def test_маг_без_комбо_не_добирает(make_combat):
    m = Mage()
    cm = make_combat(player=m)
    cm._combo_triggered = False
    from managers.DeckManager import DeckManager
    cm.deck_manager = DeckManager(m.get_starter_deck())
    before = len(cm.deck_manager.hand)
    m.on_card_played_passive(None, cm)
    after = len(cm.deck_manager.hand)
    assert after == before                    # ничего не изменилось


# ═══════════════════════════════════════════════════════════
# Mage — де-рельсенный стартдек (С56→С58): ХОТФИКС собирается, не вручён
# ═══════════════════════════════════════════════════════════

def test_маг_стартдек_де_рельсен_хотфикс_не_пред_собран():
    m = Mage()
    deck = m.get_starter_deck()
    names = [c.name for c in deck]
    assert "Разгон" in names                  # гамбл HP → Мастерство
    assert "Резонансный разряд" in names      # выжать глубину Мастерства
    assert "Закипание" not in names           # ХОТФИКС больше НЕ вручён (де-рельс)
    assert "Тайное сосредоточение" not in names  # билдер → драфт-пул
    # половины ХОТФИКС раздельно (собери сам): Кофе + Legacy
    assert "Кофе на клавиатуру" in names and "Костыль" in names
    assert len(deck) == 9


def test_закипание_вешает_и_кофе_и_legacy(make_combat, make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy = make_creature("Враг", 50, 50)
    cm = make_combat(player=player, enemy=enemy)
    card = create_boil()
    card.apply(player, enemy, cm)
    assert enemy.coffee == 3
    assert enemy.legacy == 3


def test_закипание_вешает_оба_статуса_улучшенные(make_combat, make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy = make_creature("Враг", 50, 50)
    cm = make_combat(player=player, enemy=enemy)
    card = create_boil()
    card.upgrade()
    card.apply(player, enemy, cm)
    assert enemy.coffee == 4
    assert enemy.legacy == 4


def test_закипание_не_срабатывает_хотфикс_само_на_себе(make_combat, make_creature):
    """Эффекты в порядке урон→статусы: урон наносится ДО наложения стихий,
    поэтому Закипание НЕ детонирует само-комбо (статусов ещё нет на момент
    DamageEffect). Это чистый сетап — ×2 будет на СЛЕДУЮЩЕЙ атаке."""
    player = make_creature("Игрок", 50, 50)
    enemy = make_creature("Враг", 40, 40)  # 40 HP чтобы пережить урон 5
    cm = make_combat(player=player, enemy=enemy)
    card = create_boil()
    card.apply(player, enemy, cm)
    # Флаг комбо не должен быть выставлен
    assert not getattr(cm, '_combo_triggered', False)


def test_закипание_в_generic_не_в_классе_мага():
    # С57 (чистка под Нестабильность): Закипание (чистый ПАР, 0 Мастерства) переехало
    # из классового пула Мага в GENERIC — стихийный сетап универсален, дублировал generic.
    from core.cards.catalog import GENERIC_FACTORIES
    mage_names = [f.__name__ for f in CLASS_FACTORIES["Mage"]]
    generic_names = [f.__name__ for f in GENERIC_FACTORIES]
    assert "create_boil" not in mage_names
    assert "create_boil" in generic_names


def test_закипание_в_пуле_выдачи_мага():
    # Закипание по-прежнему достижимо Магу — но как generic-карта (в общем пуле).
    pool = get_pool_for_class("Mage")
    tagged_names = [f.__name__ for f in pool]
    assert "create_boil" in tagged_names


# ═══════════════════════════════════════════════════════════
# MagePolicy — компетентный бот (приоритет энейблера)
# ═══════════════════════════════════════════════════════════

def test_mage_policy_приоритет_энейблера_без_статусов(make_combat, make_creature):
    """Враг без стихий → бот играет энейблер для сетапа."""
    from managers.balance.policy import MagePolicy
    policy = MagePolicy()
    player = make_creature("Игрок", 50, 50)
    enemy = make_creature("Враг", 50, 50)
    cm = make_combat(player=player, enemy=enemy)
    boil = create_boil()
    strike = create_strike()
    # Враг чистый — энейблер в приоритете
    chosen = policy.pick_card([boil, strike], cm)
    assert chosen.name == "Закипание"


def test_mage_policy_атака_после_сетапа(make_combat, make_creature):
    """На враге уже coffee+legacy — бот играет атаку для детонации."""
    from managers.balance.policy import MagePolicy
    policy = MagePolicy()
    player = make_creature("Игрок", 50, 50)
    enemy = make_creature("Враг", 50, 50)
    enemy.coffee = 3
    enemy.legacy = 3
    cm = make_combat(player=player, enemy=enemy)
    boil = create_boil()
    strike = create_strike()
    chosen = policy.pick_card([boil, strike], cm)
    assert chosen.name == "Удар"


def test_mage_policy_фолбэк_если_энейблера_нет(make_combat, make_creature):
    """Энейблера нет в руке — бот играет случайно (не падает)."""
    from managers.balance.policy import MagePolicy
    policy = MagePolicy()
    player = make_creature("Игрок", 50, 50)
    enemy = make_creature("Враг", 50, 50)
    cm = make_combat(player=player, enemy=enemy)
    strike1 = create_strike()
    strike2 = create_strike()
    chosen = policy.pick_card([strike1, strike2], cm)
    assert chosen is not None
