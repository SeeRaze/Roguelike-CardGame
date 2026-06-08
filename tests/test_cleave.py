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
    """3 врага на сетке (С51 — 1Ф/2Т): E0 фронт-ЦЕНТР, E1 тыл-ЦЕНТР, E2 тыл-ЛЕВО.
    E0 ортогонально соседствует только с E1 (Δранг, вертикаль колонки); E2 (тыл-ЛЕВО)
    от E0 по диагонали → НЕ сосед. Удар по E0 → сплеш по E1, мимо E2."""
    p, enemies, cm = _make_cm(3, positioning=True)
    e0, e1, e2 = enemies
    SplashDamageEffect(10, 12).execute(p, e0, cm, is_upgraded=False)
    assert e0.hp < 50          # цель — полный урон
    assert e1.hp < 50          # сосед по рангу (тыл-центр) — сплеш
    assert e2.hp == 50         # тыл-лево от центр-фронта по диагонали — не задет
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
    """3 врага (С51 — 1Ф/2Т): E0 фронт-ЦЕНТР, E1 тыл-ЦЕНТР, E2 тыл-ЛЕВО. Колонка
    ЦЕНТР = E0+E1. «Прокол» по E0 пробивает в тыл-центр (E1), но НЕ задевает
    линию ЛЕВО (E2)."""
    p, enemies, cm = _make_cm(3, positioning=True)
    e0, e1, e2 = enemies
    ColumnStrikeEffect(10, 12).execute(p, e0, cm, is_upgraded=False)
    assert e0.hp < 50          # цель
    assert e1.hp < 50          # тыл той же колонки (центр) — пробит
    assert e2.hp == 50         # другая линия (лево) — не задета


def test_размах_бьёт_весь_ряд():
    """С51 — 1Ф/2Т: шеренга из двух теперь в ТЫЛУ (E1 тыл-ЦЕНТР, E2 тыл-ЛЕВО);
    фронт = один E0. «Размах» по тыловому E1 задевает соседа по ряду E2, но не
    фронт (E0)."""
    p, enemies, cm = _make_cm(3, positioning=True)
    e0, e1, e2 = enemies
    RankStrikeEffect(10, 12).execute(p, e1, cm, is_upgraded=False)
    assert e1.hp < 50          # цель (тыл-центр)
    assert e2.hp < 50          # сосед по шеренге тыла (тыл-лево)
    assert e0.hp == 50         # фронт — не задет


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


def test_проекция_aoe_показывает_вторичные_цели():
    """Регресс-гард (С51 плейтест): проекция урона на HP-барах должна включать
    вторичные цели позиционного AoE (колонка/сплеш), а не только первичную —
    иначе игрок не видит, что заденет, и думает «урона нет»."""
    from ui.combat.interface import CombatInterface
    p, enemies, cm = _make_cm(3, positioning=True)
    e0, e1, e2 = enemies   # С51 1Ф/2Т: e0 фронт-центр, e1 тыл-центр, e2 тыл-лево
    # «Прокол» (колонка): цель e0 + вся колонка центра (e1 в тылу центра).
    pierce = create_piercing_thrust()
    cm.deck_manager.hand = [pierce]
    proj = CombatInterface._card_projection(cm, p, pierce)
    assert e0 in proj and proj[e0] > 0          # первичная цель
    assert e1 in proj and proj[e1] > 0          # колонка пробивает в тыл-центр
    # «Рассекающий» (сплеш по соседям): цель e0 + сосед e1 (тыл-центр по вертикали).
    splash = create_cleaving_strike()
    cm.deck_manager.hand = [splash]
    proj2 = CombatInterface._card_projection(cm, p, splash)
    assert e0 in proj2 and proj2[e0] > 0
    assert len([t for t in (e1, e2) if proj2.get(t, 0) > 0]) >= 1   # хотя бы один сосед


def test_проекция_без_позиционки_только_цель():
    """Без позиционки AoE-вторичных целей нет → проекция только на первичную цель
    (регресс-нейтрально)."""
    from ui.combat.interface import CombatInterface
    p, enemies, cm = _make_cm(3, positioning=False)
    splash = create_cleaving_strike()
    cm.deck_manager.hand = [splash]
    proj = CombatInterface._card_projection(cm, p, splash)
    # ровно одна цель в проекции (вторичных нет без сетки)
    assert sum(1 for v in proj.values() if v > 0) == 1
