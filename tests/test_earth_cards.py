# tests/test_earth_cards.py
# Карты стихии «Земля» (статус Раскол) + их интеграция в каталог.
# Архетип контры броне: Раскол навешивается энейблером, множит урон по щиту ×3.
from core.cards.earth import (
    create_rockfall, create_crush, create_tectonic_strike,
)
from core.cards.catalog import GENERIC_FACTORIES, get_pool_for_class
from core.rarity import Rarity
from ui.cards.keywords import get_card_keywords


# ═══════════════════════════════════════════════════════════
# «Камнепад» — чистый энейблер Раскола
# ═══════════════════════════════════════════════════════════

def test_камнепад_накладывает_раскол(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    create_rockfall().apply(player, enemy)
    assert enemy.shatter == 2
    assert enemy.hp == 50          # энейблер сам урона не наносит


def test_камнепад_улучшенный_держится_дольше(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    card = create_rockfall()
    card.upgrade()
    card.apply(player, enemy)
    assert enemy.shatter == 3


# ═══════════════════════════════════════════════════════════
# «Дробящий удар» — дешёвый эксплойт Раскола
# ═══════════════════════════════════════════════════════════

def test_дробящий_удар_по_голой_цели(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    create_crush().apply(player, enemy)
    assert enemy.hp == 46          # урон 4, щита/Раскола нет


def test_дробящий_удар_крушит_щит_через_раскол(make_combat, make_creature):
    # Раскол + щит → урон ×3: 4 → 12 по щиту.
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    enemy.shatter = 2
    enemy.shield = 20
    cm = make_combat(player=player, enemy=enemy)
    create_crush().apply(player, enemy, cm)
    assert enemy.shield == 8        # 20 - 12
    assert enemy.hp == 50
    assert enemy.shatter == 2       # длительность не тратится при ударе


def test_дробящий_удар_без_щита_не_усилен(make_combat, make_creature):
    # Раскол есть, но щита нет → множитель не применяется.
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    enemy.shatter = 2
    enemy.shield = 0
    cm = make_combat(player=player, enemy=enemy)
    create_crush().apply(player, enemy, cm)
    assert enemy.hp == 46           # обычные 4


# ═══════════════════════════════════════════════════════════
# «Тектонический удар» — гибрид (урон + наложение Раскола)
# ═══════════════════════════════════════════════════════════

def test_тектонический_удар_бьёт_и_вешает_раскол(make_creature):
    player = make_creature("Игрок", 50, 50)
    enemy  = make_creature("Враг", 50, 50)
    create_tectonic_strike().apply(player, enemy)
    assert enemy.hp == 44          # урон 6 (щита нет → без ×3)
    assert enemy.shatter == 2


def test_тектонический_удар_редкость_uncommon():
    assert create_tectonic_strike().rarity == Rarity.UNCOMMON


# ═══════════════════════════════════════════════════════════
# Интеграция: каталог + глоссарий ключевых слов
# ═══════════════════════════════════════════════════════════

def test_карты_земли_в_общем_пуле():
    assert create_rockfall in GENERIC_FACTORIES
    assert create_crush in GENERIC_FACTORIES
    assert create_tectonic_strike in GENERIC_FACTORIES


def test_карты_земли_доступны_любому_классу():
    pool = get_pool_for_class("Warrior")
    assert create_rockfall in pool


def test_карта_земли_показывает_ключевое_слово():
    keywords = get_card_keywords(create_rockfall())
    keys = [k for k, _ in keywords]
    assert "shatter" in keys
