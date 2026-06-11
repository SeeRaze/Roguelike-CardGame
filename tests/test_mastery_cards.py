# tests/test_mastery_cards.py
# Проверяем движок Мага «Мастерство стихий»: бонус урона, рост от комбо, карты.
from core.cards.mage import (
    MasteryEffect, create_arcane_focus, create_elemental_surge,
)
from core.EffectCalculator import EffectCalculator
from core.players import Mage
from core.enemies import Cultist


class FakeMasteryCombat:
    def __init__(self, player=None):
        self.player = player if player is not None else Mage()
        self.enemy = Cultist("Тест", hp=200, max_hp=200)
        self.enemy.base_test_damage = 5
        self.enemy.base_test_shield = 3
        self.enemies = [self.enemy]
        self.log = []
        self.gm = None
        self._elemental_blocked = False
        self._combo_triggered = False

    def add_log_message(self, msg):
        self.log.append(msg)

    def get_target_enemy(self):
        return self.enemy


# ─── Статус и бонус урона ────────────────────────────────────────────────


def test_mastery_в_status_registry():
    from core.StatusRegistry import STATUSES, get
    assert "mastery" in STATUSES
    data = get("mastery")
    assert data["is_stack"] is True
    assert data["is_duration"] is False
    assert data["abbr"] == "МАСТ"


def test_mastery_добавляет_урон_в_калькуляторе():
    """Игрок с mastery=3 наносит +3 урона."""
    cm = FakeMasteryCombat()
    player = cm.player
    # Без мастерства
    dmg0 = EffectCalculator.calculate_damage(
        player, cm.enemy, 10, None, cm, dry_run=True
    )
    # С мастерством
    player.mastery = 3
    dmg3 = EffectCalculator.calculate_damage(
        player, cm.enemy, 10, None, cm, dry_run=True
    )
    assert dmg3 == dmg0 + 3


def test_mastery_только_для_атак_игрока():
    """Мастерство врага не учитывается (только is_player_attack)."""
    cm = FakeMasteryCombat()
    enemy = cm.enemy
    enemy.mastery = 5  # врагу не должно помочь
    # Враг атакует игрока — combat_manager.player != enemy
    dmg = EffectCalculator.calculate_damage(
        enemy, cm.player, 10, None, cm, dry_run=True
    )
    # Без бонуса мастерства (10 базовый, возможны другие модификаторы)
    assert dmg <= 10  # мастерство врага не добавилось


# ─── MasteryEffect и карты ───────────────────────────────────────────────


def test_mastery_effect_накладывает():
    cm = FakeMasteryCombat()
    effect = MasteryEffect(2, 3)
    effect.execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.player.mastery == 2
    effect.execute(cm.player, cm.enemy, cm, is_upgraded=True)
    assert cm.player.mastery == 5


def test_тайное_сосредоточение_даёт_мастерство():
    cm = FakeMasteryCombat()
    card = create_arcane_focus()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.mastery == 2
    card.upgrade()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.mastery == 5


def test_стихийный_всплеск_вешает_всё():
    cm = FakeMasteryCombat()
    card = create_elemental_surge()
    hp_before = cm.enemy.hp
    card.apply(cm.player, cm.enemy, cm)
    assert cm.enemy.hp < hp_before          # урон
    assert cm.enemy.get_status("coffee") == 3  # разлитый кофе
    assert cm.enemy.get_status("legacy") == 3  # legacy-код
    assert cm.player.mastery == 1           # мастерство


# ─── Пассив Мага: мастерство растёт от комбо ─────────────────────────────


def test_пассив_мага_даёт_мастерство_при_комбо():
    """Когда _combo_triggered=True, пассив Мага даёт +1 мастерства."""
    cm = FakeMasteryCombat()
    # Симулируем срабатывание комбо
    cm._combo_triggered = True
    # Нужен deck_manager для draw_cards — мокаем
    class FakeDeck:
        def draw_cards(self, n):
            return 0
    cm.deck_manager = FakeDeck()
    mastery_before = cm.player.mastery
    cm.player.on_card_played_passive(None, cm)
    assert cm.player.mastery == mastery_before + 1
    assert cm._combo_triggered is False  # флаг сброшен


def test_пассив_мага_без_комбо_не_даёт_мастерство():
    cm = FakeMasteryCombat()
    cm._combo_triggered = False
    cm.player.on_card_played_passive(None, cm)
    assert cm.player.mastery == 0


def test_мастерство_компаунд_растёт_за_бой():
    """Несколько комбо подряд накапливают мастерство (кат.4)."""
    cm = FakeMasteryCombat()

    class FakeDeck:
        def draw_cards(self, n):
            return 0
    cm.deck_manager = FakeDeck()

    for _ in range(3):
        cm._combo_triggered = True
        cm.player.on_card_played_passive(None, cm)
    assert cm.player.mastery == 3  # компаунд: +1 за каждое комбо


# ─── Каталог ─────────────────────────────────────────────────────────────


def test_карты_мастерства_в_каталоге_мага():
    from core.cards.catalog import CLASS_FACTORIES
    mage_factories = CLASS_FACTORIES.get("Mage", [])
    names = [f.__name__ for f in mage_factories]
    assert "create_arcane_focus" in names
    assert "create_elemental_surge" in names
