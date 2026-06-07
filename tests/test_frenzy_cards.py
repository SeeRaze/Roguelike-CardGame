# tests/test_frenzy_cards.py
# Проверяем движок Разбойника «Кровожадность»: рост frenzy за атаки,
# усиление Кровотечения, карты.
from core.cards.base import Card, DamageEffect
from core.cards.debuff.bleed import BleedEffect, create_lacerate
from core.cards.rogue import (
    create_bloodlust, create_serrated_edge,
)
from core.players import Rogue
from core.enemies import Cultist


class FakeFrenzyCombat:
    def __init__(self):
        self.player = Rogue()
        self.enemy = Cultist("Тест", hp=200, max_hp=200)
        self.enemy.base_test_damage = 5
        self.enemy.base_test_shield = 3
        self.enemies = [self.enemy]
        self.log = []
        self.gm = None
        self._elemental_blocked = False

    def add_log_message(self, msg):
        self.log.append(msg)

    def get_target_enemy(self):
        return self.enemy


# ─── Статус ──────────────────────────────────────────────────────────────


def test_frenzy_в_status_registry():
    from core.StatusRegistry import STATUSES, get
    assert "frenzy" in STATUSES
    data = get("frenzy")
    assert data["is_stack"] is True
    assert data["is_duration"] is False
    assert data["abbr"] == "КРОВОЖ"


# ─── BleedEffect усиливается frenzy ──────────────────────────────────────


def test_bleed_усиливается_кровожадностью():
    """BleedEffect добавляет player.frenzy к величине кровотечения."""
    cm = FakeFrenzyCombat()
    cm.player.frenzy = 4
    effect = BleedEffect(3, 4)
    effect.execute(cm.player, cm.enemy, cm, is_upgraded=False)
    # 3 (база) + 4 (frenzy) = 7
    assert cm.enemy.get_status("bleed") == 7


def test_bleed_без_frenzy_базовый():
    cm = FakeFrenzyCombat()
    cm.player.frenzy = 0
    effect = BleedEffect(3, 4)
    effect.execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.enemy.get_status("bleed") == 3


# ─── Пассив Rogue: frenzy за атаки ───────────────────────────────────────


def test_пассив_rogue_растит_frenzy_за_атаку():
    cm = FakeFrenzyCombat()
    attack_card = Card("Удар", 1, "attack", "урон", [DamageEffect(5, 5)])
    cm.player.on_card_played_passive(attack_card, cm)
    assert cm.player.frenzy == 1
    cm.player.on_card_played_passive(attack_card, cm)
    assert cm.player.frenzy == 2


def test_пассив_rogue_скилл_не_растит_frenzy():
    cm = FakeFrenzyCombat()
    skill_card = Card("Скилл", 1, "skill", "эффект", [])
    cm.player.on_card_played_passive(skill_card, cm)
    assert cm.player.frenzy == 0


def test_frenzy_компаунд_за_серию_атак():
    """Несколько атак подряд накапливают frenzy (кат.4)."""
    cm = FakeFrenzyCombat()
    attack = Card("Удар", 1, "attack", "урон", [DamageEffect(5, 5)])
    for _ in range(5):
        cm.player.on_card_played_passive(attack, cm)
    assert cm.player.frenzy == 5


# ─── Карты ───────────────────────────────────────────────────────────────


def test_жажда_крови_даёт_frenzy():
    cm = FakeFrenzyCombat()
    card = create_bloodlust()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.frenzy == 2
    card.upgrade()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.frenzy == 5  # 2 + 3


def test_зубчатый_клинок_бьёт_кровит_и_растит():
    cm = FakeFrenzyCombat()
    card = create_serrated_edge()
    hp_before = cm.enemy.hp
    card.apply(cm.player, cm.enemy, cm)
    assert cm.enemy.hp < hp_before          # урон
    assert cm.enemy.get_status("bleed") >= 2  # кровотечение
    assert cm.player.frenzy == 1            # frenzy


