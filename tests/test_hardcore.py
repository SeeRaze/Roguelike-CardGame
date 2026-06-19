# tests/test_hardcore.py
# С70 полировка (П3): хардкор-Ставка «Восхождение» (бонус L3 Грейда).
# Штрафы: враги бьют ×1.25 (DAMAGE-мод, не игрок) + макс. HP ×0.75 (DECKBUILD).
# Гейт по Грейду L3. is_hardcore_active читает RuleStack.

from types import SimpleNamespace

from core.rules import RuleStack, STAKES, is_hardcore_active
from core.rules import stakes as S
from core.Creature import Creature
from core.EffectCalculator import EffectCalculator
from core import meta_currency


def _gm(player=None):
    return SimpleNamespace(
        rulestack=RuleStack(), current_deck=[],
        player=player if player is not None else Creature("Игрок", 80, 80),
        relics=[], stats={}, current_floor=1, meta=None,
    )


def _enemy_hit(gm, base=10):
    enemy = Creature("Враг", 50, 50)
    cm = SimpleNamespace(player=gm.player, gm=gm, add_log_message=lambda _: None)
    return EffectCalculator.calculate_damage(enemy, gm.player, base,
                                             game_manager=gm, combat_manager=cm)


def _player_hit(gm, base=10):
    target = Creature("Враг", 100, 100)
    cm = SimpleNamespace(player=gm.player, gm=gm, add_log_message=lambda _: None)
    return EffectCalculator.calculate_damage(gm.player, target, base,
                                             game_manager=gm, combat_manager=cm)


# ─── Реестр / гейт ────────────────────────────────────────────────────────────

def test_hardcore_in_registry_gated_l3():
    assert S.HARDCORE_STAKE_ID in STAKES
    assert STAKES[S.HARDCORE_STAKE_ID].min_grade == 3


def test_gating_excludes_below_l3_includes_at_l3():
    def visible(grade_xp):
        grade = meta_currency.current_grade({"grade_xp": grade_xp})
        return [st.id for st in STAKES.values()
                if getattr(st, "min_grade", 0) <= grade]
    assert S.HARDCORE_STAKE_ID not in visible(0)       # L0
    assert S.HARDCORE_STAKE_ID not in visible(600)     # L2
    assert S.HARDCORE_STAKE_ID in visible(1800)        # L3
    # Обычные Ставки видны всегда.
    assert "ascetic" in visible(0) and "fragile" in visible(0)


# ─── Штрафы ───────────────────────────────────────────────────────────────────

def test_hardcore_enemies_hit_harder():
    gm = _gm()
    STAKES[S.HARDCORE_STAKE_ID].activate(gm)
    assert _enemy_hit(gm, 10) == 12          # ×1.25 → int(12.5)


def test_hardcore_player_damage_unchanged():
    # У Восхождения нет урон-награды игроку (в отличие от Хрупкости).
    gm = _gm()
    STAKES[S.HARDCORE_STAKE_ID].activate(gm)
    assert _player_hit(gm, 10) == 10


def test_hardcore_cuts_max_hp():
    player = Creature("Игрок", 80, 80)
    gm = _gm(player=player)
    STAKES[S.HARDCORE_STAKE_ID].activate(gm)
    assert player.max_hp == 60               # 75%
    assert player.hp == 60                    # текущее клампится


# ─── is_hardcore_active ───────────────────────────────────────────────────────

def test_is_hardcore_active_lifecycle():
    gm = _gm()
    assert is_hardcore_active(gm) is False
    STAKES[S.HARDCORE_STAKE_ID].activate(gm)
    assert is_hardcore_active(gm) is True
    gm.rulestack.clear()                      # новый забег без хардкора
    assert is_hardcore_active(gm) is False


def test_is_hardcore_active_no_rulestack():
    assert is_hardcore_active(SimpleNamespace()) is False


def test_other_stake_is_not_hardcore():
    gm = _gm()
    STAKES["fragile"].activate(gm)
    assert is_hardcore_active(gm) is False


# ─── Награды (П3b): золото ×0.5, Опыт ×1.5 ────────────────────────────────────

def test_multipliers_off_by_default():
    gm = _gm()
    assert S.hardcore_gold_multiplier(gm) == 1.0
    assert S.hardcore_xp_multiplier(gm) == 1.0


def test_multipliers_on_with_hardcore():
    gm = _gm()
    STAKES[S.HARDCORE_STAKE_ID].activate(gm)
    assert S.hardcore_gold_multiplier(gm) == S.HARDCORE_GOLD_MULT
    assert S.hardcore_xp_multiplier(gm) == S.HARDCORE_XP_MULT


def test_gold_reward_halved_under_hardcore():
    import random
    from managers.RewardManager import build_rewards

    def _gold(rewards):
        return next(r["value"] for r in rewards if r["type"] == "gold")

    # Один seed → одинаковый базовый бросок золота; разница только в множителе.
    random.seed(777)
    normal = build_rewards(_gm(), is_boss=False, is_elite=False)
    g_n = _gold(normal)

    gm = _gm()
    STAKES[S.HARDCORE_STAKE_ID].activate(gm)
    random.seed(777)
    hard = build_rewards(gm, is_boss=False, is_elite=False)
    g_h = _gold(hard)

    assert g_h == int(g_n * S.HARDCORE_GOLD_MULT)
    assert g_h < g_n


def test_xp_flow_amounts_under_hardcore():
    # Документируем итоговые суммы потока Опыта при хардкоре (×1.5):
    assert int(10 * S.HARDCORE_XP_MULT) == 15      # обычный этаж
    assert int(30 * S.HARDCORE_XP_MULT) == 45      # доп. за босса
