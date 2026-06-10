# tests/test_reaction_order.py
# Единый порядок-приоритет боевых реакций (ревизия ядра, пункт 2).
# R0: чистая таблица приоритетов + детерминированная сортировка реестров.
from core.ReactionOrder import ReactionPriority, order_keyed


# ═══════════════════════════════════════════════════════════
# R0 — таблица приоритетов
# ═══════════════════════════════════════════════════════════

def test_приоритеты_строго_возрастают_в_порядке_цепочки():
    # Комбо раньше детонаций, детонации раньше эха, эхо раньше тиков статусов,
    # тики раньше хуков реликвий/врагов — порядок розыгрыша карты → фазы врага.
    assert ReactionPriority.COMBO < ReactionPriority.FORGE_TAG
    assert ReactionPriority.FORGE_TAG < ReactionPriority.DETONATION
    assert ReactionPriority.DETONATION < ReactionPriority.ECHO
    assert ReactionPriority.ECHO < ReactionPriority.STATUS_TICK
    assert ReactionPriority.STATUS_TICK < ReactionPriority.RELIC_HOOK
    assert ReactionPriority.RELIC_HOOK < ReactionPriority.ENEMY_HOOK


def test_приоритеты_уникальны():
    values = [p.value for p in ReactionPriority]
    assert len(values) == len(set(values))


def test_приоритет_это_int():
    # IntEnum → можно сравнивать и сортировать как числа без .value.
    assert ReactionPriority.COMBO == 10
    assert int(ReactionPriority.DETONATION) == 40


# ═══════════════════════════════════════════════════════════
# R0 — детерминированная сортировка реестров
# ═══════════════════════════════════════════════════════════

def test_order_keyed_сортирует_по_имени_при_общем_приоритете():
    # Однородное семейство (один приоритет) → стабильный алфавит по ключу,
    # независимо от порядка вставки в dict.
    records = {"z": {"v": 1}, "a": {"v": 2}, "m": {"v": 3}}
    keys = [k for k, _ in order_keyed(records, ReactionPriority.DETONATION)]
    assert keys == ["a", "m", "z"]


def test_order_keyed_стабилен_независимо_от_порядка_вставки():
    r1 = {"electro_blast": {}, "lava": {}, "acid": {}}
    r2 = {"acid": {}, "electro_blast": {}, "lava": {}}
    assert order_keyed(r1, ReactionPriority.DETONATION) and True
    assert [k for k, _ in order_keyed(r1, ReactionPriority.DETONATION)] == \
           [k for k, _ in order_keyed(r2, ReactionPriority.DETONATION)]


def test_order_keyed_принимает_функцию_приоритета():
    # Разнородные приоритеты на запись: сортируем по prio, затем по ключу.
    records = {
        "b": {"prio": 50},
        "a": {"prio": 10},
        "c": {"prio": 10},
    }
    keys = [k for k, _ in order_keyed(records, lambda rec: rec["prio"])]
    assert keys == ["a", "c", "b"]   # 10:a,c (алфавит) → 50:b


# ═══════════════════════════════════════════════════════════
# R1 — реестры завязаны на единый порядок
# ═══════════════════════════════════════════════════════════
# NB (С58): старые priority-тесты детонаций удалены — DetonationRegistry стал
# функцией-позвоночником detonate() без data-driven priority-dict. Покрытие
# детонаций — в test_detonations.py (спина + вкусы по со-элементу).


# ═══════════════════════════════════════════════════════════
# R5 — сквозной розыгрыш под единым порядком + гардом
# ═══════════════════════════════════════════════════════════

def _live_cm(enemy_hp=200):
    """Живой CombatManager: Воин vs Культист, минимальная колода."""
    from core.players import Warrior
    from core.enemies.cultist import Cultist
    from core.cards import create_strike, create_defend
    from managers.CombatManager import CombatManager
    deck = [create_strike(), create_strike(), create_defend()]
    return CombatManager(Warrior(), Cultist("Культист", enemy_hp, enemy_hp), deck)


def test_розыгрыш_с_эхо_и_комбо_размотает_гард_в_ноль():
    # Враг с wet+ignited (комбо ПАР ×3) + у игрока эхо: вся цепочка (apply→комбо→
    # эхо-ретриггеры) проходит без зацикливания, глубина гарда размотана в 0.
    cm = _live_cm()
    enemy = cm.enemies[0]
    enemy.wet = 5
    enemy.ignited = 5
    cm.player.echo = 2
    cm.player.energy = 99
    # найти атакующую карту в руке
    from core.cards.base import DamageEffect
    idx = next(i for i, c in enumerate(cm.deck_manager.hand)
               if any(isinstance(e, DamageEffect) for e in c.effects))
    hp_before = enemy.hp
    cm.play_card_by_index(idx, target=enemy)
    assert enemy.hp < hp_before                  # урон прошёл (комбо учтено)
    assert cm._trigger_guard.depth == 0          # гард полностью размотан


def test_post_хуки_получают_свежий_бюджет_после_эхо():
    # Даже если эхо «накопило» глубину, post-хуки стартуют с depth=0 (свой бюджет):
    # после полного розыгрыша глубина всегда 0, хуки не были обрезаны эхом.
    cm = _live_cm()
    enemy = cm.enemies[0]
    cm.player.echo = 3
    cm.player.energy = 99
    from core.cards.base import DamageEffect
    idx = next(i for i, c in enumerate(cm.deck_manager.hand)
               if any(isinstance(e, DamageEffect) for e in c.effects))
    cm.play_card_by_index(idx, target=enemy)
    assert cm._trigger_guard.depth == 0

