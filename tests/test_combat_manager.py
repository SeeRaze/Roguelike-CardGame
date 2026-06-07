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

    # Патчим send_run_record чтобы не лезть в сеть (живёт в managers.combat.defeat, С49)
    with patch("managers.combat.defeat.send_run_record"):
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


def test_хук_on_turn_end_зовётся_в_конце_хода():
    """end_turn_phase дёргает relic.on_turn_end для всех реликвий (под гардом)."""
    from core.relics.base import Relic

    class _Spy(Relic):
        def __init__(self):
            super().__init__("Шпион", "тест")
            self.calls = 0
        def on_turn_end(self, cm):
            self.calls += 1
    spy = _Spy()
    cm = _make_cm(gm=SimpleNamespace(relics=[spy]))
    cm.end_turn_phase()
    assert spy.calls == 1
    assert cm._trigger_guard.depth == 0     # глубина размотана


# ═══════════════════════════════════════════════════════════
# Обработка смерти врага в МОМЕНТ убивающего действия (карта/способность)
# Регресс С43: _check_enemy_death жил только в end_turn_phase → победа картой
# теряла on_kill / счётчик / перенос стаи. Фикс: _process_enemy_deaths перед
# _check_victory в play_card_by_index.
# ═══════════════════════════════════════════════════════════

def _kill_with_card(cm):
    """Сыграть «Удар» (6 урона) по врагу с 1 HP — добить картой."""
    cm.player.energy = 3
    idx = next(i for i, c in enumerate(cm.deck_manager.hand)
               if c.name == "Удар")
    cm.enemies[0].hp = 1
    return cm.play_card_by_index(idx)


def test_on_kill_срабатывает_на_килле_картой_до_конца_хода():
    """ТрофейныйКлык (+1 Сила/килл) срабатывает в момент добивания картой,
    а не только в end_turn_phase."""
    from core.relics.advanced.damage import ТрофейныйКлык
    gm = SimpleNamespace(relics=[ТрофейныйКлык()])
    cm = _make_cm(gm=gm)
    strength_before = cm.player.strength
    _kill_with_card(cm)
    assert cm.player.strength == strength_before + 1
    assert cm.enemies[0]._death_processed is True


def test_берсерк_медальон_даёт_энергию_на_килле_картой():
    """БерсеркМедальон (+1 Энергия/килл) пополняет энергию в момент килла картой."""
    from core.relics.advanced.damage import БерсеркМедальон
    gm = SimpleNamespace(relics=[БерсеркМедальон()])
    cm = _make_cm(gm=gm)
    # Удар стоит 1 энергии; ставим 3 → после розыгрыша 2, +1 за килл = 3.
    energy_after_play = 2
    _kill_with_card(cm)
    assert cm.player.energy == energy_after_play + 1


def test_статистика_убийства_засчитана_на_килле_картой():
    """monsters_killed растёт в момент добивания картой."""
    gm = SimpleNamespace(stats={"monsters_killed": 0, "bosses_killed": 0})
    cm = _make_cm(gm=gm)
    _kill_with_card(cm)
    assert gm.stats["monsters_killed"] == 1
    assert gm.stats["bosses_killed"] == 0


def test_стая_переносится_при_добивании_последнего_врага_картой():
    """Призыватель: победа картой сохраняет живую стаю (карточный аналог
    теста персиста через end_turn_phase)."""
    summoner = Summoner()
    cm = CombatManager(summoner, Cultist("Культист", 30, 30),
                       _simple_deck())
    cm.allies.append(_make_wolf(summoner))
    _kill_with_card(cm)
    assert len(summoner.persistent_allies) == 1


def test_обработка_смерти_картой_идемпотентна():
    """Килл картой + последующий свип (end_turn_phase) не дублирует on_kill /
    статистику (_death_processed)."""
    from core.relics.advanced.damage import ТрофейныйКлык
    gm = SimpleNamespace(relics=[ТрофейныйКлык()],
                         stats={"monsters_killed": 0, "bosses_killed": 0})
    cm = _make_cm(gm=gm)
    _kill_with_card(cm)
    assert gm.stats["monsters_killed"] == 1
    strength_after_kill = cm.player.strength
    # Повторный свип; смерть уже обработана → no-op.
    cm._process_enemy_deaths()
    cm._check_enemy_death(cm.enemies[0])
    assert gm.stats["monsters_killed"] == 1
    assert cm.player.strength == strength_after_kill


