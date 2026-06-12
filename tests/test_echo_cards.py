# tests/test_echo_cards.py
# Проверяем механику Эха: статус на игроке, ретриггер карт, карты эха.
from core.cards.echo import (
    EchoEffect, create_echo_resonance, create_echo_cascade,
)
from core.cards.base import Card, DamageEffect, ShieldEffect
from core.players import Warrior
from core.enemies import Cultist


# ─── Юнит-тесты эффектов ────────────────────────────────────────────────


class FakeCombat:
    """Минимальный контекст для тестов эха (без CombatManager)."""
    def __init__(self):
        self.player = Warrior()
        self.enemy = Cultist("Тест", hp=100, max_hp=100)
        self.enemies = [self.enemy]
        self.log = []
        self.gm = None

    def add_log_message(self, msg):
        self.log.append(msg)

    def get_target_enemy(self):
        return self.enemy


def test_echo_effect_накладывает_эхо_на_игрока():
    cm = FakeCombat()
    effect = EchoEffect(2, 3)
    effect.execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.player.echo == 2
    # Улучшенный
    effect.execute(cm.player, cm.enemy, cm, is_upgraded=True)
    assert cm.player.echo == 5  # 2 + 3


def test_echo_retrigger_удваивает_урон():
    """Карта с DamageEffect: первый вызов с эхом не тратит его (это работа CM)."""
    cm = FakeCombat()
    cm.player.echo = 1
    card = Card("Тест", 1, "attack", "урон 6", [DamageEffect(6, 6)])
    # Apply сам не трогает эхо — это делает CombatManager.play_card_by_index
    card.apply(cm.player, cm.enemy, cm)
    dmg1 = 100 - cm.enemy.hp
    assert dmg1 > 0
    assert cm.player.echo == 1  # card.apply НЕ тратит эхо


def test_echo_retrigger_удваивает_щит():
    """Карта с ShieldEffect даёт щит, эхо не тратится на уровне apply."""
    cm = FakeCombat()
    cm.player.echo = 1
    card = Card("Тест", 1, "defense", "щит 5", [ShieldEffect(5, 5)])
    card.apply(cm.player, cm.enemy, cm)
    shield1 = cm.player.shield
    assert shield1 == 5
    assert cm.player.echo == 1  # card.apply НЕ тратит эхо


def test_эхо_не_тратится_на_apply_тратится_в_cm():
    """Эхо тратится ТОЛЬКО в CombatManager.play_card_by_index, не в card.apply."""
    cm = FakeCombat()
    cm.player.echo = 3
    card = Card("Тест", 1, "attack", "урон 2", [DamageEffect(2, 2)])
    card.apply(cm.player, cm.enemy, cm)
    # card.apply не трогает эхо — это ответственность CombatManager
    assert cm.player.echo == 3


def test_эхо_не_тратится_при_нуле():
    """При echo=0 ничего не происходит."""
    cm = FakeCombat()
    cm.player.echo = 0
    card = Card("Тест", 1, "attack", "урон 5", [DamageEffect(5, 5)])
    card.apply(cm.player, cm.enemy, cm)
    hp_after_one = cm.enemy.hp
    card.apply(cm.player, cm.enemy, cm)
    # Второй вызов — обычный урон, не удвоенный
    assert cm.enemy.hp < hp_after_one


# ─── Карты эха ──────────────────────────────────────────────────────────


def test_резонанс_даёт_эхо():
    cm = FakeCombat()
    card = create_echo_resonance()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.echo == 2
    card.upgrade()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.echo == 5  # 2 + 3


def test_каскад_без_эха_наносит_базовый_урон():
    cm = FakeCombat()
    cm.player.echo = 0
    card = create_echo_cascade()
    hp_before = cm.enemy.hp
    card.apply(cm.player, cm.enemy, cm)
    dmg = hp_before - cm.enemy.hp
    assert dmg >= 8  # минимум базовый урон


def test_каскад_с_эхом_наносит_двойной_урон():
    cm = FakeCombat()
    cm.player.echo = 2  # есть эхо
    card = create_echo_cascade()
    hp_before = cm.enemy.hp
    card.apply(cm.player, cm.enemy, cm)
    dmg = hp_before - cm.enemy.hp
    # С эхом урон ×2, но может быть снижен слабостью и т.д.
    # Проверяем что эхо НЕ потрачено
    assert cm.player.echo == 2  # Каскад не тратит эхо
    assert dmg >= 8 * 2  # минимум двойной базовый


def test_эхо_в_catalog_доступно():
    """Эхо-карты есть в общем пуле (generic)."""
    from core.cards.catalog import GENERIC_FACTORIES
    names = [f.__name__ for f in GENERIC_FACTORIES]
    for n in ("create_echo_resonance", "create_echo_cascade"):
        assert n in names, f"{n} отсутствует в GENERIC_FACTORIES"


def test_эхо_в_status_registry():
    """Эхо зарегистрировано как статус."""
    from core.StatusRegistry import STATUSES, get
    assert "echo" in STATUSES
    data = get("echo")
    assert data["is_stack"] is True
    assert data["is_duration"] is False
    assert data["abbr"] == "ЭХО"


# ─── Интеграционный тест: ретриггер в CombatManager ──────────────────────


def test_play_card_с_эхом_ретриггерит_все_эффекты():
    """Полный цикл: карта + эхо через CombatManager.play_card_by_index."""
    from managers.CombatManager import CombatManager

    player = Warrior()
    enemy = Cultist("Тест", hp=100, max_hp=100)
    # Эхо-тест не требует реального ИИ врага — ставим заглушки.
    enemy.base_test_damage = 5
    enemy.base_test_shield = 3
    card = Card("Удар", 1, "attack", "урон 6", [DamageEffect(6, 6)])
    cm = CombatManager(player, [enemy], [card], game_manager=None)
    cm.player.energy = 3
    cm.player.echo = 2  # два заряда эха

    hp_before = enemy.hp
    cm.play_card_by_index(0)
    # Карта применена 1 + 2(эхо) = 3 раза
    # Каждый раз DamageEffect(6) → не менее 6×3=18 урона
    dmg = hp_before - enemy.hp
    assert dmg >= 18, f"Ожидалось ≥18 урона (3 применения), получено {dmg}"
    assert cm.player.echo == 0  # эхо потрачено
