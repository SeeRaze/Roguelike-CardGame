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
    forge_damage_multiplier, forge_output_multiplier, pick_tag,
    resolve_forge_record, _s,
    EARLY_ADD_TRIVIAL, EARLY_ADD_NORMAL, EARLY_ADD_RISKY,
    LEG_EMPTY_HAND, LEG_PER_SHIELD, LEG_MISSING_HP,
    CLASS_TAGS, _GENERIC_TAGS,
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
    # Два выполненных ранних тега складываются аддитивно: 1 + 0.5 (normal) + 0.35 (trivial).
    snap = {"shield": 5, "play_index": 0}
    m = forge_damage_multiplier(
        [{"tag_id": "shielded"}, {"tag_id": "first_card"}], snap)
    assert m == 1.0 + EARLY_ADD_NORMAL + EARLY_ADD_TRIVIAL


def test_early_add_off_when_condition_unmet():
    # Условие не выполнено → вклад 0 → множитель 1.0.
    assert forge_damage_multiplier([{"tag_id": "shielded"}], {"shield": 0}) == 1.0


def test_legendary_mult_product():
    # Легендарные перемножаются: empty_hand(×2) × per_shield(1+0.01·50).
    snap = {"hand_after": 0, "shield": 50}
    m = forge_damage_multiplier(
        [{"tag_id": "empty_hand"}, {"tag_id": "per_shield"}], snap)
    assert m == LEG_EMPTY_HAND * (1.0 + LEG_PER_SHIELD * 50)


def test_add_and_mult_compose():
    # (1 + ранний add) × легендарный mult.
    snap = {"shield": 3, "hand_after": 0}
    m = forge_damage_multiplier(
        [{"tag_id": "shielded"}, {"tag_id": "empty_hand"}], snap)
    assert m == (1.0 + EARLY_ADD_NORMAL) * LEG_EMPTY_HAND


def test_unknown_tag_ignored():
    # Незнакомый tag_id не ломает расчёт (вперёд-совместимость пула).
    assert forge_damage_multiplier([{"tag_id": "does_not_exist"}], {}) == 1.0


# ─── Предикаты по снимку (выборочно по каждому семейству) ─────────────────────

def test_low_hp_predicate():
    # low_hp срабатывает ниже половины HP и дает повышенный бонус RISKY.
    assert forge_damage_multiplier([{"tag_id": "low_hp"}], {"hp_frac": 0.4}) \
        == 1.0 + EARLY_ADD_RISKY
    assert forge_damage_multiplier([{"tag_id": "low_hp"}], {"hp_frac": 0.6}) == 1.0


def test_missing_hp_scales():
    # missing_hp ×(1 + scale·доля недостающего HP): на 25% HP при scale=1.0 → ×1.75.
    m = forge_damage_multiplier([{"tag_id": "missing_hp"}], {"hp_frac": 0.25})
    assert abs(m - (1.0 + LEG_MISSING_HP * 0.75)) < 1e-9


def test_first_card_only_first():
    assert forge_damage_multiplier([{"tag_id": "first_card"}], {"play_index": 0}) \
        == 1.0 + EARLY_ADD_TRIVIAL
    assert forge_damage_multiplier([{"tag_id": "first_card"}], {"play_index": 1}) == 1.0


# ─── Null-safety (§10.7) ──────────────────────────────────────────────────────

def test_s_null_safe():
    assert _s(None, "minions") == 0
    assert _s({}, "minions") == 0
    assert _s({"minions": 3}, "minions") == 3
    assert _s(None, "hp_frac", 1.0) == 1.0


def test_multiplier_with_empty_snapshot_safe():
    # Снимок пуст (цель погибла/нет данных) → дефолты, без падения.
    m = forge_damage_multiplier(
        [{"tag_id": "per_shield"}, {"tag_id": "missing_hp"}], {})
    assert m == 1.0     # shield=0 и hp_frac=1.0 (полное HP) → нейтрально


# ─── Smart-weighted выбор тега (§10.1) ────────────────────────────────────────

def test_pick_tag_class_resonant():
    assert pick_tag("Mage", "legendary") == CLASS_TAGS["Mage"]["legendary"]
    assert pick_tag("Warrior", "early") == CLASS_TAGS["Warrior"]["early"]


def test_pick_tag_generic_fallback():
    # Неизвестный класс → generic-теги.
    assert pick_tag("Нечто", "early") == _GENERIC_TAGS["early"]
    assert pick_tag("Нечто", "legendary") == _GENERIC_TAGS["legendary"]


# ─── Драфт тега 1-из-3 (B3, живая игра) ───────────────────────────────────────

