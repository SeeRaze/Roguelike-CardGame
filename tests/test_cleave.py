# tests/test_cleave.py
# Сплеш-урон по соседним клеткам — первый потребитель 2D-субстрата позиционки (§1).
from core.players.warrior import Warrior
from core.enemies.cultist import Cultist
from core.cards.base import DamageEffect
from core.cards.cleave import (
    SplashDamageEffect, ColumnStrikeEffect, RankStrikeEffect,
    create_cleaving_strike, create_piercing_thrust, create_wide_swing,
)
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


# ── column / same_rank потребители (§1-добивка) ──────────────────────────────────

def test_column_все_наследуют_DamageEffect():
    assert isinstance(ColumnStrikeEffect(6, 8), DamageEffect)
    assert isinstance(RankStrikeEffect(6, 8), DamageEffect)


def test_прокол_бьёт_всю_колонку_сквозь_перехват():
    """3 врага: E0 фронт-ЦЕНТР, E1 фронт-ЛЕВО, E2 тыл-ЦЕНТР. Колонка ЦЕНТР = E0+E2.
    «Прокол» по E0 пробивает в тыл (E2), но НЕ задевает другую линию (E1)."""
    p, enemies, cm = _make_cm(3, positioning=True)
    e0, e1, e2 = enemies
    ColumnStrikeEffect(10, 12).execute(p, e0, cm, is_upgraded=False)
    assert e0.hp < 50          # цель
    assert e2.hp < 50          # тыл той же колонки — пробит
    assert e1.hp == 50         # другая линия — не задета


def test_размах_бьёт_весь_ряд():
    """Ряд ФРОНТ = E0+E1 (оба фронт). «Размах» по E0 задевает E1, но не тыл (E2)."""
    p, enemies, cm = _make_cm(3, positioning=True)
    e0, e1, e2 = enemies
    RankStrikeEffect(10, 12).execute(p, e0, cm, is_upgraded=False)
    assert e0.hp < 50          # цель
    assert e1.hp < 50          # сосед по шеренге фронта
    assert e2.hp == 50         # тыл — не задет


def test_column_rank_без_позиционки_одиночная_цель():
    """КРИТИЧНО: позиционка off → line/rank == None → колонка/ряд НЕ должны
    схлопнуться во «всех врагов» (column(None)/same_rank(None)). Гард = только цель."""
    p, enemies, cm = _make_cm(3, positioning=False)
    e0, e1, e2 = enemies
    ColumnStrikeEffect(10, 12).execute(p, e0, cm, is_upgraded=False)
    assert e1.hp == 50 and e2.hp == 50
    # сбросим и проверим Размах
    p2, en2, cm2 = _make_cm(3, positioning=False)
    RankStrikeEffect(10, 12).execute(p2, en2[0], cm2, is_upgraded=False)
    assert en2[1].hp == 50 and en2[2].hp == 50


def test_карты_прокол_размах_несут_свои_кирпичи():
    assert any(isinstance(e, ColumnStrikeEffect) for e in create_piercing_thrust().effects)
    assert any(isinstance(e, RankStrikeEffect) for e in create_wide_swing().effects)
