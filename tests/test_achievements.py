# tests/test_achievements.py
# Этап 3 С70: реестр ачивок MVP (core/achievements.py) — предикаты на синтетических
# снапшотах, грант, идемпотентность, интеграция через шину meta_events.

import pytest

from core import achievements, meta_events


def _meta(xp=0, grade_xp=0, done=()):
    return {
        "xp": xp, "grade_xp": grade_xp,
        "achievements": list(done),
        "casino_seen": [], "casino_bans": [],
        "unlocks": [], "keepsake": None,
    }


def _victory_facts(**overrides):
    """Базовый снапшот «победа Тестировщика на этаже 2 без потери HP»."""
    base = {
        "player_class": "Warrior", "floor": 2, "is_boss": False, "victory": True,
        "hp_start": 50, "hp_end": 50, "max_hp": 50,
        "peak_discipline": 0, "peak_mastery": 0, "peak_hp_debt": 0,
        "lucky_prompt_high_mastery": False, "big_boil_hit": False,
    }
    base.update(overrides)
    return base


@pytest.fixture(autouse=True)
def clean_bus():
    """Между тестами очищаем шину и подписки achievements."""
    meta_events.clear()
    achievements._reset_handlers_for_tests()
    yield
    meta_events.clear()
    achievements._reset_handlers_for_tests()


# ─── Предикаты ачивок ─────────────────────────────────────────────────────────

def test_clean_review_grants_on_warrior_no_hp_loss():
    meta = _meta()
    facts = _victory_facts(hp_start=50, hp_end=50, floor=2)
    granted = achievements.check_all(meta, facts)
    assert "clean_review" in granted
    assert "ДашбордМетрик" in meta["unlocks"]
    assert "clean_review" in meta["achievements"]
    assert meta["xp"] == 50          # бонус Опыта


def test_clean_review_rejected_on_floor_1():
    meta = _meta()
    facts = _victory_facts(floor=1)
    granted = achievements.check_all(meta, facts)
    assert "clean_review" not in granted


def test_clean_review_rejected_with_hp_loss():
    meta = _meta()
    facts = _victory_facts(hp_start=50, hp_end=40)
    granted = achievements.check_all(meta, facts)
    assert "clean_review" not in granted


def test_clean_review_rejected_for_mage():
    meta = _meta()
    facts = _victory_facts(player_class="Mage", floor=5)
    granted = achievements.check_all(meta, facts)
    assert "clean_review" not in granted


def test_discipline_8_grants():
    meta = _meta()
    facts = _victory_facts(peak_discipline=8, floor=4)
    granted = achievements.check_all(meta, facts)
    assert "discipline_8" in granted
    assert "steel_barricade" in meta["unlocks"]


def test_discipline_8_threshold_is_inclusive():
    meta = _meta()
    facts = _victory_facts(peak_discipline=7)
    granted = achievements.check_all(meta, facts)
    assert "discipline_8" not in granted


def test_lucky_prompt_mastery_grants_for_mage():
    meta = _meta()
    facts = _victory_facts(player_class="Mage", lucky_prompt_high_mastery=True)
    granted = achievements.check_all(meta, facts)
    assert "lucky_prompt_mastery" in granted
    assert "Автодополнение" in meta["unlocks"]


def test_lucky_prompt_rejected_without_flag():
    meta = _meta()
    facts = _victory_facts(player_class="Mage", lucky_prompt_high_mastery=False)
    assert "lucky_prompt_mastery" not in achievements.check_all(meta, facts)


def test_big_boil_grants_for_mage():
    meta = _meta()
    facts = _victory_facts(player_class="Mage", big_boil_hit=True)
    granted = achievements.check_all(meta, facts)
    assert "big_boil" in granted
    assert "boil" in meta["unlocks"]


def test_hp_debt_crunch_grants_for_berserker():
    meta = _meta()
    facts = _victory_facts(player_class="Berserker", peak_hp_debt=20)
    granted = achievements.check_all(meta, facts)
    assert "hp_debt_crunch" in granted
    assert "final_deploy" in meta["unlocks"]


def test_hp_debt_crunch_threshold_is_inclusive():
    meta = _meta()
    facts = _victory_facts(player_class="Berserker", peak_hp_debt=19)
    assert "hp_debt_crunch" not in achievements.check_all(meta, facts)


def test_first_boss_grants_any_class():
    meta = _meta()
    facts = _victory_facts(is_boss=True, floor=20)
    granted = achievements.check_all(meta, facts)
    assert "first_boss" in granted
    assert "ДеплойВПятницу" in meta["unlocks"]


def test_first_boss_rejected_on_regular_combat():
    meta = _meta()
    facts = _victory_facts(is_boss=False)
    assert "first_boss" not in achievements.check_all(meta, facts)


# ─── Грант: идемпотентность и поток Опыта ─────────────────────────────────────

def test_grant_is_idempotent():
    """Повторная проверка той же ачивки не повторяет грант (анти-дубль).
    hp_end<hp_start ломает clean_review → discipline_8 единственная сработавшая."""
    meta = _meta()
    facts = _victory_facts(peak_discipline=8, hp_start=50, hp_end=40)
    g1 = achievements.check_all(meta, facts)
    g2 = achievements.check_all(meta, facts)
    assert g1 == ["discipline_8"]
    assert g2 == []
    assert meta["xp"] == 50          # бонус начислен ОДИН раз
    assert meta["achievements"].count("discipline_8") == 1


def test_check_all_none_meta_or_facts_returns_empty():
    assert achievements.check_all(None, _victory_facts()) == []
    assert achievements.check_all(_meta(), None) == []


def test_check_all_can_grant_multiple_at_once():
    """Бой может закрыть несколько ачивок: победа над боссом Тестировщиком без HP-потерь
    закрывает И clean_review И first_boss."""
    meta = _meta()
    facts = _victory_facts(player_class="Warrior", floor=20, is_boss=True,
                           hp_start=60, hp_end=60)
    granted = achievements.check_all(meta, facts)
    assert "clean_review" in granted
    assert "first_boss"   in granted
    assert meta["xp"] == 100         # 50 × 2 бонуса


# ─── Интеграция через шину meta_events ────────────────────────────────────────

def test_register_handlers_subscribes_once():
    achievements.register_handlers()
    assert meta_events.subscribers_count("combat_finished") == 1
    achievements.register_handlers()             # дубль не задваивает
    assert meta_events.subscribers_count("combat_finished") == 1


def test_publish_combat_finished_grants_achievement():
    """e2e: после publish('combat_finished') подписчик ачивок отрабатывает."""
    achievements.register_handlers()
    meta = _meta()
    facts = _victory_facts(peak_discipline=8)
    meta_events.publish("combat_finished", facts=facts, meta=meta)
    assert "discipline_8" in meta["achievements"]
    assert "steel_barricade" in meta["unlocks"]


def test_achievement_unlocked_event_fires_with_payload():
    """При успешном гранте publishes 'achievement_unlocked' с ach_id.
    hp_end<hp_start ломает clean_review → только discipline_8 трегерится."""
    received = []
    meta_events.subscribe("achievement_unlocked",
                          lambda ach_id=None, ach=None, **_: received.append((ach_id, ach.title)))
    meta = _meta()
    facts = _victory_facts(peak_discipline=8, hp_start=50, hp_end=40)
    achievements.check_all(meta, facts)
    assert len(received) == 1
    ach_id, title = received[0]
    assert ach_id == "discipline_8"
    assert title == "Регламент соблюдён"