def test_зубчатый_клинок_с_накопленным_frenzy():
    """С frenzy=5 зубчатый клинок накладывает усиленное кровотечение."""
    cm = FakeFrenzyCombat()
    cm.player.frenzy = 5
    card = create_serrated_edge()
    card.apply(cm.player, cm.enemy, cm)
    # bleed = 2 (база) + 5 (frenzy на момент BleedEffect) = 7
    # FrenzyEffect добавляет +1 ПОСЛЕ (порядок эффектов), но bleed уже наложен
    assert cm.enemy.get_status("bleed") == 7
    assert cm.player.frenzy == 6  # 5 + 1 от FrenzyEffect


# ─── Интеграция: серия атак растит урон ──────────────────────────────────


def test_серия_атак_растит_dot_урон():
    """Полный цикл: атаки растят frenzy → bleed-карты бьют сильнее."""
    cm = FakeFrenzyCombat()
    attack = Card("Удар", 1, "attack", "урон", [DamageEffect(5, 5)])
    lacerate = create_lacerate()  # bleed 3

    # Первая bleed-карта без накопления
    lacerate.apply(cm.player, cm.enemy, cm)
    cm.player.on_card_played_passive(lacerate, cm)  # +1 frenzy (это attack)
    bleed_1 = cm.enemy.get_status("bleed")

    # Сыграли 3 атаки — frenzy растёт
    for _ in range(3):
        cm.player.on_card_played_passive(attack, cm)
    assert cm.player.frenzy == 4  # 1 (lacerate) + 3 (атаки)

    # Сброс bleed для чистоты измерения
    cm.enemy.set_status("bleed", 0)
    lacerate2 = create_lacerate()
    lacerate2.apply(cm.player, cm.enemy, cm)
    bleed_2 = cm.enemy.get_status("bleed")
    # bleed_2 = 3 + 4 (frenzy) = 7 > bleed_1 = 3
    assert bleed_2 > bleed_1


# ─── Каталог ─────────────────────────────────────────────────────────────


def test_карты_frenzy_в_каталоге_rogue():
    from core.cards.catalog import CLASS_FACTORIES
    rogue_factories = CLASS_FACTORIES.get("Rogue", [])
    names = [f.__name__ for f in rogue_factories]
    assert "create_bloodlust" in names
    assert "create_serrated_edge" in names


# ─── Врождённый bleed-half Разбойника (движок-фундамент) ─────────────────


def test_кровотечение_разбойника_убывает_вдвое():
    """У Разбойника bleed убывает вдвое, а не в ноль (накопление dot)."""
    cm = FakeFrenzyCombat()  # player = Rogue
    cm.enemy.set_status("bleed", 8)
    # take_damage сначала срабатывает bleed-при-ударе, тикаем напрямую
    cm.enemy.tick_statuses(cm)
    # Разбойник: 8 // 2 = 4 (не 0)
    assert cm.enemy.get_status("bleed") == 4


def test_кровотечение_не_разбойника_сбрасывается():
    """У других классов bleed сбрасывается в ноль (без Гнилого Клыка)."""
    from core.players import Warrior
    cm = FakeFrenzyCombat()
    cm.player = Warrior()  # не Разбойник
    cm.enemy.set_status("bleed", 8)
    cm.enemy.tick_statuses(cm)
    assert cm.enemy.get_status("bleed") == 0


def test_накопление_bleed_разбойника_за_ходы():
    """Frenzy-усиленные наложения + half-decay = растущий dot (компаунд)."""
    cm = FakeFrenzyCombat()
    cm.player.frenzy = 4

    # Ход 1: наложили bleed (2 + 4 frenzy = 6)
    from core.cards.debuff.bleed import BleedEffect
    BleedEffect(2, 3).execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.enemy.get_status("bleed") == 6
    # Тик: 6 // 2 = 3 остаётся
    cm.enemy.set_status("ignited", 0)  # чистим прочее
    cm.enemy.tick_statuses(cm)
    assert cm.enemy.get_status("bleed") == 3
    # Ход 2: ещё наложение поверх остатка
    BleedEffect(2, 3).execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.enemy.get_status("bleed") == 9  # 3 + 6
