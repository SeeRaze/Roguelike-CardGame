# tests/test_balance_events.py
# Сим-слой %-событий (managers/balance/events.py) — Сессия 39.3, «скачки»
# триединства экономики. Тестируем СТРОИТЕЛЬНЫЕ БЛОКИ: детерминированную каденцию
# (минует спец-этажи), opt-in-нейтральность, исходы гамбита (компаунд MaxHP / FP),
# акт-скейл ставки HP и детерминизм при фикс. seed. Чистая логика, без pygame.
import random

from managers.MapGenerator import FLOORS_PER_ACT
from managers.balance.events import (
    EventPolicy, event_floors, EVENTS_PER_ACT, HP_STAKE_FROM_ACT,
    _act_pct_range,
)


class _FakePlayer:
    def __init__(self, max_hp=100):
        self.max_hp = max_hp
        self.hp = max_hp


class _FakeGM:
    def __init__(self, gold=200):
        self.player_gold = gold


# ─── Каденция (детерминированная структура карты) ─────────────────────────────

def test_event_floors_count_per_act():
    """EVENTS_PER_ACT нод на каждый акт (100 этажей = 5 актов)."""
    floors = event_floors(100, events_per_act=2)
    assert len(floors) == 2 * 5


def test_event_floors_skip_special():
    """События не падают на бои-1/2, костёр (FLOORS_PER_ACT-1) и босса."""
    for f in event_floors(100, events_per_act=3):
        local = (f - 1) % FLOORS_PER_ACT + 1
        assert local not in (1, 2, FLOORS_PER_ACT - 1, FLOORS_PER_ACT)


def test_event_floors_zero_disables():
    assert event_floors(100, events_per_act=0) == set()


# ─── Opt-in нейтральность ─────────────────────────────────────────────────────

def test_no_event_on_plain_floor():
    """Вне EVENT-этажа maybe_event НИЧЕГО не меняет (стейт нетронут)."""
    p, gm = _FakePlayer(), _FakeGM()
    pol = EventPolicy(events_per_act=2)
    plain = next(f for f in range(1, 100) if f not in pol._floors_for(100))
    random.seed(1)
    pol.maybe_event(p, gm, plain, 100)
    assert p.max_hp == 100 and gm.player_gold == 200


# ─── Исходы гамбита (явный win-флаг, без RNG) ─────────────────────────────────

def test_altar_win_grows_max_hp():
    """Победа на алтаре → компаунд-% к max_hp + полное исцеление."""
    p, gm = _FakePlayer(100), _FakeGM(200)
    EventPolicy._altar(p, gm, pct=0.10, win=True, allow_hp_stake=False)
    assert p.max_hp > 100              # бак вырос
    assert p.hp == p.max_hp            # полное исцеление


def test_altar_act1_stakes_gold_not_hp():
    """В акте 1 (allow_hp_stake=False) проигрыш жжёт ЗОЛОТО, не HP."""
    p, gm = _FakePlayer(100), _FakeGM(200)
    EventPolicy._altar(p, gm, pct=0.10, win=False, allow_hp_stake=False)
    assert gm.player_gold < 200        # ставка-золото сожжена
    assert p.hp == 100                 # HP не тронуто (не death-рулетка)


def test_altar_vabank_stakes_hp_when_broke():
    """Ва-банк (act≥3) без золота → ставка ТЕКУЩЕГО HP."""
    p, gm = _FakePlayer(100), _FakeGM(0)
    EventPolicy._altar(p, gm, pct=0.20, win=False, allow_hp_stake=True)
    assert p.hp < 100 and p.hp >= 1    # HP сожжено, но не насмерть


def test_treasury_win_grants_fp():
    """Победа в сокровищнице → золото сожжено, банк FP пополнен."""
    p, gm = _FakePlayer(100), _FakeGM(200)
    EventPolicy._fp_treasury(p, gm, pct=0.50, win=True)
    assert gm.player_gold < 200
    assert getattr(p, "forge_points", 0) > 0


# ─── Акт-скейл (% растёт по актам) ────────────────────────────────────────────

def test_act_scale_grows():
    lo1, hi1 = _act_pct_range(5)     # акт 1
    lo3, hi3 = _act_pct_range(45)    # акт 3
    assert hi1 < lo3                 # диапазоны не пересекаются, акт 3 выше


# ─── Детерминизм при фикс. seed (воспроизводимость baseline) ──────────────────

def test_same_seed_same_outcome():
    pol = EventPolicy(events_per_act=2)
    f = min(pol._floors_for(100))
    def run():
        p, gm = _FakePlayer(100), _FakeGM(500)
        random.seed(42)
        pol.maybe_event(p, gm, f, 100)
        return (p.max_hp, p.hp, gm.player_gold, getattr(p, "forge_points", 0))
    assert run() == run()


# ─── Дефолты-якоря (ловят случайный сдвиг калибровки) ─────────────────────────

def test_calibrated_defaults():
    assert EVENTS_PER_ACT == 2
    assert HP_STAKE_FROM_ACT == 3
