# tests/test_progression.py
# Ярусная прогрессия классов (С50): TIER1 всегда открыт, ярус 2 открывается за
# достижения и пишется в мету, Демиург — маяк (всегда закрыт). Чистый модуль —
# без боя и pygame, работаем на голом мета-словаре.

import core.progression as prog
from core.progression import (
    TIER1, class_tier, is_unlocked, newly_unlocked, UNLOCK_CONDITIONS,
    LOCKED_CARDS, LOCKED_RELICS, card_id_for, relic_id_for,
    is_card_unlocked, is_relic_unlocked, dev_unlock_all,
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


# ── анлок карт/артефактов (С57, step 1) ──────────────────────────────────────
def test_card_id_снимает_префикс_create():
    def create_strike(): pass
    def create_fire_breath(): pass
    assert card_id_for(create_strike) == "strike"
    assert card_id_for(create_fire_breath) == "fire_breath"


def test_relic_id_это_имя_класса():
    class ТочильныйКамень:
        pass
    assert relic_id_for(ТочильныйКамень) == "ТочильныйКамень"


def test_реестры_locked_наполнены_разметкой():
    # К3: разметка страманом — узкий стартовый пул (часть заперта за мета-прогрессию).
    assert len(LOCKED_CARDS) == 37      # 37 из 50 generic заперты (+Барьер Воина +ПАР Мага, С57)
    assert len(LOCKED_RELICS) == 27     # 27 из 33 артефактов заперты
    # Базовые карты НЕ заперты (стартовые).
    for starter in ("strike", "defend", "heavy_blade", "iron_wall"):
        assert starter not in LOCKED_CARDS
    # Стартовые артефакты по осям НЕ заперты.
    for starter in ("ТочильныйКамень", "Заплатка", "СчастливаяМонетка"):
        assert starter not in LOCKED_RELICS


def test_стартовая_карта_всегда_доступна():
    # Карта не в LOCKED_CARDS доступна даже без меты.
    assert is_card_unlocked(None, "strike") is True
    assert is_card_unlocked(_meta(), "strike") is True


def test_locked_карта_требует_анлок_в_мете(monkeypatch):
    monkeypatch.setattr(prog, "LOCKED_CARDS", {"fire_breath"})
    assert is_card_unlocked(_meta(), "fire_breath") is False      # не открыта
    assert is_card_unlocked(None, "fire_breath") is False         # без меты — закрыта
    assert is_card_unlocked({"unlocks": ["fire_breath"]}, "fire_breath") is True
    assert is_card_unlocked(_meta(), "strike") is True            # стартовая — мимо


def test_locked_артефакт_требует_анлок_в_мете(monkeypatch):
    monkeypatch.setattr(prog, "LOCKED_RELICS", {"СердцеТитана"})
    assert is_relic_unlocked(_meta(), "СердцеТитана") is False
    assert is_relic_unlocked({"unlocks": ["СердцеТитана"]}, "СердцеТитана") is True
    assert is_relic_unlocked(_meta(), "ТочильныйКамень") is True  # стартовый — мимо


# ── Дев-флаг «полный доступ» (С57, под тест-сессии) ──────────────────────────

def test_дев_флаг_дефолт_выключен(monkeypatch):
    # Без env и без meta-ключа флаг выключен → поведение байт-в-байт прежнее.
    monkeypatch.delenv("ROGUELIKE_DEV_UNLOCK", raising=False)
    assert dev_unlock_all(None) is False
    assert dev_unlock_all(_meta()) is False


def test_дев_флаг_через_env(monkeypatch):
    monkeypatch.setenv("ROGUELIKE_DEV_UNLOCK", "1")
    assert dev_unlock_all(None) is True
    # env=0 → выключен (не ложно-положительный).
    monkeypatch.setenv("ROGUELIKE_DEV_UNLOCK", "0")
    assert dev_unlock_all(None) is False


def test_дев_флаг_через_мету(monkeypatch):
    monkeypatch.delenv("ROGUELIKE_DEV_UNLOCK", raising=False)
    assert dev_unlock_all({"dev_unlock_all": True}) is True
    assert dev_unlock_all({"dev_unlock_all": False}) is False


def test_дев_флаг_открывает_всё(monkeypatch):
    # Взведённый флаг открывает залоченные классы/карты/артефакты, минуя unlocks.
    monkeypatch.setenv("ROGUELIKE_DEV_UNLOCK", "1")
    monkeypatch.setattr(prog, "LOCKED_CARDS", {"fire_breath"})
    monkeypatch.setattr(prog, "LOCKED_RELICS", {"СердцеТитана"})
    assert is_unlocked(_meta(), "Druid") is True          # тир-2 без анлока
    assert is_card_unlocked(_meta(), "fire_breath") is True
    assert is_relic_unlocked(_meta(), "СердцеТитана") is True


def test_дев_флаг_не_трогает_sim_путь(monkeypatch):
    # Sim/baseline зовут с meta=None и без env → флаг молчит, локи в силе.
    monkeypatch.delenv("ROGUELIKE_DEV_UNLOCK", raising=False)
    monkeypatch.setattr(prog, "LOCKED_CARDS", {"fire_breath"})
    assert is_card_unlocked(None, "fire_breath") is False
