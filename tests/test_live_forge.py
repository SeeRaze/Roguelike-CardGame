# tests/test_live_forge.py
# Живая обвязка движка прокачки карт (Сессия 39.5): состояние игрока, штамповка
# uid, FP-ковка на костре, миграция upgrade→level, босс-капы, предохранитель
# триггеров и сквозное применение тегов/Заточки в расчёте урона. Сим-слой
# (ForgePolicy/economy) покрыт отдельно в test_balance_forge/sharpen/tags.

from core import forge as f
from core.forge import TriggerGuard, combat_fp_gain
from core.cards.base import Card, DamageEffect, ShieldEffect
from core.EffectCalculator import EffectCalculator
from core.Creature import Creature
from core.players import Warrior


def _atk(name="Удар", dmg=6):
    return Card(name=name, cost=1, card_type="attack",
                description="", effects=[DamageEffect(dmg, dmg + 2)])


class _P:
    """Минимальный живой игрок: поля ковки как ставит Player.__init__."""
    def __init__(self, fp=100, cap=25, max_hp=80):
        self.deck_forge_state = {}
        self.forge_points     = fp
        self.forge_level_cap  = cap
        self._forge_uid_next  = 0
        self.atk_mult         = 1.0
        self.max_hp = max_hp
        self.hp     = max_hp


def _forge_to_cap(player, card, class_name="Warrior"):
    """Прокачать карту, пока хватает FP и не упёрлись в кап."""
    while f.forge_card_one_level(player, card, class_name):
        pass


# ─── Состояние игрока ─────────────────────────────────────────────────────────

def test_player_init_has_forge_state():
    p = Warrior()
    assert p.deck_forge_state == {}
    assert p.forge_points == 0
    assert p.forge_level_cap == f.INITIAL_LEVEL_CAP
    assert p.atk_mult == 1.0


def test_forge_state_survives_combat_reset():
    # Ковочное состояние персистентно весь забег (не сбрасывается между боями).
    p = Warrior()
    p.forge_points = 7
    p.deck_forge_state[0] = {"level": 3, "slots": []}
    p.atk_mult = 1.5
    p.reset_combat_statuses()
    assert p.forge_points == 7
    assert p.deck_forge_state[0]["level"] == 3
    assert p.atk_mult == 1.5


# ─── Штамповка uid ────────────────────────────────────────────────────────────

def test_assign_uid_unique_and_idempotent():
    p = _P()
    a = _atk("A")
    b = _atk("B")
    f.assign_forge_uid(p, a)
    f.assign_forge_uid(p, b)
    assert a._fuid == 0
    assert b._fuid == 1
    f.assign_forge_uid(p, a)            # повторно — uid не меняется
    assert a._fuid == 0
    assert p._forge_uid_next == 2


# ─── Ковка карты за FP ────────────────────────────────────────────────────────

def test_forge_level_and_cost():
    p = _P(fp=100)
    c = _atk()
    f.assign_forge_uid(p, c)
    assert f.forge_level(p, c) == 0
    assert f.can_forge(p, c) is True
    assert f.forge_card_one_level(p, c, "Warrior") is True
    assert f.forge_level(p, c) == 1
    assert p.forge_points == 100 - f.level_cost(0)


def test_forge_migration_level1_sets_upgraded():
    # Миграция: уровень 1 = бережно ручной «+» (без δ); δ — с уровня 2.
    p = _P()
    c = _atk()
    f.assign_forge_uid(p, c)
    base0 = c.effects[0].base_val
    f.forge_card_one_level(p, c, "Warrior")
    assert c.upgraded is True
    assert c.effects[0].base_val == base0
    f.forge_card_one_level(p, c, "Warrior")
    assert c.effects[0].base_val == base0 + f.LINEAR_BONUS_PER_LEVEL


def test_forge_milestone_opens_slot_with_class_tag():
    # Этаж 5 (кап 5) → один слот ранним тегом класса по каналу карты.
    p = _P(cap=5)
    c = _atk()
    f.assign_forge_uid(p, c)
    _forge_to_cap(p, c)
    rec = p.deck_forge_state[c._fuid]
    assert rec["level"] == 5
    assert [s["tag_id"] for s in rec["slots"]] == ["shielded"]


