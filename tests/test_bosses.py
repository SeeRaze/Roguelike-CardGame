# tests/test_bosses.py
# Комплексные тесты 5 боссов-фильтров: механики, фазы, хуки, диспатч.
# Паттерн: каждая механика — один тест (surgical, как в остальных тестах).
import pytest
from core.Creature import Creature
from core.enemies.base import Enemy, IntentHeal
from core.enemies.bosses.base import BossBase
from core.enemies.bosses.guardian import ThresholdGuardian
from core.enemies.bosses.archivist import OblivionArchivist
from core.enemies.bosses.elemental import VoidElemental
from core.enemies.bosses.keeper import TimeKeeper
from core.enemies.bosses.architect import TowerArchitect
from core.enemies import BOSS_BY_FLOOR, BossTitan
from managers.EnemySpawner import build_enemy


# ═══════════════════════════════════════════════════════════════════════════
# BossBase
# ═══════════════════════════════════════════════════════════════════════════

class TestBossBase:
    def test_is_boss_flag_set(self):
        b = BossBase("Test", 100, 100)
        assert b.is_boss is True

    def test_default_phase1_above_threshold(self):
        b = BossBase("Test", 100, 100)
        b.hp = 51
        assert b.current_phase == 1

    def test_default_phase2_at_threshold(self):
        b = BossBase("Test", 100, 100)
        b.hp = 50
        assert b.current_phase == 2

    def test_default_phase2_below_threshold(self):
        b = BossBase("Test", 100, 100)
        b.hp = 1
        assert b.current_phase == 2

    def test_phase_zero_max_hp_guarded(self):
        b = BossBase("Test", 0, 0)
        assert b.current_phase == 1

    def test_on_card_played_noop(self):
        b = BossBase("Test", 100, 100)
        # Не падает при вызове заглушки
        b.on_card_played(None, None, None)

    def test_on_turn_start_noop(self):
        b = BossBase("Test", 100, 100)
        b.on_turn_start(None, None)


# ═══════════════════════════════════════════════════════════════════════════
# Threshold Guardian (floor 20)
# ═══════════════════════════════════════════════════════════════════════════

class TestThresholdGuardian:
    def _boss(self, hp=100):
        g = ThresholdGuardian("Страж Порога", hp, 100)
        g.base_test_damage = 10
        g.base_test_shield = 5
        return g

    def test_phase_threshold_40pct(self):
        g = self._boss(100)
        assert g.PHASE_THRESHOLD == 0.4
        g.hp = 41
        assert g.current_phase == 1
        g.hp = 40
        assert g.current_phase == 2

    def test_turn0_attack(self):
        g = self._boss()
        g.choose_intent()
        assert g.intent_type == "attack"

    def test_turn1_attack_same_multiplier(self):
        g = self._boss()
        g.turn_count = 1
        g.choose_intent()
        assert g.intent_type == "attack"

    def test_turn2_defend_and_escalate(self):
        g = self._boss()
        g.turn_count = 2
        g.choose_intent()
        assert g.intent_type == "defend"
        assert g._escalation == 1

    def test_escalation_damage_grows(self):
        g = self._boss()
        # escalation=0 → mult=1.0 → dmg=10
        g.choose_intent()
        assert g.intent_value == 10
        # escalation=2 → mult=1.8 → dmg=18
        g._escalation = 2
        g.choose_intent()
        assert g.intent_value == 18

    def test_escalation_capped_at_3x(self):
        g = self._boss()
        g._escalation = 10  # 1 + 0.4*10 = 5.0 → capped 3.0
        g.choose_intent()
        assert g.intent_value == 30  # 10 * 3.0

    def test_phase2_always_attacks(self):
        g = self._boss(hp=30)  # HP 30% → phase 2
        assert g.current_phase == 2
        for turn in range(6):
            g.turn_count = turn
            g.choose_intent()
            assert g.intent_type == "attack", f"turn {turn}: expected attack, got {g.intent_type}"

    def test_phase2_damage_is_base(self):
        g = self._boss(hp=30)
        g.choose_intent()
        assert g.intent_value == 10  # base, без эскалации

    def test_cycle_repeats(self):
        g = self._boss()
        # Turn 0-2: attack, attack, defend+escalate
        g.turn_count = 0; g.choose_intent(); assert g.intent_type == "attack"
        g.turn_count = 1; g.choose_intent(); assert g.intent_type == "attack"
        g.turn_count = 2; g.choose_intent(); assert g.intent_type == "defend"
        # Turn 3-5 (next cycle): снова attack(escalated), attack, defend
        g.turn_count = 3; g.choose_intent(); assert g.intent_type == "attack"
        g.turn_count = 4; g.choose_intent(); assert g.intent_type == "attack"
        g.turn_count = 5; g.choose_intent(); assert g.intent_type == "defend"

    def test_random_title(self):
        title = ThresholdGuardian.random_title()
        assert title in ThresholdGuardian._TITLES


