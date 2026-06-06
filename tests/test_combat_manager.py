# tests/test_combat_manager.py
# Проверяем CombatManager — ядро боевого цикла:
# add_log_message, play_card_by_index, check_player_defeat,
# start_turn_phase (добор/энергия/Разбойник).
from unittest.mock import patch
from types import SimpleNamespace

from core.players import Warrior, Rogue, Summoner
from core.enemies.cultist import Cultist
from core.cards import create_strike, create_defend
from core.relics import ПроклятаяКорона
from managers.CombatManager import CombatManager


# ═══════════════════════════════════════════════════════════
# Помощники
# ═══════════════════════════════════════════════════════════

def _simple_deck():
    """Минимальная колода для тестов: 2 удара + 1 защита."""
    return [create_strike(), create_strike(), create_defend()]


def _make_cm(player=None, enemy=None, deck=None, gm=None):
    """Создать CombatManager с минимальными зависимостями.
    По умолчанию: Воин vs Культист, колода из 3 базовых карт."""
    p = player if player is not None else Warrior()
    e = enemy  if enemy  is not None else Cultist("Культист", 30, 30)
    d = deck   if deck   is not None else _simple_deck()
    if enemy is not None and player is None:
        # Если врага передали, а игрока нет — не форсируем Воина
        pass
    return CombatManager(p, e, d, game_manager=gm)


# ═══════════════════════════════════════════════════════════
# add_log_message
# ═══════════════════════════════════════════════════════════

def test_лог_пополняется_сообщением():
    cm = _make_cm()
    initial = len(cm.combat_log)
    cm.add_log_message("Тестовое сообщение")
    assert len(cm.combat_log) == initial + 1
    assert "Тестовое сообщение" in cm.combat_log


def test_лог_ограничен_шестью_сообщениями():
    cm = _make_cm()
    for i in range(10):
        cm.add_log_message(f"Сообщение {i}")
    assert len(cm.combat_log) == 6
    assert "Сообщение 9" in cm.combat_log
    assert "Сообщение 0" not in cm.combat_log  # самое старое ушло


# ═══════════════════════════════════════════════════════════
# play_card_by_index
# ═══════════════════════════════════════════════════════════

def test_розыгрыш_по_невалидному_индексу_возвращает_false():
    cm = _make_cm()
    assert cm.play_card_by_index(-1) is False
    assert cm.play_card_by_index(99) is False


def test_розыгрыш_без_энергии_возвращает_false():
    cm = _make_cm()
    cm.player.energy = 0
    result = cm.play_card_by_index(0)
    assert result is False


def test_розыгрыш_тратит_энергию_и_убирает_карту_из_руки():
    cm = _make_cm()
    cm.player.energy = 3
    hand_before = len(cm.deck_manager.hand)
    energy_before = cm.player.energy
    result = cm.play_card_by_index(0)
    assert result is True
    assert cm.player.energy == energy_before - 1
    assert len(cm.deck_manager.hand) == hand_before - 1


def test_розыгрыш_изгоняемой_карты_попадает_в_изгнание():
    """Карта с exile=True уходит в exile_pile, а не в discard."""
    from core.cards.base import Card, DamageEffect
    exile_card = Card("Изгнанник", 1, "attack", "...",
                       [DamageEffect(3, 5)], exile=True)
    deck = [exile_card, create_strike()]
    cm = _make_cm(deck=deck)
    cm.player.energy = 3
    # Найти индекс exile-карты в руке
    idx = next(i for i, c in enumerate(cm.deck_manager.hand)
               if getattr(c, 'exile', False))
    cm.play_card_by_index(idx)
    assert len(cm.deck_manager.exile_pile) == 1
    assert cm.deck_manager.exile_pile[0].name == "Изгнанник"


def test_розыгрыш_не_падает_с_реликвией():
    """Реликвия с on_card_played не мешает розыгрышу."""
    gm = SimpleNamespace(relics=[ПроклятаяКорона()])
    cm = _make_cm(gm=gm)
    cm.player.energy = 3
    result = cm.play_card_by_index(0)
    assert result is True


# ═══════════════════════════════════════════════════════════
# start_turn_phase — добор, энергия, Разбойник
# ═══════════════════════════════════════════════════════════

