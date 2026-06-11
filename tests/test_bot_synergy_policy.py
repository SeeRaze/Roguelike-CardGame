# tests/test_bot_synergy_policy.py
# Синергийный слой политики бота (managers/balance/policy.py): бот осмысленно
# пилотирует синергийные карты из generic-пула (детонаторы/Поток), чтобы
# симулятор мерил баланс честно (см. balance-findings-shock-dilution).
#
# Ключевой инвариант: _synergy_pick срабатывает ТОЛЬКО при наличии синергии в
# руке; иначе возвращает None и выбор падает в _class_pick (random/класс-специфика).
# NB (С58): сетапы Раскола/Шока удалены вместе со статусами; детонации переехали на
# позвоночник detonate() — синергия по НОВЫМ стихиям re-bless в G1.
from core.cards.base import Card, DamageEffect
from core.cards.air import create_updraft, create_gust
from managers.balance.policy import BotPolicy, WarriorPolicy, get_policy


def _vanilla(name="Удар", cost=1):
    """Несинергийная карта: чистый урон, ничего не вешает."""
    return Card(name=name, cost=cost, card_type="attack",
                description="Простой урон.", effects=[DamageEffect(5, 7)])


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
    # _class_pick подкласса без синергии возвращает случайную карту из руки.
    cm = make_combat()
    hand = [_vanilla("Удар1"), _vanilla("Удар2")]
    pick = WarriorPolicy().pick_card(hand, cm)
    assert pick in hand


def test_синергия_приоритетнее_класс_специфики(make_combat, make_creature):
    # В руке чистый энейблер Потока + запасная карта → синергия
    # (удешевление) побеждает random выбор _class_pick.
    enemy = make_creature("Враг", 50, 50)
    cm = make_combat(enemy=enemy)
    hand = [_vanilla(), create_updraft()]
    pick = WarriorPolicy().pick_card(hand, cm)
    assert pick.name == "Восходящий поток"


def test_get_policy_возвращает_экземпляр_политики():
    assert isinstance(get_policy("Mage"), BotPolicy)
    assert isinstance(get_policy("НесуществующийКласс"), BotPolicy)