# ═══════════════════════════════════════════════════════════════════════════
# Oblivion Archivist (floor 40)
# ═══════════════════════════════════════════════════════════════════════════

class TestOblivionArchivist:
    def _boss(self, hp=100):
        a = OblivionArchivist("Архивариус", hp, 100)
        a.base_test_damage = 10
        a.base_test_shield = 5
        return a

    def test_on_card_played_gains_shield_phase1(self):
        a = self._boss()
        shield_before = a.shield
        a.on_card_played(None, None, None)
        assert a.shield == shield_before + 2  # SHIELD_PER_CARD_P1

    def test_on_card_played_gains_shield_phase2(self):
        a = self._boss(hp=40)
        assert a.current_phase == 2
        shield_before = a.shield
        a.on_card_played(None, None, None)
        assert a.shield == shield_before + 3  # SHIELD_PER_CARD_P2

    def test_on_turn_start_weak_if_deck_large(self):
        a = self._boss()
        player = Creature("Игрок", 50, 50)
        # Без CombatManager → deck_size=99 → больше 15 → Слабость
        weak_before = player.weak
        a.on_turn_start(player, None)
        assert player.weak == weak_before + 1

    def test_on_turn_start_phase2_always_weak(self):
        a = self._boss(hp=40)
        player = Creature("Игрок", 50, 50)
        weak_before = player.weak
        a.on_turn_start(player, None)
        assert player.weak == weak_before + 1

    def test_intent_cycle(self):
        a = self._boss()
        a.turn_count = 0; a.choose_intent()
        assert a.intent_type == "debuff"; assert a.intent_value == 1
        a.turn_count = 1; a.choose_intent()
        assert a.intent_type == "defend"
        a.turn_count = 2; a.choose_intent()
        assert a.intent_type == "attack"

    def test_random_title(self):
        title = OblivionArchivist.random_title()
        assert title in OblivionArchivist._TITLES


# ═══════════════════════════════════════════════════════════════════════════
# Void Elemental (floor 60)
# ═══════════════════════════════════════════════════════════════════════════

class TestVoidElemental:
    def _boss(self, hp=100, floor=60):
        v = VoidElemental("Элементаль", hp, 100)
        v.base_test_damage = 10
        v.base_test_shield = 5
        v.spawn_floor = floor
        return v

    def test_void_shield_amount_scales_with_floor(self):
        v60 = self._boss(floor=60)
        assert v60.void_shield_amount == 8 + 6   # BASE + 60//10
        v80 = self._boss(floor=80)
        assert v80.void_shield_amount == 8 + 8

    def test_turn0_void_shield_phase(self):
        v = self._boss()
        v.on_turn_start(None, None)
        assert v.shield == v.void_shield_amount
        assert not v._exposed

    def test_turn1_exposed_phase(self):
        v = self._boss()
        v.turn_count = 1
        v.on_turn_start(None, None)
        assert v.vulnerable == 1
        assert v._exposed

    def test_phase1_3turn_cycle(self):
        v = self._boss()
        # Turn 0: Void Shield (attack 0.7)
        v.turn_count = 0; v.choose_intent()
        assert v.intent_value == 7  # 10*0.7
        # Turn 1: Exposed (attack 1.4)
        v.turn_count = 1; v.choose_intent()
        assert v.intent_value == 14  # 10*1.4
        # Turn 2: Defend
        v.turn_count = 2; v.choose_intent()
        assert v.intent_type == "defend"

    def test_phase2_2turn_cycle(self):
        v = self._boss(hp=30)
        assert v.current_phase == 2
        # Phase 2: 2-turn cycle (Void Shield → Exposed), no defend
        v.turn_count = 0; v.choose_intent()
        assert v.intent_type == "attack"  # Void Shield attack (0.7)
        v.turn_count = 1; v.choose_intent()
        assert v.intent_type == "attack"  # Exposed attack (1.4)
        # Turn 2 wraps back to Void Shield (0 mod 2 = 0)
        v.turn_count = 2; v.choose_intent()
        assert v.intent_value == 7  # attack 0.7 again (not defend!)

    def test_phase2_void_shield_extra_2(self):
        v = self._boss(hp=30)
        v.turn_count = 0
        v.on_turn_start(None, None)
        # Phase 2: +2 extra shield
        assert v.shield == v.void_shield_amount + 2

    def test_random_title(self):
        title = VoidElemental.random_title()
        assert title in VoidElemental._TITLES