def test_draft_возвращает_3_уникальных_тега_канала_тира():
    import random
    from core.ForgeRegistry import draft_tag_choices, TAGS
    rng = random.Random(42)
    choices = draft_tag_choices("Warrior", "early", "damage", k=3, rng=rng)
    assert len(choices) == 3
    assert len(set(choices)) == 3                      # без повторов
    for tag_id in choices:                             # все — early/damage
        assert TAGS[tag_id]["tier"] == "early"
        assert TAGS[tag_id]["channel"] == "damage"


def test_draft_не_лезут_теги_чужого_канала():
    # damage-карта → НИ shield/heal тегов в драфте (фильтр пустышек по каналу).
    import random
    from core.ForgeRegistry import draft_tag_choices, TAGS
    for seed in range(20):
        choices = draft_tag_choices("Mage", "early", "damage", k=3,
                                     rng=random.Random(seed))
        assert all(TAGS[t]["channel"] == "damage" for t in choices)


def test_draft_свой_тег_чаще_чужого_B3():
    # Подкрут B3: класс-резонансный тег выпадает ЧАЩЕ чужого (но чужой возможен).
    import random
    from core.ForgeRegistry import draft_tag_choices
    rng = random.Random(7)
    self_hits = foreign_seen = 0
    for _ in range(400):
        choices = draft_tag_choices("Warrior", "early", "damage", k=3, rng=rng)
        if "shielded" in choices:          # резонанс Воина
            self_hits += 1
        if "low_hp" in choices:            # резонанс Берсерка (чужой)
            foreign_seen += 1
    assert self_hits > foreign_seen        # свой чаще
    assert foreign_seen > 0                # но чужой всё равно кусается (не вырезан)


def test_draft_бедный_канал_возвращает_сколько_есть():
    # Теперь в раннем heal два тега: mending и coffee_break. Драфт вернет оба.
    import random
    from core.ForgeRegistry import draft_tag_choices
    choices = draft_tag_choices("Warrior", "early", "heal", k=3, rng=random.Random(0))
    assert set(choices) == {"mending", "coffee_break"}


# ─── Per-run бан тега (бонус L3 Грейда) ───────────────────────────────────────

def test_draft_бан_исключает_тег():
    # Забаненный тег НЕ появляется в кандидатах ни при каком seed.
    import random
    from core.ForgeRegistry import draft_tag_choices
    for seed in range(30):
        choices = draft_tag_choices("Warrior", "early", "damage", k=3,
                                    rng=random.Random(seed), banned=["shielded"])
        assert "shielded" not in choices


def test_draft_бан_всех_кроме_одного():
    # Забанили весь early/damage пул кроме одного → драфт вернёт ровно его.
    import random
    from core.ForgeRegistry import draft_tag_choices, TAGS
    pool = [t for t, s in TAGS.items()
            if s["tier"] == "early" and s.get("channel", "damage") == "damage"]
    assert len(pool) >= 2
    keep, banned = pool[0], pool[1:]
    choices = draft_tag_choices("Warrior", "early", "damage", k=3,
                                rng=random.Random(1), banned=banned)
    assert choices == [keep]


def test_draft_бан_none_не_меняет_поведение():
    import random
    from core.ForgeRegistry import draft_tag_choices
    a = draft_tag_choices("Warrior", "early", "damage", k=3, rng=random.Random(5))
    b = draft_tag_choices("Warrior", "early", "damage", k=3, rng=random.Random(5),
                          banned=None)
    assert a == b


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
    pol.forge_between_acts(p, deck, class_name="Mage")
    rec = p.deck_forge_state[deck[0]._fuid]
    # Достигли уровня ≥5 → ≥1 слот; первый майлстоун = ранний резонансный тег.
    assert rec["level"] >= 5
    assert len(rec["slots"]) >= 1
    early_tag = CLASS_TAGS["Mage"][MILESTONE_TIER[5]]
    assert rec["slots"][0]["tag_id"] == early_tag


def test_no_slot_below_first_milestone():
    # Уровень < 5 (упёрлись в стартовый кап 4) → слотов нет.
    p = _P()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)   # cap = INITIAL (4)
    p.forge_points = 999
    deck = [_atk("Удар", 6)]
    pol.forge_between_acts(p, deck, class_name="Mage")
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
    pol.forge_between_acts(p, deck, class_name="Warrior")
    rec = p.deck_forge_state[deck[0]._fuid]
    tags = [s["tag_id"] for s in rec["slots"]]
    assert CLASS_TAGS["Warrior"]["legendary"] in tags   # per_shield (×mult)


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


