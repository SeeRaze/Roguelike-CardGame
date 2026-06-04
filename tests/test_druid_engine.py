# tests/test_druid_engine.py
# Проверяем движок Друида «Вирулентность»: рост virulence за скиллы, усиление
# наложений Яда, загнивание яда (не убывает на враге), карта-энейблер.
from core.cards.base import Card, DamageEffect, PoisonEffect
from core.cards.druid import VirulenceEffect, create_virulent_strain
from core.players import Druid, Warrior
from core.enemies import Cultist


class FakeDruidCombat:
    def __init__(self):
        self.player = Druid()
        self.enemy = Cultist("Тест", hp=200, max_hp=200)
        self.enemies = [self.enemy]
        self.log = []
        self.gm = None
        self._elemental_blocked = False

    def add_log_message(self, msg):
        self.log.append(msg)

    def get_target_enemy(self):
        return self.enemy


# ─── Статус ──────────────────────────────────────────────────────────────


def test_virulence_в_status_registry():
    from core.StatusRegistry import STATUSES, get
    assert "virulence" in STATUSES
    data = get("virulence")
    assert data["is_stack"] is True
    assert data["is_duration"] is False
    assert data["abbr"] == "ВИРУЛ"


# ─── PoisonEffect усиливается virulence ──────────────────────────────────


def test_яд_усиливается_вирулентностью():
    """PoisonEffect добавляет player.virulence к величине яда."""
    cm = FakeDruidCombat()
    cm.player.virulence = 4
    PoisonEffect(3, 5).execute(cm.player, cm.enemy, cm, is_upgraded=False)
    # 3 (база) + 4 (virulence) = 7
    assert cm.enemy.get_status("poison") == 7


def test_яд_без_вирулентности_базовый():
    cm = FakeDruidCombat()
    cm.player.virulence = 0
    PoisonEffect(3, 5).execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.enemy.get_status("poison") == 3


def test_не_друид_не_усиливает_яд():
    """У не-Друида virulence=0 (никогда не растёт) → яд базовый."""
    cm = FakeDruidCombat()
    cm.player = Warrior()
    PoisonEffect(3, 5).execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.enemy.get_status("poison") == 3


# ─── Пассив Druid: virulence за скиллы ───────────────────────────────────


def test_пассив_druid_растит_virulence_за_скилл():
    cm = FakeDruidCombat()
    skill = Card("Скилл", 1, "skill", "эффект", [])
    cm.player.on_card_played_passive(skill, cm)
    assert cm.player.virulence == 1
    cm.player.on_card_played_passive(skill, cm)
    assert cm.player.virulence == 2


def test_пассив_druid_атака_не_растит_virulence():
    cm = FakeDruidCombat()
    attack = Card("Удар", 1, "attack", "урон", [DamageEffect(5, 5)])
    cm.player.on_card_played_passive(attack, cm)
    assert cm.player.virulence == 0


def test_virulence_компаунд_за_серию_скиллов():
    """Несколько скиллов подряд накапливают virulence (кат.4)."""
    cm = FakeDruidCombat()
    skill = Card("Скилл", 1, "skill", "эффект", [])
    for _ in range(5):
        cm.player.on_card_played_passive(skill, cm)
    assert cm.player.virulence == 5


# ─── Карта-энейблер ──────────────────────────────────────────────────────


def test_вирулентный_штамм_даёт_virulence():
    cm = FakeDruidCombat()
    card = create_virulent_strain()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.virulence == 2
    card.upgrade()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.virulence == 5  # 2 + 3


def test_вирулентный_штамм_это_скилл():
    card = create_virulent_strain()
    assert card.card_type == "skill"
    assert isinstance(card.effects[0], VirulenceEffect)


# ─── Загнивание яда Друида (не убывает на враге) ─────────────────────────


def test_яд_друида_загнивает_на_враге():
    """У Друида яд на враге НЕ убывает в тике (накопление → движок кат.4)."""
    cm = FakeDruidCombat()  # player = Druid
    cm.enemy.set_status("poison", 8)
    cm.enemy.tick_statuses(cm)
    # Урон 8 прошёл, но стак НЕ убыл (8, не 7)
    assert cm.enemy.get_status("poison") == 8


def test_яд_не_друида_убывает():
    """У других классов яд убывает на 1 в тике (как раньше)."""
    cm = FakeDruidCombat()
    cm.player = Warrior()  # не Друид
    cm.enemy.set_status("poison", 8)
    cm.enemy.tick_statuses(cm)
    assert cm.enemy.get_status("poison") == 7


def test_яд_на_самом_друиде_убывает():
    """Яд, наложенный врагом на самого Друида (self is player), убывает —
    загнивание только для яда НА ВРАГЕ."""
    cm = FakeDruidCombat()  # player = Druid
    cm.player.set_status("poison", 8)
    cm.player.tick_statuses(cm)
    assert cm.player.get_status("poison") == 7


# ─── Сброс между боями ───────────────────────────────────────────────────


def test_virulence_сбрасывается_между_боями():
    cm = FakeDruidCombat()
    cm.player.virulence = 7
    cm.player.reset_combat_statuses()
    assert cm.player.virulence == 0


# ─── Интеграция: скиллы растят яд + накопление ───────────────────────────


def test_серия_скиллов_растит_яд():
    """Полный цикл: скиллы растят virulence → яд-карты бьют сильнее."""
    cm = FakeDruidCombat()
    skill = Card("Скилл", 1, "skill", "эффект", [])

    # Первое наложение яда без накопления
    PoisonEffect(3, 5).execute(cm.player, cm.enemy, cm, is_upgraded=False)
    poison_1 = cm.enemy.get_status("poison")  # 3
    cm.enemy.set_status("poison", 0)          # чистим для замера

    # Сыграли 4 скилла — virulence растёт
    for _ in range(4):
        cm.player.on_card_played_passive(skill, cm)
    assert cm.player.virulence == 4

    PoisonEffect(3, 5).execute(cm.player, cm.enemy, cm, is_upgraded=False)
    poison_2 = cm.enemy.get_status("poison")  # 3 + 4 = 7
    assert poison_2 > poison_1


def test_накопление_яда_друида_за_ходы():
    """Virulence-усиленные наложения + загнивание = растущий dot (компаунд)."""
    cm = FakeDruidCombat()
    cm.player.virulence = 4

    # Ход 1: наложили яд (3 + 4 virulence = 7)
    PoisonEffect(3, 5).execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.enemy.get_status("poison") == 7
    # Тик: урон прошёл, стак НЕ убыл (загнивание)
    cm.enemy.set_status("ignited", 0)
    cm.enemy.tick_statuses(cm)
    assert cm.enemy.get_status("poison") == 7
    # Ход 2: ещё наложение поверх остатка
    PoisonEffect(3, 5).execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.enemy.get_status("poison") == 14  # 7 + 7


# ─── Колода Друида ───────────────────────────────────────────────────────


def test_вирулентный_штамм_в_колоде_друида():
    from core.players.druid import get_druid_deck
    names = [c.name for c in get_druid_deck()]
    assert "Вирулентный штамм" in names


# ─── UI: классификация карты-движка ──────────────────────────────────────


def test_вирулентный_штамм_классифицируется_как_яд():
    """Карта-движок Друида окрашивается в палитру яда (идентичность класса),
    как Frenzy→bleed у Разбойника."""
    from ui.cards.classifier import classify_card
    assert classify_card(create_virulent_strain()) == "poison"
