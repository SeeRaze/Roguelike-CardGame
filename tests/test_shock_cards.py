# tests/test_shock_cards.py
# Карты стихии «Молния» (статус Шок) + их интеграция в каталог.
# Архетип микро-атак: Шок навешивается энейблером, дренится ударами.
from core.cards.shock import (
    create_shock_bolt, create_chain_lightning, create_thunder_strike, create_overload,
)
from core.cards.catalog import GENERIC_FACTORIES, get_pool_for_class
from core.rarity import Rarity
from ui.cards.keywords import get_card_keywords
from ui.cards.classifier import classify_card


# ═══════════════════════════════════════════════════════════
# «Разряд» — чистый энейблер Шока
# ═══════════════════════════════════════════════════════════

def test_разряд_накладывает_шок(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    create_shock_bolt().apply(player, enemy)
    assert enemy.shock == 3
    assert enemy.hp == 50          # энейблер сам урона не наносит


def test_разряд_улучшенный_даёт_больше_зарядов(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    card = create_shock_bolt()
    card.upgrade()
    card.apply(player, enemy)
    assert enemy.shock == 4


# ═══════════════════════════════════════════════════════════
# «Серия молний» — мульти-хит пейофф
# ═══════════════════════════════════════════════════════════

def test_серия_молний_без_шока_бьёт_трижды(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    create_chain_lightning().apply(player, enemy)
    assert enemy.hp == 44          # 3 удара × 2 = 6


def test_серия_молний_дренит_все_заряды_шока(make_combat, make_creature):
    # 3 заряда → каждый удар +3: (2+3)×3 = 15 урона, заряды обнулены.
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    enemy.shock = 3
    cm = make_combat(player=player, enemy=enemy)
    create_chain_lightning().apply(player, enemy, cm)
    assert enemy.hp == 35          # 50 - 15
    assert enemy.shock == 0


def test_серия_молний_частичный_шок(make_combat, make_creature):
    # 1 заряд: только первый удар усилен → (2+3) + 2 + 2 = 9.
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    enemy.shock = 1
    cm = make_combat(player=player, enemy=enemy)
    create_chain_lightning().apply(player, enemy, cm)
    assert enemy.hp == 41          # 50 - 9
    assert enemy.shock == 0


# ═══════════════════════════════════════════════════════════
# «Громовой удар» — гибрид (урон + подзарядка Шока)
# ═══════════════════════════════════════════════════════════

def test_громовой_удар_бьёт_и_вешает_шок(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    create_thunder_strike().apply(player, enemy)
    assert enemy.hp == 44          # урон 6
    assert enemy.shock == 2


def test_громовой_удар_редкость_uncommon():
    assert create_thunder_strike().rarity == Rarity.UNCOMMON


# ═══════════════════════════════════════════════════════════
# Интеграция: каталог + глоссарий ключевых слов
# ═══════════════════════════════════════════════════════════

def test_карты_шока_в_общем_пуле():
    assert create_shock_bolt in GENERIC_FACTORIES
    assert create_chain_lightning in GENERIC_FACTORIES
    assert create_thunder_strike in GENERIC_FACTORIES


def test_карты_шока_доступны_любому_классу():
    pool = get_pool_for_class("Rogue")
    assert create_shock_bolt in pool


def test_карта_шока_показывает_ключевое_слово():
    # StatusEffect("shock") → глоссарий тянет тултип из StatusRegistry.
    keywords = get_card_keywords(create_shock_bolt())
    keys = [k for k, _ in keywords]
    assert "shock" in keys


# ═══════════════════════════════════════════════════════════
# «Перегрузка» — карта-детонатор (Электро-взрыв)
# ═══════════════════════════════════════════════════════════

def test_перегрузка_в_общем_пуле():
    assert create_overload in GENERIC_FACTORIES


def test_перегрузка_по_голой_цели_только_урон(make_combat, make_creature):
    # Нет Мокрого/Шока → детонации нет, только базовый урон 3.
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    cm = make_combat(player=player, enemy=enemy)
    create_overload().apply(player, enemy, cm)
    assert enemy.hp == 47          # урон 3


def test_перегрузка_детонирует_мокрый_шок(make_combat, make_creature):
    # Удар 3 (+3 от Шока, заряд 3→2) = 6, затем Электро-взрыв 2×6 = 12.
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    enemy.wet = 2
    enemy.shock = 3
    cm = make_combat(player=player, enemy=enemy)
    create_overload().apply(player, enemy, cm)
    assert enemy.hp == 32          # 50 - 6 - 12
    assert enemy.wet == 0 and enemy.shock == 0


def test_перегрузка_классифицируется_как_shock():
    assert classify_card(create_overload()) == "shock"


def test_перегрузка_показывает_ключевое_слово_детонация():
    keys = [k for k, _ in get_card_keywords(create_overload())]
    assert "detonate" in keys
