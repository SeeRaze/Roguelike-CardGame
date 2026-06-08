# tests/test_event_effects.py
# %-эффекты живых событий (HP-ось, шаг 2 эконом-дуги). HP → % от MAX HP
# (масштаб-инвариантно), золото аддитивно (потери %-кошелька, прибыль floor×K).
from types import SimpleNamespace
from ui.events.event_effects import apply_effect


def _gm(hp=60, max_hp=100, gold=100, floor=10):
    return SimpleNamespace(
        player=SimpleNamespace(hp=hp, max_hp=max_hp),
        player_gold=gold,
        current_floor=floor,
        event_result="",
        event_result_card=None,
    )


def test_heal_pct_от_max_hp():
    gm = _gm(hp=50, max_hp=100)
    apply_effect("heal_pct:0.30", gm)
    assert gm.player.hp == 80          # +30% от 100, не выше max


def test_heal_pct_не_превышает_max():
    gm = _gm(hp=95, max_hp=100)
    apply_effect("heal_pct:0.30", gm)
    assert gm.player.hp == 100


def test_lose_hp_pct_от_max_не_убивает():
    gm = _gm(hp=10, max_hp=100)
    apply_effect("lose_hp_pct:0.30", gm)   # -30 от max, но пол = 1
    assert gm.player.hp == 1


def test_lose_hp_pct_масштаб_по_max():
    # Тот же % бьёт пропорционально пулу: больше max → больнее.
    g_small = _gm(hp=60, max_hp=60)
    g_big   = _gm(hp=200, max_hp=200)
    apply_effect("lose_hp_pct:0.25", g_small)
    apply_effect("lose_hp_pct:0.25", g_big)
    assert g_small.player.hp == 60 - 15
    assert g_big.player.hp == 200 - 50


def test_lose_gold_pct_от_кошелька():
    gm = _gm(gold=200)
    apply_effect("lose_gold_pct:0.30", gm)
    assert gm.player_gold == 140


def test_lose_gold_pct_не_уходит_в_минус():
    gm = _gm(gold=0)
    apply_effect("lose_gold_pct:0.50", gm)
    assert gm.player_gold == 0


def test_gain_gold_floor_масштаб_по_этажу():
    gm_early = _gm(gold=0, floor=5)
    gm_late  = _gm(gold=0, floor=40)
    apply_effect("gain_gold_floor:3", gm_early)
    apply_effect("gain_gold_floor:3", gm_late)
    assert gm_early.player_gold == 15      # 3 * 5
    assert gm_late.player_gold == 120      # 3 * 40 (аддитивно, не экспонента)


def test_temper_spirit_растит_max_hp_и_хилит_дельту():
    gm = _gm(hp=70, max_hp=100)
    apply_effect("temper_spirit:0.12", gm)
    assert gm.player.max_hp == 112         # +12%
    assert gm.player.hp == 82              # хил на ту же дельту (+12)


def test_temper_spirit_процент_масштаб_инвариантен():
    # У большого пула прирост больше в абсолюте — компаунд выживаемости.
    gm = _gm(hp=200, max_hp=200)
    apply_effect("temper_spirit:0.10", gm)
    assert gm.player.max_hp == 220


def test_флэт_ключи_живы_для_back_compat():
    gm = _gm(hp=50, max_hp=100, gold=100)
    apply_effect("heal:20", gm)
    assert gm.player.hp == 70
    apply_effect("gain_gold:40", gm)
    assert gm.player_gold == 140
