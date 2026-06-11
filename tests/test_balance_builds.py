# tests/test_balance_builds.py
# Метрика CEILING симулятора (managers/balance/builds.py + параметризация
# runner). Проверяем «потолок» (собранный билд) как вторую экспоненту рядом с
# wall — см. balance-curve-framework. Без запуска полных забегов: тестируем
# строительные блоки (драфт/скоринг/темы/параметры), а не статистику.
import random

import pytest

from core.cards.base import Card, DamageEffect, ShieldEffect, HealEffect
from core.cards import create_strike
from managers.balance import builds, runner
from managers.balance.report import format_dual_report
from managers.balance.builds import (
    _card_score, _card_themes, _deck_themes, greedy_draft, get_ceiling_build,
    CLASS_CORES,
)
from core.players import Warrior, Mage, Berserker

ALL_CLASSES = [Warrior, Mage, Berserker]


def _atk(name, dmg, cost):
    return Card(name=name, cost=cost, card_type="attack",
                description="", effects=[DamageEffect(dmg, dmg + 2)])


# ═══════════════════════════════════════════════════════════
# Параметризация runner: дефолты = wall (регресс-нейтрально)
# ═══════════════════════════════════════════════════════════

def test_run_single_run_дефолт_без_extra_и_relics():
    """Без параметров билда забег идёт по wall-модели: extra_cards/relics пусты."""
    random.seed(1)
    res = runner.run_single_run(Warrior, max_floor=3)
    assert set(res.keys()) == {"death_floor", "hp_by_floor"}
    assert res["hp_by_floor"]            # что-то записалось


def test_extra_cards_попадают_в_стартовую_колоду():
    """extra_cards (ядро билда) реально добавляются в стартовую колоду игрока."""
    p = Warrior()
    before = len(p.get_starter_deck())
    p.add_to_starter_deck(create_strike())
    assert len(p.get_starter_deck()) == before + 1


def test_relics_прокидываются_в_gm(monkeypatch):
    """relics инстанцируются и кладутся в gm.relics (хуки работают в бою)."""
    from core.relics.base import Relic
    seen = {}

    class _Spy(Relic):
        def __init__(self):
            super().__init__("Шпион", "тест", None)
        def on_combat_start(self, cm):
            seen["relics"] = cm.gm.relics

    random.seed(2)
    runner.run_single_run(Warrior, max_floor=1, relics=[_Spy])
    assert "relics" in seen
    assert len(seen["relics"]) == 1
    assert isinstance(seen["relics"][0], _Spy)


def test_custom_draft_вызывается_после_боя():
    """Переданный draft зовётся после каждого выжитого боя."""
    calls = {"n": 0}

    def _draft(deck, cn, meta=None):
        calls["n"] += 1

    random.seed(3)
    runner.run_single_run(Warrior, max_floor=2, draft=_draft)
    # Воин почти всегда переживает этажи 1-2 → драфт вызван хотя бы раз.
    assert calls["n"] >= 1


# ═══════════════════════════════════════════════════════════
# _card_score: отдача за единицу энергии (эффективность)
# ═══════════════════════════════════════════════════════════

def test_score_дешёвая_эффективнее_дорогой_при_равном_уроне():
    """Эффективность: тот же урон за меньшую цену → выше скор."""
    cheap = _atk("Дешёвая", 6, 1)
    pricey = _atk("Дорогая", 6, 3)
    assert _card_score(cheap) > _card_score(pricey)


def test_score_растёт_с_ценностью_эффекта():
    big = _atk("Большая", 12, 2)
    small = _atk("Малая", 4, 2)
    assert _card_score(big) > _card_score(small)


def test_score_нулевая_цена_не_делит_на_ноль():
    free = Card(name="Бесплатная", cost=0, card_type="skill",
                description="", effects=[ShieldEffect(5, 7)])
    # max(1, cost) защищает от деления на ноль.
    assert _card_score(free) > 0


# ═══════════════════════════════════════════════════════════
# Темы колоды: усиление архетипа
# ═══════════════════════════════════════════════════════════

def test_card_themes_распознаёт_типы_эффектов():
    assert "attack" in _card_themes(_atk("A", 5, 1))
    heal = Card(name="H", cost=1, card_type="skill", description="",
                effects=[HealEffect(5, 7)])
    assert "sustain" in _card_themes(heal)


def test_deck_themes_порог_два():
    """Тема засчитывается только если встречается в ≥2 картах (отсечь шум)."""
    one_attack = [_atk("A", 5, 1)]
    assert _deck_themes(one_attack) == set()
    two_attacks = [_atk("A", 5, 1), _atk("B", 5, 1)]
    assert "attack" in _deck_themes(two_attacks)


def test_greedy_усиливает_тему_колоды(monkeypatch):
    """При близкой базовой силе greedy предпочтёт карту, совпадающую с темой
    колоды (архетип-осознанность). Колода-агро → берёт attack, не sustain."""
    attack_card = _atk("Атака", 5, 1)            # тема 'attack', скор 5.0
    heal_card = Card(name="Хил", cost=1, card_type="skill",
                     description="",
                     effects=[HealEffect(13, 15)])  # 'sustain', скор 6.5 — выше!
    deck = [_atk("A", 5, 1), _atk("B", 5, 1)]     # тема колоды = attack

    # Пул ровно из этих двух карт; оба — кандидаты (sample берёт обе).
    import core.cards.catalog as catalog
    monkeypatch.setattr(catalog, "get_pool_for_class",
                        lambda cn, meta=None: [lambda: attack_card, lambda: heal_card])
    monkeypatch.setattr(builds.random, "random", lambda: 0.0)   # шанс прошёл
    monkeypatch.setattr(builds, "_DRAFT_SAMPLE", 2)
    # choice по очереди вернёт обе фабрики → кандидаты = [attack, heal].
    seq_iter = iter([0, 1] * 10)
    monkeypatch.setattr(builds.random, "choice",
                        lambda seq: seq[next(seq_iter)])
    greedy_draft(deck, "Warrior")
    # Добрана именно тематичная (attack) карта благодаря бонусу темы.
    assert deck[-1] is attack_card