def test_начало_хода_восстанавливает_энергию():
    cm = _make_cm()
    cm.player.energy = 1
    cm.start_turn_phase()
    assert cm.player.energy == cm.player.max_energy


def test_начало_хода_добирает_карты():
    """После сброса руки start_turn_phase добирает карты из колоды."""
    cm = _make_cm()
    cm.deck_manager.discard_hand()
    assert len(cm.deck_manager.hand) == 0
    cm.start_turn_phase()
    # В колоде 3 карты — все должны оказаться в руке
    assert len(cm.deck_manager.hand) == 3


def test_разбойник_получает_скидку_на_случайную_карту():
    """В начале хода Разбойника одной карте снижается стоимость на 1."""
    rogue = Rogue()
    enemy = Cultist("Культист", 30, 30)
    cm = CombatManager(rogue, enemy, _simple_deck())
    discounted = [c for c in cm.deck_manager.hand
                  if getattr(c, 'temp_cost', None) is not None]
    assert len(discounted) == 1
    card = discounted[0]
    assert card.temp_cost == max(0, card.cost - 1)


# ═══════════════════════════════════════════════════════════
# check_player_defeat — смерть игрока
# ═══════════════════════════════════════════════════════════

def test_игрок_жив_возвращает_false():
    cm = _make_cm()
    cm.player.hp = 10
    assert cm.check_player_defeat() is False


def test_смерть_игрока_переводит_в_leaderboard():
    """При hp <= 0 игра заканчивается и переходит на экран рекордов."""
    gm = SimpleNamespace(
        current_floor=3,
        current_state="COMBAT",
        stats={"monsters_killed": 5, "bosses_killed": 0, "max_damage_dealt": 25},
    )
    cm = _make_cm(gm=gm)
    cm.player.hp = 0

    # Патчим send_run_record чтобы не лезть в сеть
    with patch("managers.CombatManager.send_run_record"):
        # Патчим LeaderboardView на уровне исходного модуля
        with patch("ui.LeaderboardView.LeaderboardView") as mock_lb:
            result = cm.check_player_defeat()

    assert result is True
    assert cm.player.hp == 0          # не уходит в минус
    assert gm.current_state == "LEADERBOARD"
    mock_lb.load_data.assert_called_once()


# ═══════════════════════════════════════════════════════════
# Персистентность стаи (Призыватель): союзники переживают бои
# ═══════════════════════════════════════════════════════════

def _make_wolf(player, hp=15, attack_power=5):
    from core.Summon import Summon
    return Summon(name="Волк", hp=hp, attack_power=attack_power, owner=player)


def test_выжившие_союзники_переносятся_в_следующий_бой():
    """При победе живые союзники сохраняются и восстанавливаются в новом бою."""
    summoner = Summoner()
    cm = CombatManager(summoner, Cultist("Культист", 1, 1), _simple_deck())
    cm.allies.append(_make_wolf(summoner))
    # Добиваем врага -> единая точка персиста в _check_enemy_death
    cm.enemies[0].hp = 0
    cm._check_enemy_death(cm.enemies[0])
    assert len(summoner.persistent_allies) == 1

    # Новый бой восстанавливает стаю
    cm2 = CombatManager(summoner, Cultist("Культист", 30, 30), _simple_deck())
    assert len(cm2.allies) == 1


def test_мёртвые_союзники_не_переносятся():
    """Павший в бою союзник не попадает в persistent_allies."""
    summoner = Summoner()
    cm = CombatManager(summoner, Cultist("Культист", 1, 1), _simple_deck())
    dead = _make_wolf(summoner)
    dead.hp = 0
    cm.allies.append(dead)
    cm.enemies[0].hp = 0
    cm._check_enemy_death(cm.enemies[0])
    assert summoner.persistent_allies == []