def test_forge_legendary_then_overcharge():
    p = _P(cap=25)
    c = _atk()
    f.assign_forge_uid(p, c)
    _forge_to_cap(p, c)
    rec = p.deck_forge_state[c._fuid]
    assert rec["level"] == 25
    assert len(rec["slots"]) == 3                  # слотов ВСЕГДА 3
    legendary = [s for s in rec["slots"] if s["tag_id"] == "per_shield"][0]
    assert legendary["grade"] >= 1                 # гипер-заряжен на 20/25


def test_forge_respects_cap():
    p = _P(fp=999, cap=4)
    c = _atk()
    f.assign_forge_uid(p, c)
    _forge_to_cap(p, c)
    assert f.forge_level(p, c) == 4                 # ниже первого майлстоуна (5)
    assert p.deck_forge_state[c._fuid]["slots"] == []


def test_forge_insufficient_fp():
    p = _P(fp=0)
    c = _atk()
    f.assign_forge_uid(p, c)
    assert f.can_forge(p, c) is False
    assert f.forge_card_one_level(p, c, "Warrior") is False
    assert f.forge_level(p, c) == 0


def test_forge_channel_picks_defense_tag_for_shield_card():
    # Чисто щитовая карта → канал shield → универсальный оборонный тег.
    p = _P(cap=5)
    c = Card(name="Блок", cost=1, card_type="skill", description="",
             effects=[ShieldEffect(5, 7)])
    f.assign_forge_uid(p, c)
    _forge_to_cap(p, c)
    assert p.deck_forge_state[c._fuid]["slots"][0]["tag_id"] == "bulwark"


# ─── FP-экономика (живая формула = sim) ───────────────────────────────────────

def test_combat_fp_gain_scales_and_boss_bonus():
    assert combat_fp_gain(5)  == f.FORGE_POINTS_PER_ACT[0]
    assert combat_fp_gain(25) == f.FORGE_POINTS_PER_ACT[1]
    assert combat_fp_gain(45) == f.FORGE_POINTS_PER_ACT[2]
    assert combat_fp_gain(20, is_boss=True) == \
        f.FORGE_POINTS_PER_ACT[0] + f.FORGE_POINTS_PER_BOSS


def test_next_cap_for_boss():
    assert f.next_cap_for_boss(20) == 5
    assert f.next_cap_for_boss(60) == 15
    assert f.next_cap_for_boss(19) is None


# ─── Сквозное применение damage-тега в расчёте урона (шаг 7) ───────────────────

class _CM:
    def __init__(self, player, card, snapshot):
        self.player = player
        self._card_being_played = card
        self._play_snapshot = snapshot

    def add_log_message(self, _):
        pass


def _forged_warrior_attack(cap=5):
    """Воин с прокачанной до кап атакой Воина (несёт тег «shielded»)."""
    p = Warrior()
    p.forge_points = 100
    p.forge_level_cap = cap
    c = _atk()
    f.assign_forge_uid(p, c)
    _forge_to_cap(p, c)
    return p, c


def test_damage_tag_applies_when_condition_met():
    # Ур.5 «shielded» (+0.5 урона при щите). Снимок со щитом → ×1.5 в шаге 7.
    p, c = _forged_warrior_attack(cap=5)
    target = Creature("Враг", 100, 100)
    cm = _CM(p, c, {"shield": 5})
    assert EffectCalculator.calculate_damage(p, target, 10, combat_manager=cm) == 15


def test_damage_tag_inert_when_condition_unmet():
    # Тот же тег, но снимок БЕЗ щита → множитель 1.0.
    p, c = _forged_warrior_attack(cap=5)
    target = Creature("Враг", 100, 100)
    cm = _CM(p, c, {"shield": 0})
    assert EffectCalculator.calculate_damage(p, target, 10, combat_manager=cm) == 10


def test_unforged_card_is_inert():
    # Карта без паспорта ковки → урон не меняется (регресс-нейтрально).
    p = Warrior()
    c = _atk()
    f.assign_forge_uid(p, c)
    target = Creature("Враг", 100, 100)
    cm = _CM(p, c, {"shield": 5})
    assert EffectCalculator.calculate_damage(p, target, 10, combat_manager=cm) == 10


# ─── Предохранитель глубины триггеров ─────────────────────────────────────────

def test_trigger_guard_caps_and_resets():
    g = TriggerGuard(max_depth=3)
    assert g.enter() and g.enter() and g.enter()   # 3 входа разрешены
    assert g.enter() is False                       # 4-й обрублен
    g.exit()
    assert g.enter() is True                         # после выхода снова есть слот
    g.depth = 0
    assert g.enter() is True                         # сброс на новый розыгрыш
