# tests/test_bot_synergy_policy.py
# Синергийный слой политики бота (managers/balance/policy.py): бот осмысленно
# пилотирует синергийные карты из generic-пула (Шок/Раскол/Поток/детонаторы),
# чтобы симулятор мерил баланс честно (см. balance-findings-shock-dilution).
#
# Ключевой инвариант: _synergy_pick срабатывает ТОЛЬКО при наличии синергии в
# руке; иначе возвращает None и выбор падает в _class_pick (random/класс-специфика).
from core.cards.base import Card, DamageEffect
from core.cards.shock import (
    create_shock_bolt, create_chain_lightning, create_overload,
)
from core.cards.earth import create_rockfall
from core.cards.air import create_updraft, create_gust
from managers.balance.policy import BotPolicy, SummonerPolicy, get_policy


def _vanilla(name="Удар", cost=1):
    """Несинергийная карта: чистый урон, ничего не вешает."""
    return Card(name=name, cost=cost, card_type="attack",
                description="Простой урон.", effects=[DamageEffect(5, 7)])


# ═══════════════════════════════════════════════════════════
# Детонатор: жать при готовой детонации, иначе — нет
# ═══════════════════════════════════════════════════════════

def test_детонатор_жмётся_при_готовой_детонации(make_combat, make_creature):
    # Цель Мокрая + под Шоком → готов Электро-взрыв (requires wet+shock).
    enemy = make_creature("Враг", 50, 50)
    enemy.add_status("wet", 2)
    enemy.add_status("shock", 3)
    cm = make_combat(enemy=enemy)
    hand = [_vanilla(), create_overload()]      # «Перегрузка» = детонатор
    pick = BotPolicy()._synergy_pick(hand, cm)
    assert pick is not None and pick.name == "Перегрузка"


def test_детонатор_не_жмётся_без_готовой_детонации(make_combat, make_creature):
    # На цели только Шок — ни одна детонация (нужна пара статусов) не готова.
    enemy = make_creature("Враг", 50, 50)
    enemy.add_status("shock", 3)
    cm = make_combat(enemy=enemy)
    hand = [create_overload()]      # урон+детонация, но детонировать нечего
    pick = BotPolicy()._synergy_pick(hand, cm)
    # shock==3>0, но «Перегрузка» — не чистый энейблер Шока (есть DamageEffect),
    # а детонация не готова → синергийный слой её НЕ выбирает.
    assert pick is None


# ═══════════════════════════════════════════════════════════
# Раскол: энейблер только пока у цели есть щит
# ═══════════════════════════════════════════════════════════

def test_раскол_энейблер_жмётся_при_щите(make_combat, make_creature):
    enemy = make_creature("Враг", 50, 50)
    enemy.shield = 10
    cm = make_combat(enemy=enemy)
    hand = [_vanilla(), create_rockfall()]      # «Камнепад» = чистый энейблер Раскола
    pick = BotPolicy()._synergy_pick(hand, cm)
    assert pick is not None and pick.name == "Камнепад"


def test_раскол_энейблер_не_жмётся_без_щита(make_combat, make_creature):
    enemy = make_creature("Враг", 50, 50)
    enemy.shield = 0                            # без щита Раскол бесполезен
    cm = make_combat(enemy=enemy)
    hand = [create_rockfall()]
    pick = BotPolicy()._synergy_pick(hand, cm)
    assert pick is None


def test_раскол_энейблер_не_дублируется(make_combat, make_creature):
    # Раскол уже висит — повторно вешать не нужно.
    enemy = make_creature("Враг", 50, 50)
    enemy.shield = 10
    enemy.add_status("shatter", 2)
    cm = make_combat(enemy=enemy)
    hand = [create_rockfall()]
    pick = BotPolicy()._synergy_pick(hand, cm)
    assert pick is None


# ═══════════════════════════════════════════════════════════
# Шок: энейблер пока на цели нет заряда
# ═══════════════════════════════════════════════════════════