def test_перенос_стаи_ограничен_потолком():
    """Сохраняется не больше MAX_PERSISTENT_ALLIES — сильнейших по HP."""
    summoner = Summoner()
    cm = CombatManager(summoner, Cultist("Культист", 1, 1), _simple_deck())
    cap = CombatManager.MAX_PERSISTENT_ALLIES
    for hp in range(cap + 3):                 # заведомо больше потолка
        cm.allies.append(_make_wolf(summoner, hp=10 + hp))
    cm.enemies[0].hp = 0
    cm._check_enemy_death(cm.enemies[0])
    assert len(summoner.persistent_allies) == cap
    # Перенесены именно сильнейшие (наибольшие HP)
    carried_hp = sorted(a.hp for a in summoner.persistent_allies)
    assert min(carried_hp) > 10               # самые слабые отброшены


def test_восстановленный_союзник_теряет_щит_и_статусы():
    """Транзиентное состояние (щит/статусы) обнуляется при переносе в новый бой."""
    summoner = Summoner()
    cm = CombatManager(summoner, Cultist("Культист", 1, 1), _simple_deck())
    wolf = _make_wolf(summoner)
    wolf.shield = 9
    wolf.poison = 4
    cm.allies.append(wolf)
    cm.enemies[0].hp = 0
    cm._check_enemy_death(cm.enemies[0])

    cm2 = CombatManager(summoner, Cultist("Культист", 30, 30), _simple_deck())
    restored = cm2.allies[0]
    assert restored.shield == 0
    assert restored.poison == 0


# ═══════════════════════════════════════════════════════════
# Предохранитель глубины: _guarded (ревизия ядра, R2)
# ═══════════════════════════════════════════════════════════

def test_guarded_выполняет_функцию_и_возвращает_результат():
    cm = _make_cm()
    cm._trigger_guard.depth = 0
    out = cm._guarded("тест", lambda: 42)
    assert out == 42
    # depth восстановлен после выхода (finally guard.exit()).
    assert cm._trigger_guard.depth == 0


def test_guarded_обрывает_на_потолке_глубины():
    cm = _make_cm()
    # Искусственно «упираем» гард в потолок → следующий enter() = False.
    cm._trigger_guard.depth = cm._trigger_guard.max_depth
    called = []
    out = cm._guarded("тест", lambda: called.append(1))
    assert out is None
    assert called == []                       # fn НЕ вызвана — каскад оборван
    assert any("ПРЕДОХРАНИТЕЛЬ" in m for m in cm.combat_log)


def test_guarded_рекурсивный_хук_не_зацикливается():
    """Хук, который рекурсивно дёргает _guarded, гарантированно завершается на
    потолке глубины (а не уходит в бесконечность/переполнение)."""
    cm = _make_cm()
    cm._trigger_guard.depth = 0
    calls = {"n": 0}

    def recursive():
        calls["n"] += 1
        # Бесконечная по замыслу рекурсия — должна оборваться гардом.
        cm._guarded("рекурсия", recursive)

    cm._guarded("старт", recursive)
    # Ровно max_depth входов прошло, дальше enter() вернул False.
    assert calls["n"] == cm._trigger_guard.max_depth
    assert cm._trigger_guard.depth == 0       # стек полностью размотан


def test_фаза_врага_тикает_статусы_под_гардом_и_разматывает_глубину():
    """end_turn_phase проводит тики/намерения через _guarded_action — поведение
    идентично (горение наносит урон), а глубина гарда размотана в 0 после фазы."""
    cm = _make_cm()
    enemy = cm.enemies[0]
    enemy.statuses['ignited'] = 2             # горит → тик нанесёт урон
    hp_before = enemy.hp
    cm._trigger_guard.depth = 3               # искусственный «мусор» в гарде
    cm.end_turn_phase()
    assert enemy.hp < hp_before                # тик горения сработал
    # Каждое действие сбрасывает depth в 0 и разматывает — после фазы чисто.
    assert cm._trigger_guard.depth == 0


def test_guarded_action_сбрасывает_глубину_перед_вызовом():
    cm = _make_cm()
    cm._trigger_guard.depth = cm._trigger_guard.max_depth   # «упёрт» в потолок
    seen = {}
    cm._guarded_action("действие", lambda: seen.setdefault("depth_inside",
                                                            cm._trigger_guard.depth))
    # Несмотря на упор перед вызовом — сброс в 0, затем enter() → depth=1 внутри.
    assert seen["depth_inside"] == 1
    assert cm._trigger_guard.depth == 0
