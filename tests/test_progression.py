# tests/test_progression.py
# Ярусная прогрессия классов (С50): TIER1 всегда открыт, ярус 2 открывается за
# достижения и пишется в мету, Демиург — маяк (всегда закрыт). Чистый модуль —
# без боя и pygame, работаем на голом мета-словаре.

from core.progression import (
    TIER1, class_tier, is_unlocked, newly_unlocked, UNLOCK_CONDITIONS,
)


def _meta(**stats) -> dict:
    """Мини-мета: только нужные статы + пустой список анлоков (как у нового игрока)."""
    return {"stats": stats, "unlocks": []}


# ── ярусы ────────────────────────────────────────────────────────────────────────

def test_ярус_1_это_воин_маг_берсерк():
    assert TIER1 == ("Warrior", "Mage", "Berserker")
    for cls in TIER1:
        assert class_tier(cls) == 1


def test_ярус_2_и_демиург():
    assert class_tier("Rogue") == 2
    assert class_tier("Druid") == 2
    assert class_tier("Summoner") == 2
    assert class_tier("Demiurge") == 3


def test_неизвестный_класс_дефолт_ярус_1():
    assert class_tier("Ктотамещё") == 1


# ── is_unlocked ────────────────────────────────────────────────────────────────────

def test_ярус_1_всегда_открыт_даже_без_меты():
    for cls in TIER1:
        assert is_unlocked(None, cls) is True
        assert is_unlocked(_meta(), cls) is True


def test_ярус_2_закрыт_у_нового_игрока():
    m = _meta()
    assert is_unlocked(m, "Rogue") is False
    assert is_unlocked(m, "Druid") is False
    assert is_unlocked(m, "Summoner") is False


def test_записанный_анлок_открывает_класс():
    m = _meta()
    m["unlocks"].append("Rogue")
    assert is_unlocked(m, "Rogue") is True
    assert is_unlocked(m, "Druid") is False   # другой класс не задет


def test_демиург_всегда_закрыт_маяк():
    # Даже с максимальным прогрессом — условие всегда False.
    m = _meta(best_floor=999, total_bosses=99)
    newly_unlocked(m)
    assert is_unlocked(m, "Demiurge") is False
    assert "Demiurge" not in m["unlocks"]


# ── newly_unlocked ──────────────────────────────────────────────────────────────────

def test_условие_не_выполнено_ничего_не_открывает():
    m = _meta(best_floor=3, total_bosses=0)
    assert newly_unlocked(m) == []
    assert m["unlocks"] == []


def test_этаж_открывает_разбойника():
    m = _meta(best_floor=5)            # Rogue: этаж >= 5
    fresh = newly_unlocked(m)
    assert "Rogue" in fresh
    assert is_unlocked(m, "Rogue") is True


def test_босс_открывает_друида():
    m = _meta(total_bosses=1)          # Druid: боссов >= 1
    fresh = newly_unlocked(m)
    assert "Druid" in fresh
    assert "Summoner" not in fresh     # этаж недостаточный


def test_идемпотентность_повтор_без_прогресса_пуст():
    m = _meta(best_floor=6, total_bosses=1)   # откроет Rogue+Druid+Summoner
    first = newly_unlocked(m)
    assert set(first) == {"Rogue", "Druid", "Summoner"}
    assert newly_unlocked(m) == []            # второй раз — нечего открывать
    assert set(m["unlocks"]) == {"Rogue", "Druid", "Summoner"}


def test_newly_unlocked_создаёт_ключ_unlocks_если_нет():
    m = {"stats": {"best_floor": 5}}          # без ключа unlocks
    newly_unlocked(m)
    assert "unlocks" in m
    assert "Rogue" in m["unlocks"]


def test_все_условия_вызываемы_и_булевы():
    # Контракт реестра: каждое условие — функция меты → bool.
    m = _meta(best_floor=10, total_bosses=2)
    for cls, cond in UNLOCK_CONDITIONS.items():
        assert isinstance(cond(m), bool), cls
