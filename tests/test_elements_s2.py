# tests/test_elements_s2.py
# Этап S2 айти-передела стихий: механики новых статусов.
#   legacy  — DoT, УВАЖАЕТ щит, декей-триангуляр.
#   coffee  — Уязвимость АДДИТИВНАЯ (+20%/стак) на цели.
#   tox     — Слабость МУЛЬТИПЛИКАТИВНАЯ (×0.9/стак, пол 20%) на атакующем.
#   decomp  — анти-щит: глушит gain_shield, длительность тикает.
from core.Creature import Creature
from core.EffectCalculator import EffectCalculator


# ─── legacy: DoT, уважает щит, убывает на 1 ──────────────────────────────────
def test_legacy_absorbed_by_shield_then_decays():
    c = Creature("враг", 20, 20)
    c.shield = 5
    c.legacy = 4
    c.tick_statuses()
    # Щит впитал весь тик (4) → HP цел, щит 1, стак убыл до 3.
    assert c.hp == 20
    assert c.shield == 1
    assert c.legacy == 3


def test_legacy_pierces_only_after_shield_gone():
    c = Creature("враг", 20, 20)
    c.shield = 1
    c.legacy = 3
    c.tick_statuses()
    # Щит 1 впитал 1, остаток 2 в HP; стак 3→2.
    assert c.shield == 0
    assert c.hp == 18
    assert c.legacy == 2


def test_legacy_triangular_total_no_shield():
    c = Creature("враг", 20, 20)
    c.legacy = 3
    for _ in range(3):
        c.tick_statuses()
    # 3 + 2 + 1 = 6 суммарного урона, стак исчерпан.
    assert c.hp == 14
    assert c.legacy == 0


# ─── coffee: аддитивная уязвимость на цели ───────────────────────────────────
def test_coffee_additive_amp():
    atk = Creature("игрок", 50, 50)
    tgt = Creature("враг", 50, 50)
    tgt.coffee = 2  # ×(1 + 0.2·2) = ×1.4
    dmg = EffectCalculator.calculate_damage(atk, tgt, 10, dry_run=True)
    assert dmg == 14


def test_coffee_is_additive_not_exponential():
    atk = Creature("игрок", 50, 50)
    tgt = Creature("враг", 50, 50)
    tgt.coffee = 3  # аддитив ×1.6 = 16, НЕ 1.2^3≈1.728
    dmg = EffectCalculator.calculate_damage(atk, tgt, 10, dry_run=True)
    assert dmg == 16


# ─── tox: мультипликативная слабость на атакующем, пол 20% ────────────────────
def test_tox_multiplicative():
    atk = Creature("враг", 50, 50)
    tgt = Creature("игрок", 50, 50)
    atk.tox = 2  # 0.9^2 = 0.81 → int(10·0.81) = 8
    dmg = EffectCalculator.calculate_damage(atk, tgt, 10, dry_run=True)
    assert dmg == 8


def test_tox_floor_20_percent():
    atk = Creature("враг", 50, 50)
    tgt = Creature("игрок", 50, 50)
    atk.tox = 30  # 0.9^30 ≈ 0.04, но пол 0.2 → ×0.2 → int(100·0.2) = 20
    dmg = EffectCalculator.calculate_damage(atk, tgt, 100, dry_run=True)
    assert dmg == 20


# ─── decomp: анти-щит + длительность ─────────────────────────────────────────
def test_decomp_blocks_shield_generation():
    c = Creature("враг", 50, 50)
    c.decomp = 2
    c.gain_shield(10)
    assert c.shield == 0  # генерация щита заглушена


def test_decomp_duration_ticks_down():
    c = Creature("враг", 50, 50)
    c.decomp = 2
    c.tick_statuses()
    assert c.decomp == 1
    c.tick_statuses()
    assert c.decomp == 0
    # Истекла → щит снова генерируется.
    c.gain_shield(10)
    assert c.shield == 10