def test_calculate_damage_dry_run_applies_tags_without_side_effects():
    # Новая семантика (аудит механик): dry_run гасит ТОЛЬКО побочки, но считает
    # детерминированный теговый множитель — превью совпадает с ударом. Чтобы убрать
    # теги из «гарантированного» числа карты, используется include_forge=False.
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    card = _atk("Удар", 10)
    card._fuid = 1
    player.deck_forge_state = {1: {"level": 15, "slots": [{"tag_id": "empty_hand"}]}}
    cm = _FakeCombat(player)
    cm._card_being_played = card
    cm._play_snapshot = {"hand_after": 0}     # пустая рука → ×2
    # dry_run ПРИМЕНЯЕТ тег (число превью = число удара)
    assert EffectCalculator.calculate_damage(
        player, target, 10, combat_manager=cm, dry_run=True) == 20
    # include_forge=False убирает тег из «гарантированного» числа
    assert EffectCalculator.calculate_damage(
        player, target, 10, combat_manager=cm, dry_run=True,
        include_forge=False) == 10


# ─── С68: добор контента + калибровка легендарок ──────────────────────────────

def test_no_dead_tags_all_respond_to_snapshot():
    # РЕГРЕСС-ГАРД (С68): каждый тег ОБЯЗАН реагировать хотя бы на один РЕАЛЬНЫЙ
    # ключ снимка (_build_play_snapshot, cardplay.py). Тег, читающий несуществующий
    # ключ, молча мёртв (_s даёт дефолт) → ловушка в живом драфте. Этот тест ловит
    # ровно такой класс ошибки (поймал бы 4 мёртвых тега первой итерации майлстоунов).
    from core.ForgeRegistry import TAGS
    # Пустой снимок + по снимку на каждый ключ с «активным» значением.
    active = {"play_index": 5, "hand_after": 9, "hand_attack": 9, "hp_frac": 0.05,
              "shield": 500, "barrier": 500, "mastery": 500, "minions": 9,
              "tgt_legacy": 500}
    probes = [{}] + [{k: v} for k, v in active.items()]
    dead = [tag_id for tag_id, spec in TAGS.items()
            if len({spec["fn"](s) for s in probes}) == 1]
    assert not dead, f"Мёртвые теги (читают ключ вне снимка): {dead}"


def test_new_shield_heal_tags_live():
    # clean_code (+щит первой картой), coffee_break (+хил из полной руки),
    # refactoring (×щит по Мастерству), healthy_vibe (×хил по щиту+барьеру).
    assert forge_output_multiplier([{"tag_id": "clean_code"}],
                                   {"play_index": 0}, "shield") == 1.0 + EARLY_ADD_NORMAL
    assert forge_output_multiplier([{"tag_id": "clean_code"}],
                                   {"play_index": 3}, "shield") == 1.0
    assert forge_output_multiplier([{"tag_id": "coffee_break"}],
                                   {"hand_after": 4}, "heal") == 1.0 + EARLY_ADD_NORMAL
    assert forge_output_multiplier([{"tag_id": "coffee_break"}],
                                   {"hand_after": 1}, "heal") == 1.0
    assert forge_output_multiplier([{"tag_id": "refactoring"}],
                                   {"mastery": 10}, "shield") == 1.0 + 0.05 * 10
    assert forge_output_multiplier([{"tag_id": "healthy_vibe"}],
                                   {"shield": 20, "barrier": 5}, "heal") == 1.0 + 0.02 * 25


def test_new_damage_class_tags_live():
    # overclocked_ram (Маг: +урон за карту в руке), burnout_rage (Берсерк: ×1.5 при HP<30%),
    # bug_report (Воин: +щит если на цели Легаси — починен на реальный ключ tgt_legacy).
    assert forge_damage_multiplier([{"tag_id": "overclocked_ram"}],
                                   {"hand_after": 5}) == 1.0 + 0.10 * 5
    assert forge_damage_multiplier([{"tag_id": "burnout_rage"}], {"hp_frac": 0.2}) == 1.5
    assert forge_damage_multiplier([{"tag_id": "burnout_rage"}], {"hp_frac": 0.5}) == 1.0
    assert forge_output_multiplier([{"tag_id": "bug_report"}],
                                   {"tgt_legacy": 3}, "shield") == 1.0 + EARLY_ADD_NORMAL
    assert forge_output_multiplier([{"tag_id": "bug_report"}],
                                   {"tgt_legacy": 0}, "shield") == 1.0


def test_legendary_calibration_doubles_at_measured_peak():
    # С68: ×2 откалиброван на ИЗМЕРЕННЫЙ пик стата ceiling-билда (sim, N=40, seed=99):
    # per_combo ×2 при Мастерстве 8; per_shield ×2 при ~100 щита; missing_hp ×2 у смерти.
    assert abs(forge_damage_multiplier([{"tag_id": "per_combo"}], {"mastery": 8}) - 2.0) < 1e-9
    assert abs(forge_damage_multiplier([{"tag_id": "per_shield"}], {"shield": 100}) - 2.0) < 1e-9
    assert abs(forge_damage_multiplier([{"tag_id": "missing_hp"}], {"hp_frac": 0.0}) - 2.0) < 1e-9
