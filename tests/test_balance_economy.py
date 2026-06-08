# tests/test_balance_economy.py
# Экономика симулятора (managers/balance/economy.py + параметризация runner).
# Шаг №6 фреймворка: золото + удаление карт как измеримый рычаг прореживания.
# Тестируем строительные блоки (формула золота, политика удаления, цена,
# регресс-нейтральность), а не статистику забегов.
import random

from core.cards.base import Card, DamageEffect, ShieldEffect
from managers.balance import runner
from managers.balance.economy import (
    EconomyPolicy, gold_reward, _removal_target, _has_crown,
)
from core.players import Warrior


def _atk(name, dmg, cost):
    return Card(name=name, cost=cost, card_type="attack",
                description="", effects=[DamageEffect(dmg, dmg + 2)])


class _FakeGM:
    """Минимальный gm для тестов экономики: зеркало полей _StubGM."""
    def __init__(self, gold=100, floor=1, removals=0, relics=None):
        self.player_gold   = gold
        self.current_floor = floor
        self.removal_count = removals
        self.relics        = relics if relics is not None else []

    def get_removal_price(self):
        base = (15 + self.current_floor * 2) + self.removal_count * 25
        if any(r.name == "Проклятая Корона" for r in self.relics):
            base *= 2
        return base


class _Relic:
    def __init__(self, name):
        self.name = name


# ═══════════════════════════════════════════════════════════
# gold_reward: зеркало RewardManager.build_rewards
# ═══════════════════════════════════════════════════════════

def test_gold_базовая_формула():
    random.seed(0)
    g = gold_reward(floor=10, is_elite=False, has_crown=False)
    # randint(20,35) + floor*3 → диапазон 50..65 на этаже 10.
    assert 50 <= g <= 65


def test_gold_корона_обнуляет():
    assert gold_reward(floor=50, is_elite=True, has_crown=True) == 0


def test_gold_элита_множит():
    random.seed(1)
    base = gold_reward(floor=5, is_elite=False, has_crown=False)
    random.seed(1)
    elite = gold_reward(floor=5, is_elite=True, has_crown=False)
    assert elite == int(base * 1.5)


# ═══════════════════════════════════════════════════════════
# EconomyPolicy.on_combat_won: начисление золота
# ═══════════════════════════════════════════════════════════

def test_on_combat_won_копит_золото():
    gm = _FakeGM(gold=100, floor=3)
    random.seed(7)
    EconomyPolicy().on_combat_won(gm, floor=3)
    assert gm.player_gold > 100


def test_on_combat_won_корона_не_даёт_золота():
    gm = _FakeGM(gold=100, floor=3, relics=[_Relic("Проклятая Корона")])
    EconomyPolicy().on_combat_won(gm, floor=3)
    assert gm.player_gold == 100


# ═══════════════════════════════════════════════════════════
# _removal_target: слабейшая, при равенстве — нетематичная
# ═══════════════════════════════════════════════════════════

def test_removal_target_берёт_слабейшую():
    weak = _atk("Слабая", 2, 1)        # score 2
    strong = _atk("Сильная", 12, 1)    # score 12
    assert _removal_target([weak, strong], set()) is weak


def test_removal_target_при_равной_силе_нетематичная():
    # Две карты РАВНОЙ силы (score 7.0): одна в теме (attack), другая — щит.
    themed = _atk("Тематичная", 7, 1)                          # attack, score 7.0
    off = Card(name="Вне темы", cost=1, card_type="skill",
               description="", effects=[ShieldEffect(10, 12)])  # shield, 0.7*10=7.0
    # При равной силе тай-брейк режет нетематичную (не ломаем архетип).
    target = _removal_target([themed, off], {"attack"})
    assert target is off


def test_removal_target_пустая_колода_none():
    assert _removal_target([], set()) is None


# ═══════════════════════════════════════════════════════════
# EconomyPolicy.between_acts: трата на удаление
# ═══════════════════════════════════════════════════════════

def test_between_acts_удаляет_слабейшую_когда_по_карману():
    gm = _FakeGM(gold=500, floor=1)
    deck = [_atk("Мусор", 1, 1)] + [_atk(f"X{i}", 8, 1) for i in range(6)]
    before = len(deck)
    EconomyPolicy().between_acts(gm, deck, "Warrior")
    assert len(deck) == before - 1
    assert all(c.name != "Мусор" for c in deck)   # удалили слабейшую
    assert gm.removal_count == 1
    assert gm.player_gold < 500                    # списали цену


def test_between_acts_без_золота_не_удаляет():
    gm = _FakeGM(gold=0, floor=1)
    deck = [_atk(f"X{i}", 5, 1) for i in range(6)]
    EconomyPolicy().between_acts(gm, deck, "Warrior")
    assert len(deck) == 6
    assert gm.removal_count == 0


def test_between_acts_не_оголяет_колоду():
    gm = _FakeGM(gold=9999, floor=1)
    deck = [_atk(f"X{i}", 5, 1) for i in range(EconomyPolicy.MIN_DECK_SIZE)]
    EconomyPolicy().between_acts(gm, deck, "Warrior")
    # Колода ровно на пороге MIN_DECK_SIZE → не трогаем.
    assert len(deck) == EconomyPolicy.MIN_DECK_SIZE
    assert gm.removal_count == 0


def test_between_acts_уважает_лимит_за_акт():
    gm = _FakeGM(gold=99999, floor=1)
    deck = [_atk(f"X{i}", i + 1, 1) for i in range(10)]
    EconomyPolicy().between_acts(gm, deck, "Warrior")
    # MAX_REMOVALS_PER_ACT=1 → не более одного удаления за вызов.
    assert gm.removal_count == EconomyPolicy.MAX_REMOVALS_PER_ACT


