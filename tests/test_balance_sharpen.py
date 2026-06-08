# tests/test_balance_sharpen.py
# Заточка (Sharpen) — DPS-сток FP в множитель урона + ТЕМА-ГЕЙТ (Сессия 39.4).
# См. память balance-findings-dps-bound. Покрываем: механику sharpen (FP→atk_mult,
# компаунд, нехватка FP), тема-гейт классификации колоды, проактивный дрен под
# угрозой, маршрутизацию invest_if_threatened (офенс→урон / оборона→Max HP) и
# сквозную врезку atk_mult в EffectCalculator (шаг 8). Чистая логика, без pygame.
from core.Creature import Creature
from core.cards.base import (
    Card, DamageEffect, ShieldEffect, HealEffect, PoisonEffect,
)
from core.cards.debuff.bleed import BleedEffect
from core.EffectCalculator import EffectCalculator

from managers.balance.forge import (
    ForgePolicy, deck_prefers_sharpen, _card_is_defensive,
    SHARPEN_FP_COST, SHARPEN_ATK_PCT,
)


def _atk(name="Удар", dmg=6, cost=1):
    return Card(name=name, cost=cost, card_type="attack",
                description="", effects=[DamageEffect(dmg, dmg + 2)])


def _shield(name="Блок", val=5, cost=1):
    return Card(name=name, cost=cost, card_type="skill",
                description="", effects=[ShieldEffect(val, val + 2)])


def _heal(name="Лечение", val=5, cost=1):
    return Card(name=name, cost=cost, card_type="skill",
                description="", effects=[HealEffect(val, val + 2)])


class _FakePlayer:
    """Минимальный игрок: ForgePolicy лениво проставляет ковочные поля сам."""
    def __init__(self, max_hp=80):
        self.max_hp = max_hp
        self.hp = max_hp


# ─── Механика Заточки: FP → компаунд-% atk_mult ───────────────────────────────

def test_sharpen_spends_fp_and_compounds():
    p = _FakePlayer()
    ForgePolicy().on_combat_won(p, floor=1)
    p.forge_points = SHARPEN_FP_COST * 2
    assert ForgePolicy.sharpen(p) is True
    assert p.forge_points == SHARPEN_FP_COST
    assert p.atk_mult == 1.0 * (1 + SHARPEN_ATK_PCT)
    # Второй раз — КОМПАУНД (множитель умножается, не складывается).
    assert ForgePolicy.sharpen(p) is True
    assert abs(p.atk_mult - (1 + SHARPEN_ATK_PCT) ** 2) < 1e-9


def test_sharpen_insufficient_fp_noop():
    p = _FakePlayer()
    ForgePolicy().on_combat_won(p, floor=1)
    p.forge_points = SHARPEN_FP_COST - 1
    assert ForgePolicy.sharpen(p) is False
    assert getattr(p, "atk_mult", 1.0) == 1.0
    assert p.forge_points == SHARPEN_FP_COST - 1


# ─── Тема-гейт: классификация карт и колоды ───────────────────────────────────

def test_card_is_defensive():
    assert _card_is_defensive(_shield()) is True          # чистый щит
    assert _card_is_defensive(_heal()) is True            # чистый хил
    assert _card_is_defensive(_atk()) is False            # урон
    # Смешанная (урон + щит) — НЕ оборонная (офенс доминирует).
    mixed = Card(name="Гибрид", cost=1, card_type="attack", description="",
                 effects=[DamageEffect(4, 6), ShieldEffect(4, 6)])
    assert _card_is_defensive(mixed) is False
    # Дот (яд/кровь) — офенс, не оборона.
    pois = Card(name="Яд", cost=1, card_type="skill", description="",
                effects=[PoisonEffect(3, 5)])
    bld = Card(name="Кровь", cost=1, card_type="attack", description="",
               effects=[BleedEffect(3, 5)])
    assert _card_is_defensive(pois) is False
    assert _card_is_defensive(bld) is False


def test_deck_prefers_sharpen():
    # Офенс-колода (атак больше обороны) → Заточка.
    off = [_atk(), _atk(), _shield()]
    assert deck_prefers_sharpen(off) is True
    # Оборонная колода (обороны ≥ прочего) → Закалка.
    deff = [_shield(), _shield(), _heal(), _atk()]
    assert deck_prefers_sharpen(deff) is False
    # Пустая колода → не точим.
    assert deck_prefers_sharpen([]) is False


