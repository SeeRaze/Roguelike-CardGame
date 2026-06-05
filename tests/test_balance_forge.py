# tests/test_balance_forge.py
# Сим-слой ковки карт (managers/balance/forge.py) — Сессия 39, шаг 39.1.
# Тестируем строительные блоки (экономика FP, растущая цена, кап-гейтинг, босс-капы,
# концентрация на ядре, линейный δ, регресс-нейтральность, предохранитель глубины),
# а НЕ статистику забегов. Чистая логика, без pygame.
from core.cards.base import Card, DamageEffect

from managers.balance.forge import (
    ForgePolicy, TriggerGuard, apply_linear_level,
    FORGE_POINTS_PER_COMBAT, FORGE_POINTS_PER_BOSS, LINEAR_BONUS_PER_LEVEL,
    INITIAL_LEVEL_CAP, BOSS_LEVEL_CAPS, MAX_TRIGGER_DEPTH,
)


def _atk(name, dmg, cost=1):
    return Card(name=name, cost=cost, card_type="attack",
                description="", effects=[DamageEffect(dmg, dmg + 2)])


class _FakePlayer:
    """Минимальный игрок: ForgePolicy лениво проставляет ковочные поля сам."""
    pass


# ─── Экономика FP ─────────────────────────────────────────────────────────────

def test_fp_accrual_per_combat():
    p = _FakePlayer()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=3)
    assert p.forge_points == FORGE_POINTS_PER_COMBAT
    pol.on_combat_won(p, floor=4)
    assert p.forge_points == 2 * FORGE_POINTS_PER_COMBAT


def test_fp_boss_bonus():
    p = _FakePlayer()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=20, is_boss=True)
    assert p.forge_points == FORGE_POINTS_PER_COMBAT + FORGE_POINTS_PER_BOSS


def test_initial_cap():
    p = _FakePlayer()
    ForgePolicy().on_combat_won(p, floor=1)
    assert p.forge_level_cap == INITIAL_LEVEL_CAP


# ─── Растущая цена уровня ─────────────────────────────────────────────────────

def test_level_cost_rises_within_tier():
    # cost(level→level+1) = BASE + level·STEP = 1 + level·1
    assert ForgePolicy._level_cost(0) == 1
    assert ForgePolicy._level_cost(1) == 2
    assert ForgePolicy._level_cost(4) == 5


# ─── Босс-капы (увязка шкал §3) ───────────────────────────────────────────────

def test_boss_raises_cap():
    p = _FakePlayer()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)            # cap = INITIAL (4)
    pol.on_boss_defeated(p, floor=20)
    assert p.forge_level_cap == BOSS_LEVEL_CAPS[20]   # 5
    pol.on_boss_defeated(p, floor=40)
    assert p.forge_level_cap == BOSS_LEVEL_CAPS[40]   # 10


def test_boss_cap_never_lowers():
    p = _FakePlayer()
    pol = ForgePolicy()
    pol.on_boss_defeated(p, floor=60)        # cap 15
    pol.on_boss_defeated(p, floor=20)        # 5 < 15 → не понижаем
    assert p.forge_level_cap == BOSS_LEVEL_CAPS[60]


# ─── Кап-гейтинг: ковка не превышает текущий кап ──────────────────────────────

def test_forge_respects_cap():
    p = _FakePlayer()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)            # cap=4, FP=1
    p.forge_points = 999                     # денег вдоволь
    deck = [_atk("Удар", 6)]
    pol.forge_between_acts(p, deck)
    rec = p.deck_forge_state[deck[0]._fuid]
    assert rec["level"] == INITIAL_LEVEL_CAP  # упёрлись ровно в кап (4), не выше


# ─── Концентрация: FP идут в сильнейшую карту ─────────────────────────────────

def test_concentration_pumps_strongest():
    p = _FakePlayer()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)
    p.forge_level_cap = 10                    # кап не мешает
    p.forge_points = 10
    strong = _atk("Бомба", 12)
    weak   = _atk("Тычок", 2)
    deck = [weak, strong]
    pol.forge_between_acts(p, deck)
    lvl_strong = p.deck_forge_state[strong._fuid]["level"]
    # Слабая карта может вообще не получить _fuid: концентрация обрывает цикл на
    # сильной до неё → её просто не касались. Любой из исходов = уровень 0.
    weak_fuid = getattr(weak, "_fuid", None)
    lvl_weak  = p.deck_forge_state.get(weak_fuid, {"level": 0})["level"]
    assert lvl_strong > lvl_weak
    assert lvl_weak == 0                       # вся FP сконцентрирована в сильной


# ─── Линейный δ применяется к числам карты ────────────────────────────────────

def test_linear_delta_applied():
    card = _atk("Удар", 6)             # base 6 / upg 8
    apply_linear_level(card, LINEAR_BONUS_PER_LEVEL)
    eff = card.effects[0]
    assert eff.base_val    == 6 + LINEAR_BONUS_PER_LEVEL
    assert eff.upgrade_val == 8 + LINEAR_BONUS_PER_LEVEL


def test_forge_raises_card_damage():
    p = _FakePlayer()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)             # cap=4, FP=1
    p.forge_points = 99
    card = _atk("Удар", 6)
    pol.forge_between_acts(p, [card])
    # 4 уровня по +δ → base вырос на 4·δ
    assert card.effects[0].base_val == 6 + INITIAL_LEVEL_CAP * LINEAR_BONUS_PER_LEVEL


# ─── Регресс-нейтральность: нет FP → нет изменений ────────────────────────────

def test_no_fp_no_change():
    p = _FakePlayer()
    pol = ForgePolicy()
    pol.on_boss_defeated(p, floor=20)         # есть кап, но FP=0
    card = _atk("Удар", 6)
    pol.forge_between_acts(p, [card])
    assert card.effects[0].base_val == 6      # не тронули
    assert p.deck_forge_state == {}


# ─── deck_forge_state: структура паспорта ─────────────────────────────────────

def test_forge_state_structure():
    p = _FakePlayer()
    pol = ForgePolicy()
    pol.on_combat_won(p, floor=1)
    p.forge_points = 1
    card = _atk("Удар", 6)
    pol.forge_between_acts(p, [card])
    rec = p.deck_forge_state[card._fuid]
    assert set(rec.keys()) == {"level", "slots"}
    assert rec["level"] == 1
    assert rec["slots"] == []                 # слоты-теги — шаг 39.2


# ─── Предохранитель глубины триггеров (гард-рейл §10.2) ───────────────────────

def test_trigger_guard_caps_depth():
    g = TriggerGuard(max_depth=MAX_TRIGGER_DEPTH)
    for _ in range(MAX_TRIGGER_DEPTH):
        assert g.enter() is True
    assert g.enter() is False                 # 6-й вход (при cap=5) обрублен
    g.exit()
    assert g.enter() is True                  # освободили слот — снова можно


def test_trigger_guard_exit_floor():
    g = TriggerGuard(max_depth=2)
    g.exit()                                   # не уходит ниже нуля
    assert g.depth == 0
    assert g.enter() is True