def test_aoe_убивает_двух_врагов_оба_обработаны():
    """Свип _process_enemy_deaths обрабатывает смерть ВСЕХ врагов (AoE может
    добить нескольких за одно действие)."""
    gm = SimpleNamespace(stats={"monsters_killed": 0, "bosses_killed": 0})
    p = Warrior()
    cm = CombatManager(p, [Cultist("К1", 30, 30), Cultist("К2", 30, 30)],
                       _simple_deck(), game_manager=gm)
    cm.enemies[0].hp = 0
    cm.enemies[1].hp = 0
    cm._process_enemy_deaths()
    assert gm.stats["monsters_killed"] == 2
    assert all(e._death_processed for e in cm.enemies)


# ═══════════════════════════════════════════════════════════
# Очередь отложенных эффектов (§3) — живая врезка в бой
# ═══════════════════════════════════════════════════════════

def test_очередь_отложенных_заведена_и_инертна():
    """CombatManager даёт пустую очередь; tick в end_turn_phase no-op (baseline)."""
    cm = _make_cm()
    assert len(cm.delayed_queue) == 0
    cm._tick_delayed_effects()        # пустая → ничего не делает, не падает
    assert len(cm.delayed_queue) == 0


def test_tick_исполняет_созревшее_через_n_ходов():
    """Эффект «через 2 хода» молчит на первом тике, срабатывает на втором и получает
    сам CombatManager аргументом (контракт action(cm))."""
    cm = _make_cm()
    fired = []
    cm.delayed_queue.schedule(2, lambda c: fired.append(c), label="бомба")
    cm._tick_delayed_effects()
    assert fired == []                # ход 1 — ещё не созрел
    assert len(cm.delayed_queue) == 1
    cm._tick_delayed_effects()
    assert fired == [cm]              # ход 2 — сработал, получил cm
    assert len(cm.delayed_queue) == 0


def test_созревший_эффект_свип_смертей():
    """Отложенный эффект, добивший врага, обработан свипом (on_kill/статы/persist),
    а не оставлен «висеть» до фазы врага."""
    gm = SimpleNamespace(stats={"monsters_killed": 0, "bosses_killed": 0})
    enemy = Cultist("Цель", 30, 30)
    cm = _make_cm(enemy=enemy, gm=gm)
    cm.delayed_queue.schedule(1, lambda c: c.enemies[0].take_damage(999), label="мина")
    cm._tick_delayed_effects()
    assert enemy.hp <= 0
    assert enemy._death_processed is True
    assert gm.stats["monsters_killed"] == 1


def test_end_turn_phase_тикает_очередь():
    """Интеграция: tick реально вызывается из end_turn_phase (созревший «через 1»
    срабатывает в конце хода игрока)."""
    cm = _make_cm()
    fired = []
    cm.delayed_queue.schedule(1, lambda c: fired.append(True), label="конец хода")
    cm.end_turn_phase()
    assert fired == [True]
    assert len(cm.delayed_queue) == 0


# ═══════════════════════════════════════════════════════════
# Трупы на сетке (субстрат Некроманта) — врезка в смерть-путь
# ═══════════════════════════════════════════════════════════

def test_павший_враг_становится_трупом():
    """_check_enemy_death помечает павшего врага тегом [Corpse], сохраняя клетку."""
    from core.corpse import is_corpse
    gm = SimpleNamespace(stats={"monsters_killed": 0, "bosses_killed": 0})
    enemy = Cultist("Жертва", 30, 30)
    cm = _make_cm(enemy=enemy, gm=gm)
    rank0, line0 = enemy.rank, enemy.line
    enemy.hp = 0
    cm._process_enemy_deaths()
    assert is_corpse(enemy) is True
    assert enemy.rank == rank0 and enemy.line == line0   # координата цела
    assert cm.corpses == [enemy]                          # виден через cm.corpses


def test_живой_враг_не_труп():
    cm = _make_cm()                                       # Культист жив
    assert cm.corpses == []


def test_труп_не_мешает_победе():
    """Труп = мёртвый объект (hp<=0) → victory=all(hp<=0) срабатывает как раньше."""
    from core.corpse import is_corpse
    p = Warrior()
    cm = CombatManager(p, [Cultist("К1", 30, 30), Cultist("К2", 30, 30)],
                       _simple_deck())
    for e in cm.enemies:
        e.hp = 0
    cm._process_enemy_deaths()
    assert all(is_corpse(e) for e in cm.enemies)          # оба — трупы
    assert all(e.hp <= 0 for e in cm.enemies)             # victory-инвариант цел