def test_шок_энейблер_жмётся_при_нуле_заряда(make_combat, make_creature):
    enemy = make_creature("Враг", 50, 50)
    cm = make_combat(enemy=enemy)
    hand = [_vanilla(), create_shock_bolt()]    # «Разряд» = чистый энейблер Шока
    pick = BotPolicy()._synergy_pick(hand, cm)
    assert pick is not None and pick.name == "Разряд"


def test_шок_энейблер_не_дублируется(make_combat, make_creature):
    enemy = make_creature("Враг", 50, 50)
    enemy.add_status("shock", 3)                # заряд уже есть
    cm = make_combat(enemy=enemy)
    hand = [create_shock_bolt(), _vanilla()]
    pick = BotPolicy()._synergy_pick(hand, cm)
    # Шок-энейблер не нужен; детонаций нет, Потока нет → None (бьём в _class_pick).
    assert pick is None


def test_серия_молний_не_энейблер(make_combat, make_creature):
    # «Серия молний» — урон (пейофф), не чистый энейблер: слой её не выбирает как сетап.
    enemy = make_creature("Враг", 50, 50)
    cm = make_combat(enemy=enemy)
    hand = [create_chain_lightning()]
    pick = BotPolicy()._synergy_pick(hand, cm)
    assert pick is None


# ═══════════════════════════════════════════════════════════
# Поток: чистый энейблер рано, если есть что удешевлять
# ═══════════════════════════════════════════════════════════

def test_поток_энейблер_жмётся_при_запасной_карте(make_combat, make_creature):
    cm = make_combat()
    hand = [create_updraft(), _vanilla()]       # «Восходящий поток» = чистый Поток
    pick = BotPolicy()._synergy_pick(hand, cm)
    assert pick is not None and pick.name == "Восходящий поток"


def test_поток_энейблер_не_жмётся_без_запасной_карты(make_combat):
    cm = make_combat()
    hand = [create_updraft()]                   # удешевлять нечего (карта одна)
    pick = BotPolicy()._synergy_pick(hand, cm)
    assert pick is None


def test_поток_с_уроном_не_энейблер(make_combat):
    # «Порыв ветра» — урон + Поток: не чистый энейблер, слой не трогает как сетап.
    cm = make_combat()
    hand = [create_gust(), _vanilla()]
    pick = BotPolicy()._synergy_pick(hand, cm)
    assert pick is None


# ═══════════════════════════════════════════════════════════
# Фолбэк: без синергии слой молчит, выбор делает _class_pick
# ═══════════════════════════════════════════════════════════

def test_без_синергии_слой_возвращает_none(make_combat):
    cm = make_combat()
    hand = [_vanilla("Удар1"), _vanilla("Удар2")]
    assert BotPolicy()._synergy_pick(hand, cm) is None


def test_pick_card_фолбэк_в_class_pick(make_combat):
    # Без синергии pick_card обязан вернуть карту из руки (через _class_pick=random).
    cm = make_combat()
    hand = [_vanilla("Удар1"), _vanilla("Удар2")]
    pick = BotPolicy().pick_card(hand, cm)
    assert pick in hand


def test_class_pick_достижим_у_подкласса(make_combat):
    # Синергия имеет приоритет, но без неё отрабатывает класс-специфика.
    # SummonerPolicy._class_pick без призывов возвращает случайную карту из руки.
    cm = make_combat()
    hand = [_vanilla("Удар1"), _vanilla("Удар2")]
    pick = SummonerPolicy().pick_card(hand, cm)
    assert pick in hand


def test_синергия_приоритетнее_класс_специфики(make_combat, make_creature):
    # У Summoner в руке Шок-энейблер по цели без заряда → синергия побеждает random.
    enemy = make_creature("Враг", 50, 50)
    cm = make_combat(enemy=enemy)
    hand = [_vanilla(), create_shock_bolt()]
    pick = SummonerPolicy().pick_card(hand, cm)
    assert pick.name == "Разряд"


def test_get_policy_возвращает_экземпляр_политики():
    assert isinstance(get_policy("Druid"), BotPolicy)
    assert isinstance(get_policy("НесуществующийКласс"), BotPolicy)