# ═══════════════════════════════════════════════════════════════════════════
# Time Keeper (floor 80)
# ═══════════════════════════════════════════════════════════════════════════

class TestTimeKeeper:
    def _boss(self, hp=100):
        t = TimeKeeper("Хранитель", hp, 100)
        t.base_test_damage = 10
        t.base_test_shield = 5
        return t

    def test_temporal_charge_increments(self):
        t = self._boss()
        assert t._temporal_charge == 0
        t.on_turn_start(None, None)
        assert t._temporal_charge == 1
        t.on_turn_start(None, None)
        assert t._temporal_charge == 2

    def test_damage_scales_with_charge(self):
        t = self._boss()
        t._temporal_charge = 0; t.choose_intent()
        assert t.intent_value == 10  # 10 * 1.0
        t._temporal_charge = 2; t.choose_intent()
        assert t.intent_value == 13  # 10 * (1 + 0.15*2) = 10*1.3
        t._temporal_charge = 10; t.choose_intent()
        assert t.intent_value == 25  # 10 * (1 + 0.15*10) = 10*2.5

    def test_temporal_shift_heals(self):
        t = self._boss()
        t.turn_count = 2; t.choose_intent()
        assert t.intent_type == "heal"
        assert t.intent_value == 15  # 15% от 100

    def test_intent_cycle(self):
        t = self._boss()
        t.turn_count = 0; t.choose_intent()
        assert t.intent_type == "attack"
        t.turn_count = 1; t.choose_intent()
        assert t.intent_type == "defend"
        t.turn_count = 2; t.choose_intent()
        assert t.intent_type == "heal"

    def test_phase2_weak_on_shift(self):
        t = self._boss(hp=40)
        assert t.current_phase == 2
        player = Creature("Игрок", 50, 50)
        t.turn_count = 2; t.choose_intent()
        weak_before = player.weak
        hp_before = t.hp
        t.execute_intent(player, None)
        assert player.weak == weak_before + 2
        assert t.hp > hp_before  # heal

    def test_phase1_no_weak_on_shift(self):
        t = self._boss()
        player = Creature("Игрок", 50, 50)
        t.turn_count = 2; t.choose_intent()
        weak_before = player.weak
        t.execute_intent(player, None)
        assert player.weak == weak_before  # без Weak в фазе 1

    def test_execute_attack_defend_delegates_to_super(self):
        t = self._boss()
        player = Creature("Игрок", 50, 50)
        # Атака
        t.turn_count = 0; t.choose_intent()
        hp_before = player.hp
        t.execute_intent(player, None)
        assert player.hp < hp_before
        # Защита
        t.turn_count = 1; t.choose_intent()
        shield_before = t.shield
        t.execute_intent(player, None)
        assert t.shield > shield_before

    def test_random_title(self):
        title = TimeKeeper.random_title()
        assert title in TimeKeeper._TITLES


# ═══════════════════════════════════════════════════════════════════════════
# Tower Architect (floor 100)
# ═══════════════════════════════════════════════════════════════════════════

