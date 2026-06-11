# tests/test_chemist_class.py
# Card Fusion этап 2 (С51), РЕГИСТРАЦИЯ класса Химик (инертно): класс заводится,
# гейт слияния fusion_enabled включён только у него, ярус 2 (анлок за достижения),
# baseline-эталон НЕ тронут (Химика нет в sim CLASSES → регресс-гард зелёный).
# Механизм слияния/Нестабильность — следующие этапы.

from core.players import Chemist, Warrior, Berserker
from core.players.base import Player
from core.players.chemist import REAGENT_PER_TURN, get_chemist_deck
from core import progression


# ── класс заводится ────────────────────────────────────────────────────────────────

def test_химик_инстанцируется():
    c = Chemist()
    assert c.name == "Химик"
    assert c.max_hp == 70
    assert c.max_energy == 3
    assert isinstance(c, Player)


def test_химик_имеет_способность_заглушку():
    c = Chemist()
    assert c.active_ability is not None
    assert c.active_ability.name == "Сингулярность"
    # Сингулярность отложена (С51) → способность пока не активируется.
    assert c.active_ability.is_ready() is False
    assert c.active_ability.activate(None) is False


def test_модульная_стартовая_колода():
    deck = get_chemist_deck()
    assert len(deck) == 8                 # 3 Удара + 2 Защиты + 3 стихии-сырьё
    # сырьё разных стихий → эмерджентные Глитч-комбо при конкатенации
    names = [c.name for c in deck]
    assert names.count("Удар") == 3


# ── гейт слияния (как positioning_enabled) ─────────────────────────────────────────

def test_гейт_слияния_включён_только_у_химика():
    assert Chemist().fusion_enabled is True
    # дефолт на базовом Player и у других классов — выключен (механизм инертен)
    assert Warrior().fusion_enabled is False
    assert Berserker().fusion_enabled is False


def test_реагент_стартует_с_нуля_приток_задан():
    c = Chemist()
    assert c.reagent == 0
    assert c.reagent_per_turn == REAGENT_PER_TURN
    assert REAGENT_PER_TURN >= 1


def test_базовый_player_имеет_инертные_поля_фьюжна():
    # Поля живут на базовом Player (дефолт инертный) — не на одном Химике.
    p = Warrior()
    assert hasattr(p, "fusion_enabled") and p.fusion_enabled is False
    assert hasattr(p, "reagent") and p.reagent == 0


# ── ярусная прогрессия ─────────────────────────────────────────────────────────────

def test_химик_ярус_2():
    assert progression.class_tier("Chemist") == 2


def test_химик_залочен_на_свежей_мете():
    assert progression.is_unlocked({}, "Chemist") is False
    assert progression.is_unlocked(None, "Chemist") is False


def test_химик_в_условиях_анлока():
    assert "Chemist" in progression.UNLOCK_CONDITIONS


def test_химик_открывается_по_достижению():
    meta = {"stats": {"best_floor": 8}, "unlocks": []}
    fresh = progression.newly_unlocked(meta)
    assert "Chemist" in fresh
    assert progression.is_unlocked(meta, "Chemist") is True


def test_химик_не_открыт_до_достижения():
    meta = {"stats": {"best_floor": 7}, "unlocks": []}
    fresh = progression.newly_unlocked(meta)
    assert "Chemist" not in fresh
