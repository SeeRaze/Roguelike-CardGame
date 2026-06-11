# tests/test_elites.py
# Тесты 4 элитных врагов-контр билдам: механики, хуки, реестр, диспатч спавна.
# Паттерн: каждая механика — один тест (surgical, как в test_bosses.py).
import random

from core.Creature import Creature
from core.enemies.elites.base import EliteBase
from core.enemies.elites.spell_eater import SpellEater
from core.enemies.elites.plague import PlaguePustule
from core.enemies.elites.butcher import ButcherTorturer
from core.enemies.elites.devourer import CorruptionDevourer
from core.enemies.elites.regression import RegressionElite
from core.enemies import ELITE_REGISTRY
from managers.EnemySpawner import build_enemy


# ═══════════════════════════════════════════════════════════════════════════
# EliteBase
# ═══════════════════════════════════════════════════════════════════════════

class TestEliteBase:
    def test_is_elite_flag_set(self):
        e = EliteBase("Test", 100, 100)
        assert e.is_elite is True

    def test_not_boss(self):
        e = EliteBase("Test", 100, 100)
        # Элита не должна считаться боссом (раздельная статистика убийств).
        assert getattr(e, "is_boss", False) is False

    def test_on_card_played_noop(self):
        EliteBase("Test", 100, 100).on_card_played(None, None, None)

    def test_on_turn_start_noop(self):
        EliteBase("Test", 100, 100).on_turn_start(None, None)

    def test_all_archetypes_subclass_elitebase(self):
        for cls in ELITE_REGISTRY:
            assert issubclass(cls, EliteBase), cls.__name__


# ═══════════════════════════════════════════════════════════════════════════
# Пожиратель Заклинаний — +щит за карту
# ═══════════════════════════════════════════════════════════════════════════

class TestSpellEater:
    def test_shield_per_card(self):
        e = SpellEater("SE", 100, 100)
        e.on_card_played(None, Creature("p", 50, 50), None)
        assert e.shield == SpellEater.SHIELD_PER_CARD

    def test_shield_accumulates_across_cards(self):
        e = SpellEater("SE", 100, 100)
        for _ in range(3):
            e.on_card_played(None, None, None)
        assert e.shield == SpellEater.SHIELD_PER_CARD * 3

    def test_random_title_in_list(self):
        assert SpellEater.random_title() in SpellEater._TITLES


# ═══════════════════════════════════════════════════════════════════════════
# Чумной Гнойник — Legacy-код, ×2 +Токс (Кислотный дождь) при щите
# ═══════════════════════════════════════════════════════════════════════════

class TestPlaguePustule:
    def test_legacy_no_shield(self):
        e = PlaguePustule("PP", 100, 100)
        p = Creature("p", 50, 50)
        e.on_turn_start(p, None)
        assert p.legacy == PlaguePustule.PLAGUE_POISON
        assert p.tox == 0                      # без щита токса нет

    def test_legacy_doubled_with_shield_and_tox(self):
        e = PlaguePustule("PP", 100, 100)
        p = Creature("p", 50, 50)
        p.shield = 5
        e.on_turn_start(p, None)
        assert p.legacy == PlaguePustule.PLAGUE_POISON * 2
        assert p.tox == PlaguePustule.PLAGUE_TOX   # щит провоцирует Кислотный дождь

    def test_legacy_stacks_over_turns(self):
        e = PlaguePustule("PP", 100, 100)
        p = Creature("p", 50, 50)
        e.on_turn_start(p, None)
        e.on_turn_start(p, None)
        assert p.legacy == PlaguePustule.PLAGUE_POISON * 2


# ═══════════════════════════════════════════════════════════════════════════
# Мясник-Истязатель — Шипы + Слабость при росте HP
# ═══════════════════════════════════════════════════════════════════════════

class TestButcherTorturer:
    def test_thorns_set_on_init(self):
        e = ButcherTorturer("BT", 100, 100)
        assert e.thorns == ButcherTorturer.BUTCHER_THORNS

    def test_first_observation_no_weakness(self):
        e = ButcherTorturer("BT", 100, 100)
        p = Creature("p", 50, 80)
        e.on_turn_start(p, None)
        assert p.weak == 0

    def test_weakness_on_hp_increase(self):
        e = ButcherTorturer("BT", 100, 100)
        p = Creature("p", 50, 80)
        e.on_turn_start(p, None)   # снимок 50
        p.hp = 60                  # лечение
        e.on_turn_start(p, None)
        assert p.weak == 1

    def test_no_weakness_on_hp_decrease(self):
        e = ButcherTorturer("BT", 100, 100)
        p = Creature("p", 50, 80)
        e.on_turn_start(p, None)   # снимок 50
        p.hp = 40                  # урон
        e.on_turn_start(p, None)
        assert p.weak == 0

    def test_thorns_reflect_via_take_damage(self):
        # Интеграция: Шипы отражают урон атакующему (Creature.take_damage).
        e = ButcherTorturer("BT", 100, 100)
        attacker = Creature("a", 30, 30)
        e.take_damage(10, attacker=attacker)
        assert attacker.hp == 30 - ButcherTorturer.BUTCHER_THORNS