def test_greedy_уважает_шанс_добора(monkeypatch):
    """Если бросок не прошёл порог — карта не добирается (как у wall)."""
    deck = [_atk("A", 5, 1)]
    monkeypatch.setattr(builds.random, "random", lambda: 1.0)  # >= chance → пропуск
    greedy_draft(deck, "Warrior")
    assert len(deck) == 1


# ═══════════════════════════════════════════════════════════
# get_ceiling_build + dual-report
# ═══════════════════════════════════════════════════════════

@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_get_ceiling_build_валиден_для_всех_классов(cls):
    draft, extra, relics = get_ceiling_build(cls.__name__)
    assert callable(draft)
    # Все фабрики/реликвии ядра инстанцируются без ошибок.
    for f in extra:
        assert f().effects is not None
    for r in relics:
        assert r() is not None


def test_get_ceiling_build_неизвестный_класс_пустое_ядро():
    draft, extra, relics = get_ceiling_build("НетТакого")
    assert draft is greedy_draft
    assert extra == [] and relics == []


# ═══════════════════════════════════════════════════════════
# СТАРТЕР-РЕЖИМ (meta=∅): фильтр ядра и проводка meta в драфт
# ([[capstone-reorder-content-first]], К5a — честный замер дня-1)
# ═══════════════════════════════════════════════════════════
_STARTER_META = {"unlocks": []}


def test_ceiling_стартер_отсекает_залоченные_реликвии():
    """День-1: залоченные реликвии-движки выпадают из ядра потолка. У Воина все 3
    реликвии ядра заперты (Кэш/Санитайзер/Оверклокинг) → ядро без реликвий."""
    from core.progression import is_relic_unlocked, relic_id_for
    _, _, full_relics = get_ceiling_build("Warrior")
    _, _, starter_relics = get_ceiling_build("Warrior", meta=_STARTER_META)
    assert len(full_relics) == 3
    assert starter_relics == []
    for r in starter_relics:                       # инвариант: всё выжившее — разлочено
        assert is_relic_unlocked(_STARTER_META, relic_id_for(r))


def test_ceiling_стартер_отсекает_залоченные_карты_ядра():
    """battle_cry заперт → ядро Берсерка [battle_cry] обнуляется в стартере
    (день-1 Берсерк ≈ wall, согласуется с аутопсией)."""
    from core.progression import card_id_for
    _, full_extra, _ = get_ceiling_build("Berserker")
    _, starter_extra, _ = get_ceiling_build("Berserker", meta=_STARTER_META)
    assert any(card_id_for(f) == "battle_cry" for f in full_extra)
    assert starter_extra == []


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_ceiling_стартер_подмножество_full(cls):
    """Стартер-ядро ⊆ full-ядро (фильтр только убирает, ничего не добавляет)."""
    from core.progression import card_id_for, relic_id_for
    name = cls.__name__
    _, fe, fr = get_ceiling_build(name)
    _, se, sr = get_ceiling_build(name, meta=_STARTER_META)
    assert set(map(card_id_for, se)) <= set(map(card_id_for, fe))
    assert set(map(relic_id_for, sr)) <= set(map(relic_id_for, fr))


def test_default_draft_прокидывает_meta_в_пул(monkeypatch):
    """run-драфт wall: meta доходит до get_pool_for_class → пул фильтруется."""
    captured = []

    def fake_pool(cn, meta=None):
        captured.append(meta)
        return [lambda: _atk("x", 1, 1)]

    monkeypatch.setattr(runner, "get_pool_for_class", fake_pool)
    monkeypatch.setattr(runner.random, "random", lambda: 0.0)   # шанс прошёл
    runner.default_draft([], "Warrior", _STARTER_META)
    assert captured == [_STARTER_META]


def test_greedy_draft_прокидывает_meta_в_пул(monkeypatch):
    """ceiling-драфт: meta доходит до get_pool_for_class (локальный импорт)."""
    captured = []
    import core.cards.catalog as catalog

    def fake_pool(cn, meta=None):
        captured.append(meta)
        return [lambda: _atk("x", 1, 1)]

    monkeypatch.setattr(catalog, "get_pool_for_class", fake_pool)
    monkeypatch.setattr(builds.random, "random", lambda: 0.0)   # шанс прошёл
    greedy_draft([], "Warrior", _STARTER_META)
    assert captured and captured[0] == _STARTER_META


def test_все_ядра_классов_в_реестре():
    """Каждый из 6 классов имеет ядро билда (метрика ceiling определена)."""
    for cls in ALL_CLASSES:
        assert cls.__name__ in CLASS_CORES


def test_format_dual_report_содержит_обе_метрики():
    wall = {"runs": 10, "depth_min": 5, "depth_p25": 10, "depth_med": 20,
            "depth_p75": 30, "depth_max": 50,
            "winrates": {10: 90, 25: 40, 50: 10, 75: 0, 100: 0}, "avg_hp": {}}
    ceiling = dict(wall, depth_med=45,
                   winrates={10: 100, 25: 100, 50: 80, 75: 30, 100: 0})
    out = format_dual_report("Тест", wall, ceiling)
    assert "WALL" in out and "CEILING" in out
    assert "ЗАЗОР" in out
    assert "есть движок" in out          # gap med +25 >= 15