class TestTowerArchitect:
    def _boss(self, hp=100):
        a = TowerArchitect("Архитектор", hp, 100)
        a.base_test_damage = 10
        a.base_test_shield = 5
        return a

    def test_three_phases(self):
        a = self._boss(100)
        a.hp = 68; assert a.current_phase == 1   # >66%
        a.hp = 66; assert a.current_phase == 2   # 33-66%
        a.hp = 50; assert a.current_phase == 2   # mid phase 2
        a.hp = 34; assert a.current_phase == 2   # >33% (34/100 > 1/3)
        a.hp = 32; assert a.current_phase == 3   # <33%

    def test_phase1_defend_cycle(self):
        a = self._boss(100)
        a.turn_count = 0; a.choose_intent()
        assert a.intent_type == "attack"; assert a.intent_value == 10
        a.turn_count = 1; a.choose_intent()
        assert a.intent_type == "attack"
        a.turn_count = 2; a.choose_intent()
        assert a.intent_type == "defend"

    def test_phase2_heavy_attack(self):
        a = self._boss(50)
        assert a.current_phase == 2
        a.choose_intent()
        assert a.intent_type == "attack"
        assert a.intent_value == 13  # 10 * 1.3

    def test_phase2_weak_per_attack(self):
        a = self._boss(50)
        player = Creature("Игрок", 50, 50)
        a.choose_intent()
        weak_before = player.weak
        a.execute_intent(player, None)
        assert player.weak == weak_before + 1

    def test_phase3_always_heavy_attack(self):
        a = self._boss(20)
        assert a.current_phase == 3
        for turn in range(6):
            a.turn_count = turn
            a.choose_intent()
            assert a.intent_type == "attack", f"turn {turn}: expected attack"
            assert a.intent_value == 16  # 10 * 1.6

    def test_phase3_no_defend(self):
        a = self._boss(20)
        for turn in range(10):
            a.turn_count = turn
            a.choose_intent()
            assert a.intent_type != "defend", f"turn {turn}: unexpected defend"

    def test_phase1_no_weak_on_attack(self):
        a = self._boss(100)
        player = Creature("Игрок", 50, 50)
        a.choose_intent()
        weak_before = player.weak
        a.execute_intent(player, None)
        assert player.weak == weak_before  # без Weak в фазе 1

    def test_random_title(self):
        title = TowerArchitect.random_title()
        assert title in TowerArchitect._TITLES


# ═══════════════════════════════════════════════════════════════════════════
# IntentHeal (core/enemies/base.py)
# ═══════════════════════════════════════════════════════════════════════════

class TestIntentHeal:
    def test_intent_heal_type(self):
        h = IntentHeal(15)
        assert h.type == "heal"
        assert h.value == 15

    def test_enemy_execute_intent_heal(self):
        e = Enemy("Враг", 50, 100)
        e.set_intent("heal", 20)
        hp_before = e.hp
        e.execute_intent(None, None)
        assert e.hp == hp_before + 20

    def test_enemy_set_intent_heal(self):
        e = Enemy("Враг", 50, 100)
        e.set_intent("heal", 30)
        assert e.intent_type == "heal"
        assert e.intent_value == 30


# ═══════════════════════════════════════════════════════════════════════════
# EnemySpawner dispatch
# ═══════════════════════════════════════════════════════════════════════════

class TestBossDispatch:
    def test_boss_by_floor_keys(self):
        assert 20 in BOSS_BY_FLOOR
        assert 40 in BOSS_BY_FLOOR
        assert 60 in BOSS_BY_FLOOR
        assert 80 in BOSS_BY_FLOOR
        assert 100 in BOSS_BY_FLOOR

    def test_floor20_returns_guardian(self):
        e = build_enemy(20)
        assert isinstance(e, ThresholdGuardian)

    def test_floor40_returns_archivist(self):
        e = build_enemy(40)
        assert isinstance(e, OblivionArchivist)

    def test_floor60_returns_elemental(self):
        e = build_enemy(60)
        assert isinstance(e, VoidElemental)

    def test_floor80_returns_keeper(self):
        e = build_enemy(80)
        assert isinstance(e, TimeKeeper)

    def test_floor100_returns_architect(self):
        e = build_enemy(100)
        assert isinstance(e, TowerArchitect)

    def test_boss_spawn_floor_set(self):
        e = build_enemy(60)
        assert e.spawn_floor == 60

    def test_boss_fallback_to_titan(self):
        # Floor 120 тоже кратен 20, но не в BOSS_BY_FLOOR
        e = build_enemy(120)
        assert isinstance(e, BossTitan)

    def test_normal_floor_not_boss(self):
        e = build_enemy(5)
        assert not isinstance(e, ThresholdGuardian)
        assert not isinstance(e, BossTitan)

    def test_all_bosses_set_is_boss_flag(self):
        for floor in [20, 40, 60, 80, 100]:
            e = build_enemy(floor)
            assert e.is_boss is True, f"Floor {floor}: is_boss not set"

    def test_boss_name_contains_boss_prefix(self):
        for floor in [20, 40, 60, 80, 100]:
            e = build_enemy(floor)
            assert e.name.startswith("БОСС:"), f"Floor {floor}: name={e.name}"
