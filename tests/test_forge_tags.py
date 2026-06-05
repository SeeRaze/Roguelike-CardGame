# tests/test_forge_tags.py
# Условные теги прокачки (Сессия 39, шаг 39.2) — _upgrade_design.md §4-5,10.
# Покрываем: математику множителя тегов, предикаты по СНИМКУ (§10.6), null-safety
# (§10.7), резолв паспорта/временных копий (§10.4), Smart-weighted выбор тега,
# выдачу слотов на майлстоунах в ForgePolicy, закон тира наград (§10.5) и
# сквозную врезку множителя в EffectCalculator.calculate_damage.
from core.Creature import Creature
from core.cards.base import Card, DamageEffect
from core.EffectCalculator import EffectCalculator

from core.ForgeRegistry import (
    forge_damage_multiplier, pick_tag, resolve_forge_record, _s,
    EARLY_ADD, LEG_EMPTY_HAND, LEG_PER_MINION, CLASS_TAGS, _GENERIC_TAGS,
)
from managers.balance.forge import (
    ForgePolicy, reward_level_for_floor, MILESTONE_TIER, BOSS_LEVEL_CAPS,
)


def _atk(name, dmg, cost=1):
    return Card(name=name, cost=cost, card_type="attack",
                description="", effects=[DamageEffect(dmg, dmg + 2)])


# ─── Математика множителя (1+Σadd)×Πmult ──────────────────────────────────────

def test_empty_slots_neutral():
    # Нет слотов → 1.0 (регресс-нейтрально).
    assert forge_damage_multiplier([], {}) == 1.0


def test_early_add_accumulates():
    # Два выполненных ранних тега складываются аддитивно: 1 + 0.5 + 0.5.
    snap = {"shield": 5, "play_index": 0}
    m = forge_damage_multiplier(
        [{"tag_id": "shielded"}, {"tag_id": "first_card"}], snap)
    assert m == 1.0 + 2 * EARLY_ADD


def test_early_add_off_when_condition_unmet():
    # Условие не выполнено → вклад 0 → множитель 1.0.
    assert forge_damage_multiplier([{"tag_id": "shielded"}], {"shield": 0}) == 1.0


def test_legendary_mult_product():
    # Легендарные перемножаются: empty_hand(×2) × per_minion(1+0.2·2=1.4).
    snap = {"hand_after": 0, "minions": 2}
    m = forge_damage_multiplier(
        [{"tag_id": "empty_hand"}, {"tag_id": "per_minion"}], snap)
    assert m == LEG_EMPTY_HAND * (1.0 + LEG_PER_MINION * 2)


def test_add_and_mult_compose():
    # (1 + ранний add) × легендарный mult.
    snap = {"shield": 3, "hand_after": 0}
    m = forge_damage_multiplier(
        [{"tag_id": "shielded"}, {"tag_id": "empty_hand"}], snap)
    assert m == (1.0 + EARLY_ADD) * LEG_EMPTY_HAND


def test_unknown_tag_ignored():
    # Незнакомый tag_id не ломает расчёт (вперёд-совместимость пула).
    assert forge_damage_multiplier([{"tag_id": "does_not_exist"}], {}) == 1.0


# ─── Предикаты по снимку (выборочно по каждому семейству) ─────────────────────

def test_low_hp_predicate():
    # low_hp срабатывает ниже половины HP.
    assert forge_damage_multiplier([{"tag_id": "low_hp"}], {"hp_frac": 0.4}) \
        == 1.0 + EARLY_ADD
    assert forge_damage_multiplier([{"tag_id": "low_hp"}], {"hp_frac": 0.6}) == 1.0


def test_missing_hp_scales():
    # missing_hp ×(1 + доля недостающего HP): на 25% HP → ×1.75.
    m = forge_damage_multiplier([{"tag_id": "missing_hp"}], {"hp_frac": 0.25})
    assert abs(m - 1.75) < 1e-9


def test_first_card_only_first():
    assert forge_damage_multiplier([{"tag_id": "first_card"}], {"play_index": 0}) \
        == 1.0 + EARLY_ADD
    assert forge_damage_multiplier([{"tag_id": "first_card"}], {"play_index": 1}) == 1.0


def test_per_poison_scales_with_stacks():
    # Друид: компаунд растёт со стаком яда.
    m1 = forge_damage_multiplier([{"tag_id": "per_poison"}], {"tgt_poison": 10})
    m2 = forge_damage_multiplier([{"tag_id": "per_poison"}], {"tgt_poison": 20})
    assert m2 > m1 > 1.0


# ─── Null-safety (§10.7) ──────────────────────────────────────────────────────

def test_s_null_safe():
    assert _s(None, "minions") == 0
    assert _s({}, "minions") == 0
    assert _s({"minions": 3}, "minions") == 3
    assert _s(None, "hp_frac", 1.0) == 1.0


def test_multiplier_with_empty_snapshot_safe():
    # Снимок пуст (цель погибла/нет данных) → дефолты, без падения.
    m = forge_damage_multiplier(
        [{"tag_id": "per_minion"}, {"tag_id": "missing_hp"}], {})
    assert m == 1.0     # minions=0 и hp_frac=1.0 (полное HP) → нейтрально


# ─── Smart-weighted выбор тега (§10.1) ────────────────────────────────────────

def test_pick_tag_class_resonant():
    assert pick_tag("Druid", "legendary") == CLASS_TAGS["Druid"]["legendary"]
    assert pick_tag("Warrior", "early") == CLASS_TAGS["Warrior"]["early"]