# ═══════════════════════════════════════════════════════════════════════════
# Пожиратель Скверны — поедание DoT (cap) → хил
# ═══════════════════════════════════════════════════════════════════════════

class TestCorruptionDevourer:
    def test_devours_under_cap(self):
        e = CorruptionDevourer("CD", 50, 100)
        e.legacy = 3
        e.on_turn_start(None, None)
        assert e.legacy == 0
        assert e.hp == 53   # вылечился на 3

    def test_cap_limits_consumption(self):
        e = CorruptionDevourer("CD", 50, 100)
        e.legacy = 5
        e.bleed = 4          # суммарно 9, cap 8
        e.on_turn_start(None, None)
        # Приоритет legacy→bleed: ест legacy5 + bleed3 = 8.
        assert e.legacy == 0
        assert e.bleed == 1
        assert e.hp == 58

    def test_no_dot_no_heal(self):
        e = CorruptionDevourer("CD", 50, 100)
        e.on_turn_start(None, None)
        assert e.hp == 50

    def test_heal_capped_at_max_hp(self):
        e = CorruptionDevourer("CD", 99, 100)
        e.legacy = 8
        e.on_turn_start(None, None)
        assert e.hp == 100   # лечение не превышает max_hp


# ═══════════════════════════════════════════════════════════════════════════
# Регрессия — накопительная броня (закрывающееся окно) + реген
# ═══════════════════════════════════════════════════════════════════════════

class TestRegressionElite:
    def test_first_turn_hardens(self):
        e = RegressionElite("RE", 100, 100)
        e.on_turn_start(None, None)
        assert e.hardening == RegressionElite.HARDEN_RAMP
        assert e.shield == RegressionElite.HARDEN_RAMP

    def test_hardening_accumulates_each_turn(self):
        e = RegressionElite("RE", 100, 100)
        # Щит обнуляется вражеской фазой между ходами — эмулируем сбросом.
        e.on_turn_start(None, None)
        e.shield = 0
        e.on_turn_start(None, None)
        # Накопитель растёт: окно убийства закрывается всё сильнее.
        assert e.hardening == RegressionElite.HARDEN_RAMP * 2
        assert e.shield == RegressionElite.HARDEN_RAMP * 2

    def test_regen_when_damaged(self):
        e = RegressionElite("RE", 50, 100)
        e.on_turn_start(None, None)
        assert e.hp == 50 + RegressionElite.REGEN_PER_TURN

    def test_no_regen_at_full_hp(self):
        e = RegressionElite("RE", 100, 100)
        e.on_turn_start(None, None)
        assert e.hp == 100   # реген не переливает через max_hp

    def test_random_title_in_list(self):
        assert RegressionElite.random_title() in RegressionElite._TITLES


# ═══════════════════════════════════════════════════════════════════════════
# Реестр и диспатч спавна
# ═══════════════════════════════════════════════════════════════════════════

class TestEliteDispatch:
    def test_registry_has_five_archetypes(self):
        assert len(ELITE_REGISTRY) == 5

    def test_registry_contents(self):
        assert SpellEater in ELITE_REGISTRY
        assert PlaguePustule in ELITE_REGISTRY
        assert ButcherTorturer in ELITE_REGISTRY
        assert CorruptionDevourer in ELITE_REGISTRY
        assert RegressionElite in ELITE_REGISTRY

    def test_build_elite_returns_archetype(self):
        random.seed(0)
        # За несколько спавнов должны встретиться все 4 архетипа.
        seen = {type(build_enemy(15, is_elite=True)).__name__ for _ in range(60)}
        assert seen == {c.__name__ for c in ELITE_REGISTRY}

    def test_build_elite_is_elite_flag(self):
        e = build_enemy(15, is_elite=True)
        assert e.is_elite is True
        assert isinstance(e, EliteBase)

    def test_build_elite_name_marked(self):
        e = build_enemy(15, is_elite=True)
        assert "[Элита, Этаж 15]" in e.name

    def test_build_normal_not_elite(self):
        e = build_enemy(15, is_elite=False)
        assert not isinstance(e, EliteBase)

    def test_elite_stat_multiplier_applied(self):
        # Элита крупнее рядового того же этажа (×1.5 HP в EnemySpawner).
        random.seed(0)
        normal = build_enemy(15, is_elite=False)
        elite = build_enemy(15, is_elite=True)
        assert elite.max_hp > normal.max_hp

    def test_all_archetypes_have_random_title(self):
        for cls in ELITE_REGISTRY:
            assert isinstance(cls.random_title(), str)
