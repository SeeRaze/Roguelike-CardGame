# tests/test_cleave.py
# Сплеш-урон по соседним клеткам — первый потребитель 2D-субстрата позиционки (§1).
from core.players.warrior import Warrior
from core.enemies.cultist import Cultist
from core.cards.base import DamageEffect
from core.cards.cleave import SplashDamageEffect, create_cleaving_strike
from managers.CombatManager import CombatManager


def _make_cm(n_enemies, positioning):
    """Бой с n врагами; positioning=True расставит их на сетке (рангы/линии)."""
    p = Warrior()
    p.positioning_enabled = positioning
    enemies = [Cultist(f"E{i}", 50, 50) for i in range(n_enemies)]
    cm = CombatManager(p, enemies, [create_cleaving_strike()])
    return p, enemies, cm


def test_splash_наследует_DamageEffect():
    """isinstance-совместимость: бот/синергия/снимок видят сплеш как атаку."""
    assert isinstance(SplashDamageEffect(6, 8), DamageEffect)


def test_карта_рассекающий_удар_несёт_splash():
    card = create_cleaving_strike()
    assert any(isinstance(e, SplashDamageEffect) for e in card.effects)
    assert card.card_type == "attack"


def test_сплеш_задевает_соседей_при_позиционке():
    """3 врага на сетке: фронт-ЦЕНТР (E0) соседствует с фронт-ЛЕВО (E1, Δлиния)
    и тыл-ЦЕНТР (E2, Δранг). Удар по E0 → сплеш по обоим соседям."""
    p, enemies, cm = _make_cm(3, positioning=True)
    e0, e1, e2 = enemies
    # E0 — фронт-ЦЕНТР (первая половина группы, ЦЕНТР первым в порядке заливки).
    SplashDamageEffect(10, 12).execute(p, e0, cm, is_upgraded=False)
    assert e0.hp < 50          # цель — полный урон
    assert e1.hp < 50          # сосед по линии — сплеш
    assert e2.hp < 50          # сосед по рангу — сплеш
    # Сплеш (50%) слабее первичного удара.
    assert (50 - e1.hp) < (50 - e0.hp)


def test_без_позиционки_бьёт_только_цель():
    """Позиционка off → у врагов нет рангов/линий → neighbors пуст → одиночный удар
    (single-target fallback, поведение как обычный DamageEffect)."""
    p, enemies, cm = _make_cm(3, positioning=False)
    e0, e1, e2 = enemies
    SplashDamageEffect(10, 12).execute(p, e0, cm, is_upgraded=False)
    assert e0.hp < 50          # цель получила урон
    assert e1.hp == 50         # соседи нетронуты
    assert e2.hp == 50
