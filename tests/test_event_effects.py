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


def test_все_опции_событий_применяются_без_ошибок():
    # Целостность данные↔эффекты: каждая опция каждого базового события должна
    # примениться без исключений (ловит опечатки в ключах/битые %). HP не уходит
    # ниже 1, золото не в минус.
    from ui.events.event_data import _BASE_POOL
    from ui.events.event_effects import apply_option
    from core.players import Warrior

    for event in _BASE_POOL:
        for option in event["options"]:
            gm = SimpleNamespace(
                player=Warrior(), player_gold=200, current_floor=12,
                event_result="", event_result_card=None,
                relics=[], add_card=lambda c: None,
            )
            gm.player.hp = gm.player.max_hp
            apply_option(option, gm)
            assert gm.player.hp >= 1
            assert gm.player_gold >= 0


def test_данные_событий_перешли_на_проценты():
    # Шаг 2b: HP/золото в данных НЕ должны использовать плоские flat-ключи
    # (heal:/lose_hp:/gain_gold:/lose_gold:) — только %-варианты. gain_card/
    # gain_relic/skip/gain_random_card остаются как есть.
    from ui.events.event_data import _BASE_POOL
    flat_hp_gold = {"heal", "lose_hp", "gain_gold", "lose_gold"}
    for event in _BASE_POOL:
        for option in event["options"]:
            for eff in option["effects"]:
                key = eff.split(":", 1)[0]
                assert key not in flat_hp_gold, (
                    f"{event['title']}: плоский ключ '{key}' должен быть %-вариантом")


# ── Блок 4 (С65): новые примитивы (FP-ось / случайная реликвия / Баг-цена) ────
def _gm_full():
    from core.players import Warrior
    return SimpleNamespace(
        player=Warrior(), player_gold=100, current_floor=10,
        event_result="", event_result_card=None,
        relics=[], meta=None, deck=[],
    )


def test_gain_forge_растит_fp():
    gm = _gm_full()
    gm.player.forge_points = 0
    apply_effect("gain_forge:5", gm)
    assert gm.player.forge_points == 5


def test_gain_random_relic_выдаёт_реликвию():
    gm = _gm_full()
    apply_effect("gain_random_relic", gm)
    assert len(gm.relics) == 1                 # одна реликвия добавлена в инвентарь


def test_gain_random_relic_не_дублирует():
    # Дедуп: реликвия, которая уже есть, не выдаётся повторно (берём другую).
    from core.relics.starter import Линтер
    gm = _gm_full()
    gm.relics = [Линтер()]
    apply_effect("gain_random_relic", gm)
    имена = [type(r).__name__ for r in gm.relics]
    assert len(gm.relics) == 2 and len(set(имена)) == 2


def test_accrue_bug_кладёт_баги_в_колоду():
    gm = _gm_full()
    gm.add_card = lambda c: gm.deck.append(c)
    apply_effect("accrue_bug:2", gm)
    assert len(gm.deck) == 2
    assert all(c.name == "Баг" for c in gm.deck)


# ── С72: подсистема ИСПЫТАНИЙ под легендарки (флаги-цепочки + condition-опции) ──
def test_set_flag_ставит_флаг_забега():
    gm = _gm()
    assert getattr(gm, "death_march", False) is False
    apply_effect("set_flag:death_march", gm)
    assert gm.death_march is True


def test_set_remove_flag_полный_цикл():
    # Завязка ставит флаг → развязка снимает (мост многошаговых испытаний).
    gm = _gm()
    apply_effect("set_flag:quest", gm)
    assert gm.quest is True
    apply_effect("remove_flag:quest", gm)
    assert gm.quest is False


def test_gain_relic_марш_смерти_выдаётся():
    # Легендарка-за-испытание: Марш смерти изъят из рандом-пулов и доступен ТОЛЬКО
    # именным gain_relic (развязка испытания). Реестр _get_relic_class знает его.
    gm = _gm_full()
    apply_effect("gain_relic:МаршСмерти", gm)
    assert len(gm.relics) == 1
    assert type(gm.relics[0]).__name__ == "МаршСмерти"


def test_option_visible_гейтит_опцию_по_condition():
    # condition-опции (С72): опция без condition видна; с condition — по предикату.
    from ui.EventView import option_visible
    gm = _gm(hp=10)
    assert option_visible({"label": "x"}, gm) is True
    assert option_visible({"label": "x", "condition": lambda g: g.player.hp > 1}, gm) is True
    assert option_visible({"label": "x", "condition": lambda g: g.player.hp > 100}, gm) is False