def test_pick_tag_generic_fallback():
    # Неизвестный класс → generic-теги.
    assert pick_tag("Нечто", "early") == _GENERIC_TAGS["early"]
    assert pick_tag("Нечто", "legendary") == _GENERIC_TAGS["legendary"]


# ─── Резолв паспорта и временных копий (§10.4) ────────────────────────────────

class _P:
    pass


def test_resolve_no_state_returns_none():
    card = _atk("Удар", 6)
    assert resolve_forge_record(card, _P()) is None


def test_resolve_by_uid():
    p = _P()
    card = _atk("Удар", 6)
    card._fuid = 7
    p.deck_forge_state = {7: {"level": 5, "slots": [{"tag_id": "first_card"}]}}
    rec = resolve_forge_record(card, p)
    assert rec["level"] == 5


def test_resolve_temp_copy_inherits_parent():
    # Временная копия {parent}_temp_{id} читает запись РОДИТЕЛЯ.
    p = _P()
    p.deck_forge_state = {3: {"level": 10, "slots": []}}
    ghost = _atk("Призрак", 6)
    ghost._fuid = "3_temp_99"
    rec = resolve_forge_record(ghost, p)
    assert rec is not None and rec["level"] == 10


def test_resolve_unknown_uid_none():
    p = _P()
    p.deck_forge_state = {1: {"level": 2, "slots": []}}
    card = _atk("Удар", 6)
    card._fuid = 42
    assert resolve_forge_record(card, p) is None


# ─── ForgePolicy выдаёт слот на майлстоуне ────────────────────────────────────

def test_milestone_opens_slot():
    p = _P()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)
    p.forge_level_cap = 15          # кап не мешает достичь майлстоуна
    p.forge_points = 999
    deck = [_atk("Бомба", 12)]
    pol.forge_between_acts(p, deck, class_name="Druid")
    rec = p.deck_forge_state[deck[0]._fuid]
    # Достигли уровня ≥5 → ≥1 слот; первый майлстоун = ранний резонансный тег.
    assert rec["level"] >= 5
    assert len(rec["slots"]) >= 1
    early_tag = CLASS_TAGS["Druid"][MILESTONE_TIER[5]]
    assert rec["slots"][0]["tag_id"] == early_tag


def test_no_slot_below_first_milestone():
    # Уровень < 5 (упёрлись в стартовый кап 4) → слотов нет.
    p = _P()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)   # cap = INITIAL (4)
    p.forge_points = 999
    deck = [_atk("Удар", 6)]
    pol.forge_between_acts(p, deck, class_name="Druid")
    rec = p.deck_forge_state[deck[0]._fuid]
    assert rec["level"] == 4
    assert rec["slots"] == []


def test_legendary_slot_at_15():
    # Майлстоун 15 → легендарный (×mult) резонансный тег.
    p = _P()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)
    p.forge_level_cap = 15
    p.forge_points = 9999
    deck = [_atk("Бомба", 12)]
    pol.forge_between_acts(p, deck, class_name="Summoner")
    rec = p.deck_forge_state[deck[0]._fuid]
    tags = [s["tag_id"] for s in rec["slots"]]
    assert CLASS_TAGS["Summoner"]["legendary"] in tags   # per_minion (×mult)


# ─── Закон минимального тира наград (§10.5) ───────────────────────────────────

def test_reward_level_for_floor():
    assert reward_level_for_floor(1) == 0       # до первого босса
    assert reward_level_for_floor(20) == 0      # ровно на боссе — ещё не пройден
    assert reward_level_for_floor(21) == BOSS_LEVEL_CAPS[20]   # 5
    assert reward_level_for_floor(41) == BOSS_LEVEL_CAPS[40]   # 10
    assert reward_level_for_floor(61) == BOSS_LEVEL_CAPS[60]   # 15


# ─── Сквозная врезка в EffectCalculator.calculate_damage ──────────────────────

class _FakeCombat:
    """Минимум, который читает calculate_damage: игрок + транзиенты розыгрыша."""
    def __init__(self, player):
        self.player = player
        self._card_being_played = None
        self._play_snapshot = None

    def add_log_message(self, _):
        pass


def test_calculate_damage_applies_tag_multiplier():
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    card = _atk("Удар", 10)
    card._fuid = 1
    player.deck_forge_state = {1: {"level": 15, "slots": [{"tag_id": "empty_hand"}]}}

    cm = _FakeCombat(player)
    cm._card_being_played = card
    cm._play_snapshot = {"hand_after": 0}     # пустая рука → ×2

    dmg = EffectCalculator.calculate_damage(
        player, target, 10, combat_manager=cm)
    assert dmg == 20      # 10 × LEG_EMPTY_HAND(2.0)


def test_calculate_damage_neutral_without_forge_state():
    # Нет deck_forge_state → шаг тегов инертен (регресс-нейтрально).
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    card = _atk("Удар", 10)
    cm = _FakeCombat(player)
    cm._card_being_played = card
    cm._play_snapshot = {"hand_after": 0}
    dmg = EffectCalculator.calculate_damage(
        player, target, 10, combat_manager=cm)
    assert dmg == 10


def test_calculate_damage_dry_run_skips_tags():
    # Превью (dry_run) не применяет теговый множитель.
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    card = _atk("Удар", 10)
    card._fuid = 1
    player.deck_forge_state = {1: {"level": 15, "slots": [{"tag_id": "empty_hand"}]}}
    cm = _FakeCombat(player)
    cm._card_being_played = card
    cm._play_snapshot = {"hand_after": 0}
    dmg = EffectCalculator.calculate_damage(
        player, target, 10, combat_manager=cm, dry_run=True)
    assert dmg == 10
