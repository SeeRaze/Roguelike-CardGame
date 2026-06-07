# tests/test_persistent_relics.py
# Персистентный слой по забегу (шаг №5 framework): растущие реликвии копят
# КОМПАУНД через хук on_boss_defeated (босс-этажи 20/40/60/80/100). Проверяем
# флагман «Корона Вознесения» + проводку в сим-раннере (предусловие boss-filter:
# симулятор обязан видеть чекпойнты-ворота).
from core.relics import КоронаВознесения, ALL_RELICS
from core.relics.base import Relic
from core.players import Druid


# ─── Хук в базовом классе ────────────────────────────────────────────────


def test_базовый_relic_имеет_хук_on_boss_defeated():
    """Хук есть у всех реликвий (no-op по умолчанию) — расширяемость слоя."""
    assert hasattr(Relic, "on_boss_defeated")
    # no-op не падает
    Relic("x", "y").on_boss_defeated(player=None, combat_manager=None)


def test_корона_в_пуле_реликвий():
    names = [r().name for r in ALL_RELICS]
    assert "Корона Вознесения" in names


# ─── Рост множителя за боссов ─────────────────────────────────────────────


def test_старт_без_боссов_множитель_1():
    r = КоронаВознесения()
    assert r._mult == 1.0
    # урон не меняется без побеждённых боссов
    assert r.on_damage_calculated(10, is_player_attack=True) == 10


def test_один_босс_растит_множитель():
    g = КоронаВознесения.GROWTH_PER_BOSS
    r = КоронаВознесения()
    r.on_boss_defeated(player=None, combat_manager=None)
    assert round(r._mult, 4) == round(g, 4)


def test_компаунд_за_пять_боссов():
    """5 боссов забега → ×GROWTH^5 (множительный компаунд, кат.4)."""
    g = КоронаВознесения.GROWTH_PER_BOSS
    r = КоронаВознесения()
    for _ in range(5):
        r.on_boss_defeated(player=None, combat_manager=None)
    assert round(r._mult, 4) == round(g ** 5, 4)


# ─── Применение к урону ───────────────────────────────────────────────────


def test_урон_усиливается_после_босса():
    g = КоронаВознесения.GROWTH_PER_BOSS
    r = КоронаВознесения()
    r.on_boss_defeated(player=None, combat_manager=None)   # ×g
    # база 100 (чистое округление) — урон растёт ровно на множитель
    assert r.on_damage_calculated(100, is_player_attack=True) == int(round(100 * g))
    assert r.on_damage_calculated(100, is_player_attack=True) > 100


def test_урон_компаунд_за_пять_боссов():
    g = КоронаВознесения.GROWTH_PER_BOSS
    r = КоронаВознесения()
    for _ in range(5):
        r.on_boss_defeated(player=None, combat_manager=None)
    assert r.on_damage_calculated(100, is_player_attack=True) == int(round(100 * g ** 5))


def test_вражеские_атаки_не_усиливаются():
    """Бонус только для атак ИГРОКА (как ПроклятаяКорона)."""
    r = КоронаВознесения()
    for _ in range(5):
        r.on_boss_defeated(player=None, combat_manager=None)
    assert r.on_damage_calculated(10, is_player_attack=False) == 10


# ─── Лог при срабатывании ─────────────────────────────────────────────────


def test_лог_при_победе_над_боссом():
    from tests.conftest import FakeCombat
    cm = FakeCombat(Druid(), Druid())
    КоронаВознесения().on_boss_defeated(cm.player, cm)
    assert any("Корона Вознесения" in m for m in cm.log)


# ─── Сброс между забегами (свежий инстанс) ────────────────────────────────


def test_свежий_инстанс_сбрасывает_компаунд():
    """Состояние живёт на инстансе → новый забег = новый инстанс = mult 1.0.
    (В сим-раннере relic_objs = [r() ...] на каждый забег; в игре — новый забег.)"""
    r1 = КоронаВознесения()
    for _ in range(5):
        r1.on_boss_defeated(player=None, combat_manager=None)
    assert r1._mult > 1.0
    r2 = КоронаВознесения()   # «новый забег»
    assert r2._mult == 1.0


# ─── Интеграция: сим-раннер триггерит хук на босс-этажах ──────────────────


class _SpyRelic(Relic):
    """Реликвия-шпион: записывает этажи, на которых сработал on_boss_defeated."""
    def __init__(self):
        super().__init__("Шпион", "тест")
        self.boss_floors = []

    def on_boss_defeated(self, player, combat_manager=None):
        floor = getattr(getattr(combat_manager, "gm", None), "current_floor", None)
        self.boss_floors.append(floor)


def test_сим_раннер_триггерит_хук_на_этажах_20_40(monkeypatch):
    """run_single_run зовёт on_boss_defeated ровно на босс-этажах (local_step==20).
    Монкипатчим бой на «всегда выжил», чтобы добраться до этажа 40 детерминированно."""
    import managers.balance.runner as R

    monkeypatch.setattr(R.BotCombatManager, "run_bot_loop", lambda self: True)

    # Подсовываем свой спай-инстанс через фабрику, ловим его наружу
    spy_holder = []

    class _SpyFactory(_SpyRelic):
        def __init__(self):
            super().__init__()
            spy_holder.append(self)

    R.run_single_run(Druid, max_floor=40, relics=[_SpyFactory])
    assert len(spy_holder) == 1
    assert spy_holder[0].boss_floors == [20, 40]


# ─── Сердце Бездны (оборонный компаунд: +%макс.HP за босса) ───────────────


def test_сердце_бездны_в_пуле():
    from core.relics import СердцеБездны, RELIC_POOL
    from core.rarity import Rarity
    names = [r().name for r in ALL_RELICS]
    assert "Сердце Бездны" in names
    assert СердцеБездны in RELIC_POOL[Rarity.EPIC]


def test_сердце_бездны_растит_макс_хп_и_лечит():
    """Босс: +15% к макс. HP + мгновенный хил на ту же дельту."""
    from core.relics import СердцеБездны
    p = Druid()
    p.hp = p.max_hp           # полное HP
    base = p.max_hp
    gain = max(1, round(base * СердцеБездны.GROWTH_PCT))
    СердцеБездны().on_boss_defeated(p)
    assert p.max_hp == base + gain
    assert p.hp == base + gain          # хил на дельту → снова полное


def test_сердце_бездны_хил_не_превышает_новый_максимум():
    from core.relics import СердцеБездны
    p = Druid()
    p.hp = 1                  # почти мёртв
    base = p.max_hp
    gain = max(1, round(base * СердцеБездны.GROWTH_PCT))
    СердцеБездны().on_boss_defeated(p)
    assert p.hp == 1 + gain
    assert p.hp <= p.max_hp


def test_сердце_бездны_компаунд_за_боссов():
    """Несколько боссов компаундят макс. HP (растущая дельта от 15%)."""
    from core.relics import СердцеБездны
    p = Druid()
    r = СердцеБездны()
    start = p.max_hp
    for _ in range(3):
        r.on_boss_defeated(p)
    # 3 раза по +15% от текущего → строго больше линейного 3×15%
    assert p.max_hp > start * 1.45
