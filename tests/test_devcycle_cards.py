# tests/test_devcycle_cards.py
# Пол стартового пула = ЦИКЛ РАЗРАБОТКИ (ярус 1, С60). 4 карты пола заменяют флат
# Удар/Защита/Тяжёлый Клинок/Железная Стена под IT. Проверяем: числа/эффекты =
# шаблон флата; ACCRUE-райдер «Пуш в прод» и «Костыль» навешивают Баг; DEBUG-райдер
# «Код-ревью» вычищает Баг; «Песочница» даёт щит+барьер; сейв-раундтрип; в драфте
# (задача 4: флат снесён, пол в GENERIC; Песочница — UNCOMMON Locked).
from types import SimpleNamespace

from core.players import Warrior
from core.enemies.cultist import Cultist
from core.cards.base import DamageEffect, ShieldEffect, BarrierEffect
from core.cards.bug import AccrueBugEffect, DebugBugEffect, create_bug
from core.cards.devcycle import (
    create_commit, create_push_to_prod, create_code_review, create_sandbox,
)
from core.cards.legacy import create_legacy_patch
from managers.CombatManager import CombatManager


def _make_cm(deck):
    """CombatManager с gm.current_deck == колодой боя (как в живой игре)."""
    gm = SimpleNamespace(current_deck=deck, relics=[])
    return CombatManager(Warrior(), Cultist("Культист", 40, 40), deck, game_manager=gm)


def _eff(card, cls):
    return next((e for e in card.effects if isinstance(e, cls)), None)


# ── Структура: числа = шаблон флата ──────────────────────────────────────────

def test_коммит_чистый_урон():
    c = create_commit()
    assert c.name == "Коммит" and c.cost == 1 and c.card_type == "attack"
    dmg = _eff(c, DamageEffect)
    assert (dmg.base_val, dmg.upgrade_val) == (6, 9)
    assert _eff(c, AccrueBugEffect) is None        # пол-воркхорс, без долга


def test_пуш_в_прод_урон_плюс_accrue():
    c = create_push_to_prod()
    assert c.name == "Пуш в прод" and c.cost == 2 and c.card_type == "attack"
    dmg = _eff(c, DamageEffect)
    assert (dmg.base_val, dmg.upgrade_val) == (14, 20)
    assert _eff(c, AccrueBugEffect) is not None    # ACCRUE-райдер
    # Порядок: урон ДО навешивания долга (долг — последствие действия).
    assert isinstance(c.effects[0], DamageEffect)
    assert isinstance(c.effects[-1], AccrueBugEffect)


def test_код_ревью_щит_плюс_debug():
    c = create_code_review()
    assert c.name == "Код-ревью" and c.cost == 1 and c.card_type == "defense"
    sh = _eff(c, ShieldEffect)
    assert (sh.base_val, sh.upgrade_val) == (5, 8)
    assert _eff(c, DebugBugEffect) is not None     # DEBUG counterplay


def test_песочница_щит_плюс_барьер():
    c = create_sandbox()
    assert c.name == "Песочница" and c.cost == 2 and c.card_type == "defense"
    sh = _eff(c, ShieldEffect)
    bar = _eff(c, BarrierEffect)
    assert (sh.base_val, sh.upgrade_val) == (12, 18)
    assert (bar.base_val, bar.upgrade_val) == (6, 9)   # половина щита


# ── Поведение: ACCRUE / DEBUG через apply ────────────────────────────────────

def test_пуш_в_прод_навешивает_баг_в_колоду():
    deck = [create_commit()]
    cm = _make_cm(deck)
    before = sum(1 for c in deck if getattr(c, "unplayable", False))
    create_push_to_prod().apply(cm.player, cm.enemies[0], cm)
    after = sum(1 for c in deck if getattr(c, "unplayable", False))
    assert after == before + 1


def test_код_ревью_дебажит_баг_из_руки():
    deck = [create_bug(), create_commit()]
    cm = _make_cm(deck)
    bug = next(c for c in cm.deck_manager.hand if getattr(c, "unplayable", False))
    create_code_review().apply(cm.player, cm.enemies[0], cm)
    assert bug not in cm.deck_manager.hand
    assert bug not in deck                          # перманентно из колоды забега


def test_песочница_даёт_щит_и_барьер():
    deck = [create_commit()]
    cm = _make_cm(deck)
    cm.player.shield = 0
    cm.player.barrier = 0
    create_sandbox().apply(cm.player, cm.enemies[0], cm)
    assert cm.player.shield == 12
    assert cm.player.barrier == 6


# ── Костыль теперь тоже копит долг ───────────────────────────────────────────

def test_костыль_получил_accrue_райдер():
    c = create_legacy_patch()
    assert _eff(c, AccrueBugEffect) is not None
    # Прежняя идентичность (урон + Legacy) сохранена.
    assert _eff(c, DamageEffect) is not None


def test_костыль_навешивает_баг():
    deck = [create_commit()]
    cm = _make_cm(deck)
    before = sum(1 for c in deck if getattr(c, "unplayable", False))
    create_legacy_patch().apply(cm.player, cm.enemies[0], cm)
    assert sum(1 for c in deck if getattr(c, "unplayable", False)) == before + 1


# ── Сейв-раундтрип + отсутствие в драфте ─────────────────────────────────────

def test_карты_пола_сериализуются():
    from core.cards.catalog import card_id_of, make_card_by_id
    for factory, cid, name in [
        (create_commit, "commit", "Коммит"),
        (create_push_to_prod, "push_to_prod", "Пуш в прод"),
        (create_code_review, "code_review", "Код-ревью"),
        (create_sandbox, "sandbox", "Песочница"),
    ]:
        assert card_id_of(factory()) == cid
        restored = make_card_by_id(cid)
        assert restored is not None and restored.name == name


def test_карты_пола_в_драфте():
    # Задача 4 (снос флата): пол цикла разработки В пуле выдачи; флат — вышел
    # (фабрики живы для Химика/тестов, но не драфтятся).
    from core.cards.catalog import get_pool_for_class
    names = {f().name for f in get_pool_for_class("Warrior")}
    for n in ("Коммит", "Пуш в прод", "Код-ревью", "Песочница"):
        assert n in names
    for n in ("Удар", "Защита", "Тяжёлый Клинок", "Железная Стена"):
        assert n not in names


def test_песочница_заперта_для_нового_игрока():
    # Песочница = UNCOMMON Locked (награда за прогресс), остальной пол — открыт.
    from core.cards.catalog import get_pool_for_class
    from core.rarity import Rarity
    meta = {"stats": {}, "unlocks": []}
    names = {f().name for f in get_pool_for_class("Warrior", meta=meta)}
    assert "Песочница" not in names
    for n in ("Коммит", "Пуш в прод", "Код-ревью"):
        assert n in names
    assert create_sandbox().rarity == Rarity.UNCOMMON


# ── Проекция описания не корёжится ───────────────────────────────────────────

def test_проекция_описаний_корректна():
    from ui.cards.description import project_forge_values
    # Числа в описании совпадают с эффектами → проекция возвращает валидную строку
    # (число пар N(M) == числу отображаемых эффектов; ACCRUE/DEBUG не считаются).
    for factory in (create_commit, create_push_to_prod, create_code_review,
                    create_sandbox, create_legacy_patch):
        card = factory()
        out = project_forge_values(card)
        assert isinstance(out, str) and out