def test_between_acts_корона_удваивает_цену():
    # С Короной цена удаления вдвое выше → при пограничном золоте удаления нет.
    deck = [_atk(f"X{i}", 5, 1) for i in range(6)]
    price_no_crown = _FakeGM(floor=1).get_removal_price()      # 17
    gm = _FakeGM(gold=price_no_crown, floor=1,
                 relics=[_Relic("Проклятая Корона")])           # цена 34
    EconomyPolicy().between_acts(gm, deck, "Warrior")
    assert gm.removal_count == 0          # не хватило на удвоенную цену


def test_has_crown_детект():
    assert _has_crown(_FakeGM(relics=[_Relic("Проклятая Корона")]))
    assert not _has_crown(_FakeGM(relics=[_Relic("Другое")]))


# ═══════════════════════════════════════════════════════════
# Закалка на ЗОЛОТЕ (С57): чистая core.temper + EconomyPolicy.temper
# ═══════════════════════════════════════════════════════════

class _FakeForgePlayer:
    """Игрок для Закалки: EconomyPolicy лениво проставит ковочные поля сам."""
    def __init__(self, max_hp=100):
        self.max_hp = max_hp
        self.hp = max_hp


def test_core_temper_чистая_функция_золото():
    from core.forge import temper, TEMPER_GOLD_COST, TEMPER_HP_PCT
    p = _FakeForgePlayer(max_hp=100)
    # Хватает золота → +20% max HP + полный хил, вернуть потраченное.
    ok, spent = temper(p, gold_available=TEMPER_GOLD_COST)
    assert ok is True
    assert spent == TEMPER_GOLD_COST
    assert p.max_hp == 100 + int(100 * TEMPER_HP_PCT)
    assert p.hp == p.max_hp
    # core.temper НЕ списывает золото сам (чистая) — только сигналит сколько.


def test_core_temper_не_хватает_золота_noop():
    from core.forge import temper, TEMPER_GOLD_COST
    p = _FakeForgePlayer(max_hp=100)
    ok, spent = temper(p, gold_available=TEMPER_GOLD_COST - 1)
    assert ok is False
    assert spent == 0
    assert p.max_hp == 100                          # не тронут


def test_economy_temper_списывает_золото_с_gm():
    from core.forge import TEMPER_GOLD_COST, TEMPER_HP_PCT
    gm = _FakeGM(gold=TEMPER_GOLD_COST + 5)
    p = _FakeForgePlayer(max_hp=80)
    assert EconomyPolicy.temper(gm, p) is True
    assert gm.player_gold == 5                       # списано ровно TEMPER_GOLD_COST
    assert p.max_hp == 80 + int(80 * TEMPER_HP_PCT)


def test_economy_temper_без_золота_noop():
    from core.forge import TEMPER_GOLD_COST
    gm = _FakeGM(gold=TEMPER_GOLD_COST - 1)
    p = _FakeForgePlayer(max_hp=80)
    assert EconomyPolicy.temper(gm, p) is False
    assert gm.player_gold == TEMPER_GOLD_COST - 1
    assert p.max_hp == 80


def test_economy_temper_if_threatened_калит_под_угрозой():
    # Малый max_hp → угроза следующего акта превышает порог → калит, пока есть
    # золото (но max_hp растёт → угроза падает: самоограничение). max_hp=50:
    # прирост ненулевой (int(50*0.2)=10) И порог срабатывает на эт.19.
    from core.forge import TEMPER_GOLD_COST
    gm = _FakeGM(gold=TEMPER_GOLD_COST * 3 + 5)
    p = _FakeForgePlayer(max_hp=50)
    did = EconomyPolicy().temper_if_threatened(gm, p, floor=19)
    assert did is True
    assert gm.player_gold < TEMPER_GOLD_COST * 3 + 5   # потратила золото
    assert p.max_hp > 50                                 # выросла живучесть


def test_economy_temper_if_threatened_safe_noop():
    # Огромный max_hp → угроза ниже порога → не калит (золото цело).
    from core.forge import TEMPER_GOLD_COST
    gm = _FakeGM(gold=TEMPER_GOLD_COST * 3)
    p = _FakeForgePlayer(max_hp=10_000_000)
    assert EconomyPolicy().temper_if_threatened(gm, p, floor=1) is False
    assert gm.player_gold == TEMPER_GOLD_COST * 3


# ═══════════════════════════════════════════════════════════
# Интеграция в runner: регресс-нейтральность + работа экономики
# ═══════════════════════════════════════════════════════════

def test_run_single_run_без_economy_регресс_нейтрален():
    """economy=None (дефолт) → поведение бит-в-бит как раньше (тот же seed)."""
    random.seed(42)
    a = runner.run_single_run(Warrior, max_floor=5)
    random.seed(42)
    b = runner.run_single_run(Warrior, max_floor=5, economy=None)
    assert a == b


def test_run_single_run_с_economy_не_падает():
    """С EconomyPolicy забег проходит и возвращает корректную структуру."""
    random.seed(3)
    res = runner.run_single_run(Warrior, max_floor=25, economy=EconomyPolicy())
    assert set(res.keys()) == {"death_floor", "hp_by_floor"}
    assert res["hp_by_floor"]


def test_stub_gm_имеет_экономические_поля():
    """_StubGM зеркалит экономику GameManager (gold/keys/removal_count + цена)."""
    gm = runner._StubGM()
    assert gm.player_gold == 100
    assert gm.player_keys == 0
    assert gm.removal_count == 0
    # Цена удаления = зеркало GameManager.
    assert gm.get_removal_price() == 15 + 1 * 2 + 0 * 25
