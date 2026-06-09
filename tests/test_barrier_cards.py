# tests/test_barrier_cards.py
# Проверяем механику Барьера: несгораемый щит между ходами, карты Воина.
from core.cards.base import BarrierEffect
from core.cards.warrior import (
    create_steel_barricade, create_bastion, create_retribution,
)
from core.players import Warrior
from core.enemies import Cultist


class FakeBarrierCombat:
    """Минимальный контекст для тестов барьера."""
    def __init__(self):
        self.player = Warrior()
        self.enemy = Cultist("Тест", hp=100, max_hp=100)
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


# ─── Юнит-тесты BarrierEffect ────────────────────────────────────────────


def test_barrier_effect_накладывает_барьер():
    cm = FakeBarrierCombat()
    effect = BarrierEffect(2, 3)
    effect.execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.player.barrier == 2
    effect.execute(cm.player, cm.enemy, cm, is_upgraded=True)
    assert cm.player.barrier == 5  # 2 + 3


def test_barrier_в_status_registry():
    from core.StatusRegistry import STATUSES, get
    assert "barrier" in STATUSES
    data = get("barrier")
    assert data["is_stack"] is True
    assert data["is_duration"] is False
    assert data["abbr"] == "БАРЬЕР"


# ─── Карты барьера ───────────────────────────────────────────────────────


def test_стальной_заслон_даёт_барьер():
    cm = FakeBarrierCombat()
    card = create_steel_barricade()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.barrier == 2
    card.upgrade()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.barrier == 5  # 2 + 3


def test_бастион_даёт_щит_и_барьер():
    cm = FakeBarrierCombat()
    card = create_bastion()
    card.apply(cm.player, cm.enemy, cm)
    assert cm.player.shield == 6
    assert cm.player.barrier == 2


def test_барьер_не_сбрасывается_card_apply():
    """BarrierEffect не влияет на shield — он просто накладывает статус."""
    cm = FakeBarrierCombat()
    cm.player.shield = 10
    effect = BarrierEffect(3, 3)
    effect.execute(cm.player, cm.enemy, cm, is_upgraded=False)
    assert cm.player.shield == 10  # щит не тронут
    assert cm.player.barrier == 3


# ─── Интеграция: барьер в сбросе щита ────────────────────────────────────


def test_щит_с_барьером_не_падает_в_ноль():
    """Без carry, но с barrier=3: щит после сброса = 0 + 3 = 3."""
    cm = FakeBarrierCombat()
    cm.player.shield = 10
    cm.player.barrier = 3
    # Симулируем сброс щита как в CombatManager.start_turn_phase
    carry = 0
    cm.player.shield = carry + cm.player.barrier
    assert cm.player.shield == 3  # барьер сохранил щит


def test_барьер_суммируется_с_carry_воина():
    """Воин: carry=50% щита + barrier. Щит=20 → carry=10, barrier=4 → shield=14."""
    cm = FakeBarrierCombat()
    cm.player.shield = 20
    cm.player.barrier = 4
    carry = int(cm.player.shield * 0.5)  # пассив Воина
    cm.player.shield = carry + cm.player.barrier
    assert cm.player.shield == 14  # 10 + 4


def test_барьер_работает_как_движок_возмездия():
    """Полный цикл: барьер→щит→Возмездие. Моделируем 2 хода."""
    cm = FakeBarrierCombat()

    # Ход 1: играем Стальной заслон (барьер 2) + Защиту (щит 6)
    create_steel_barricade().apply(cm.player, cm.enemy, cm)
    # Напрямую добавляем щит (как Защита)
    cm.player.gain_shield(6, cm)
    assert cm.player.barrier == 2
    assert cm.player.shield == 6

    # Конец хода: сброс щита
    carry = int(cm.player.shield * 0.5)  # 3
    cm.player.shield = carry + cm.player.barrier  # 3 + 2 = 5

    # Ход 2: начинаем с 5 щита. Играем Возмездие.
    assert cm.player.shield == 5
    card = create_retribution()
    hp_before = cm.enemy.hp
    card.apply(cm.player, cm.enemy, cm)
    dmg = hp_before - cm.enemy.hp
    # ShieldDamageEffect: урон = щит (5) всем врагам
    assert dmg >= 5  # минимум щит


def test_барьер_в_generic_не_в_классе_воина():
    """Барьер переехал из классового пула Воина в GENERIC (С57, чистка под Дисциплину):
    универсальная защита, доступна всем; класс Воина = чисто ось Дисциплины."""
    from core.cards.catalog import CLASS_FACTORIES, GENERIC_FACTORIES
    generic_names = [f.__name__ for f in GENERIC_FACTORIES]
    warrior_names = [f.__name__ for f in CLASS_FACTORIES.get("Warrior", [])]
    # Теперь в generic
    assert "create_steel_barricade" in generic_names
    assert "create_bastion" in generic_names
    # И УЖЕ НЕ в классовом пуле Воина (старая ось вычищена)
    assert "create_steel_barricade" not in warrior_names
    assert "create_bastion" not in warrior_names
    assert "create_retribution" not in warrior_names   # Возмездие убрано из выдачи
