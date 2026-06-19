# tests/test_anchor_facts.py
# Контент гл.1 (С71), Инкремент 2: боевой трекинг 5 фактов карт-якорей.
# _track_anchor_facts тестируем изолированно (fake self — чистая логика пиков/
# счётчиков), killed_with_decomp — через реальный бой (death-check).

from types import SimpleNamespace

from core.players import Warrior
from core.enemies.cultist import Cultist
from core.Creature import Creature
from core.cards import create_strike
from managers.CombatManager import CombatManager


# ─── _track_anchor_facts (изолированно) ───────────────────────────────────────

def _fresh_facts():
    return {
        "peak_cards_per_turn": 0, "peak_element_stack": 0,
        "max_same_card_in_turn": 0, "peak_distinct_elements": 0,
        "killed_with_decomp": False,
    }


def _fake_self(enemies, cards_played=1, counts=None):
    return SimpleNamespace(
        enemies=enemies,
        cards_played_this_turn=cards_played,
        _turn_card_counts=counts if counts is not None else {},
        combat_facts=_fresh_facts(),
    )


def _enemy_with(**elements):
    e = Creature("Враг", 50, 50)
    for k, v in elements.items():
        e.set_status(k, v)
    return e


def test_peak_cards_per_turn_tracks_max():
    fs = _fake_self([_enemy_with()], cards_played=5)
    CombatManager._track_anchor_facts(fs, fs.combat_facts, create_strike(), None)
    assert fs.combat_facts["peak_cards_per_turn"] == 5


def test_same_card_in_turn_counts_repeats():
    fs = _fake_self([_enemy_with()])
    card = create_strike()
    for _ in range(3):
        CombatManager._track_anchor_facts(fs, fs.combat_facts, card, None)
    assert fs.combat_facts["max_same_card_in_turn"] == 3
    # Другое имя — отдельный счётчик.
    other = create_strike(); other.name = "Другая"
    CombatManager._track_anchor_facts(fs, fs.combat_facts, other, None)
    assert fs.combat_facts["max_same_card_in_turn"] == 3   # пик не сбит


def test_peak_element_stack_single_element():
    e = _enemy_with(legacy=6)
    fs = _fake_self([e])
    CombatManager._track_anchor_facts(fs, fs.combat_facts, create_strike(), None)
    assert fs.combat_facts["peak_element_stack"] == 6
    assert fs.combat_facts["peak_distinct_elements"] == 1


def test_peak_distinct_elements_on_one_target():
    e = _enemy_with(legacy=2, coffee=1, tox=3)
    fs = _fake_self([e])
    CombatManager._track_anchor_facts(fs, fs.combat_facts, create_strike(), None)
    assert fs.combat_facts["peak_distinct_elements"] == 3
    assert fs.combat_facts["peak_element_stack"] == 3       # макс одиночный = tox 3


def test_distinct_not_summed_across_enemies():
    # Разные стихии на РАЗНЫХ врагах не складываются в «радугу» на одной цели.
    e1 = _enemy_with(legacy=2)
    e2 = _enemy_with(coffee=2)
    fs = _fake_self([e1, e2])
    CombatManager._track_anchor_facts(fs, fs.combat_facts, create_strike(), None)
    assert fs.combat_facts["peak_distinct_elements"] == 1


def test_dead_enemies_ignored():
    e = _enemy_with(legacy=9)
    e.hp = 0
    fs = _fake_self([e])
    CombatManager._track_anchor_facts(fs, fs.combat_facts, create_strike(), None)
    assert fs.combat_facts["peak_element_stack"] == 0


# ─── killed_with_decomp (реальный бой) ────────────────────────────────────────

def test_killed_with_decomp_flag_set_on_real_kill():
    enemy = Cultist("Культист", 6, 6)
    cm = CombatManager(Warrior(), enemy, [create_strike()], game_manager=None)
    enemy.set_status("decomp", 2)
    enemy.hp = 0                       # имитируем смертельный урон
    cm._check_enemy_death(enemy)
    assert cm.combat_facts["killed_with_decomp"] is True


def test_killed_without_decomp_leaves_flag_false():
    enemy = Cultist("Культист", 6, 6)
    cm = CombatManager(Warrior(), enemy, [create_strike()], game_manager=None)
    enemy.hp = 0
    cm._check_enemy_death(enemy)
    assert cm.combat_facts["killed_with_decomp"] is False


def test_turn_card_counts_reset_on_new_turn():
    cm = CombatManager(Warrior(), Cultist("Культист", 30, 30),
                       [create_strike()], game_manager=None)
    cm._turn_card_counts["Удар"] = 2
    cm.start_turn_phase()
    assert cm._turn_card_counts == {}