# ─── Проактивный дрен под угрозой ─────────────────────────────────────────────

def test_sharpen_if_threatened_drains_under_threat():
    # max_hp очень мал → любой входящий урон превышает порог → дренит весь FP.
    p = _FakePlayer(max_hp=1)
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)
    p.forge_points = SHARPEN_FP_COST * 3 + 2     # хватает на 3 заточки
    did = pol.sharpen_if_threatened(p, floor=19)
    assert did is True
    assert p.forge_points == 2                    # дренило по cost, остаток < cost
    assert abs(p.atk_mult - (1 + SHARPEN_ATK_PCT) ** 3) < 1e-9


def test_sharpen_if_threatened_skips_when_safe():
    # max_hp огромен → угроза ниже порога → не точим (FP цел).
    p = _FakePlayer(max_hp=10_000_000)
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)
    p.forge_points = SHARPEN_FP_COST * 3
    assert pol.sharpen_if_threatened(p, floor=1) is False
    assert getattr(p, "atk_mult", 1.0) == 1.0
    assert p.forge_points == SHARPEN_FP_COST * 3


# ─── Маршрутизация стока выживаемости по тема-гейту (С57: разнесена по осям) ───
# Заточка (офенс, FP, ForgePolicy) vs Закалка (оборона, ЗОЛОТО, EconomyPolicy).
# Маршрутизация живёт в runner (нужны обе политики); тут проверяем обе ветки.

def test_offense_deck_routes_to_sharpen():
    p = _FakePlayer(max_hp=50)                     # порог угрозы сработает на эт.19
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)
    p.forge_points = 100
    base_hp = p.max_hp
    assert deck_prefers_sharpen([_atk(), _atk()]) is True
    pol.sharpen_if_threatened(p, floor=19)
    assert getattr(p, "atk_mult", 1.0) > 1.0      # точил урон
    assert p.max_hp == base_hp                     # Max HP не трогал


def test_defense_deck_routes_to_temper():
    from managers.balance.economy import EconomyPolicy

    class _GM:
        player_gold = 100000

    p = _FakePlayer(max_hp=50)                     # порог угрозы сработает на эт.19
    gm = _GM()
    assert deck_prefers_sharpen([_shield(), _shield(), _heal()]) is False
    EconomyPolicy().temper_if_threatened(gm, p, floor=19)
    assert p.max_hp > 50                           # закаляла Max HP
    assert getattr(p, "atk_mult", 1.0) == 1.0      # урон не точила
    assert gm.player_gold < 100000                 # списала золото


# ─── Сквозная врезка в EffectCalculator (шаг 8) ───────────────────────────────

def test_calculate_damage_applies_atk_mult():
    player = Creature("Игрок", 50, 50)
    player.atk_mult = 2.0
    target = Creature("Враг", 100, 100)

    class _CM:
        player = None
        def add_log_message(self, _): pass
    cm = _CM()
    cm.player = player
    dmg = EffectCalculator.calculate_damage(player, target, 10, combat_manager=cm)
    assert dmg == 20                               # 10 × atk_mult(2.0)


def test_calculate_damage_atk_mult_neutral_default():
    # Без atk_mult (дефолт 1.0) шаг инертен — регресс-нейтрально.
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)

    class _CM:
        player = None
        def add_log_message(self, _): pass
    cm = _CM()
    cm.player = player
    assert EffectCalculator.calculate_damage(player, target, 10, combat_manager=cm) == 10


def test_calculate_damage_atk_mult_applies_in_dry_run():
    # Аудит механик (С40): dry_run гасит ТОЛЬКО побочки, но считает Заточку —
    # превью на карте теперь совпадает с фактическим ударом (костыль в
    # description.py больше не нужен).
    player = Creature("Игрок", 50, 50)
    player.atk_mult = 2.0
    target = Creature("Враг", 100, 100)

    class _CM:
        player = None
        def add_log_message(self, _): pass
    cm = _CM()
    cm.player = player
    dmg = EffectCalculator.calculate_damage(player, target, 10, combat_manager=cm,
                                            dry_run=True)
    assert dmg == 20                               # превью применяет Заточку ×2.0
