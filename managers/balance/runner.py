# managers/balance/runner.py
# Симуляция СКВОЗНОГО забега: бот идёт этаж за этажом одной колодой,
# HP переносится между боями, костры лечат, колода РАСТЁТ (карты-награды).
# Использует РЕАЛЬНУЮ сборку врагов (EnemySpawner) — чтобы мерить настоящие
# формулы сложности.
#
# Две метрики (см. balance-curve-framework / двойная экспонента):
#   • wall    — случайный драфт (random-награда). «Базовая стена» без билда.
#   • ceiling — ядро билда в стартовой колоде + жадный драфт + реликвии.
#               «Потолок» собранного билда. Задаётся через параметры
#               run_single_run (draft / extra_cards / relics); дефолты дают
#               ТОЧНО прежнее wall-поведение (регресс-нейтрально).
import random
from core.cards.catalog   import get_pool_for_class
from managers.EnemySpawner import build_enemy_group
from managers.MapGenerator import FLOORS_PER_ACT
from managers.balance.bot  import BotCombatManager

# Доля HP, восстанавливаемая на костре (предбоссовый этаж).
_CAMPFIRE_HEAL = 0.30
# Шанс добрать карту-награду из классового пула после выжитого боя
# (грубая модель прогрессии: бой/магазин/сундук дают карты по ходу забега).
_CARD_REWARD_CHANCE = 0.6

# Элитные бои (Этап B): на не-босс этажах с этого этажа и с этим шансом бой
# становится элитным (build_enemy_group(is_elite=True) → архетип из ELITE_REGISTRY
# + стат-множители элиты). Сид фиксируется в baseline.measure_class →
# детерминированно. ELITE_ROOM_CHANCE — калибровочная ручка (см. _balance_knobs).
# Реальный MapGenerator: вес ELITE=5/100; в раннере каждый этаж — бой, поэтому
# шанс на этаж задан явно (≈одна элита за пол-акта).
_ELITE_FROM_FLOOR  = 8
_ELITE_ROOM_CHANCE = 0.10


def default_draft(deck: list, class_name: str) -> None:
    """Драфт метрики WALL: с вероятностью _CARD_REWARD_CHANCE добавить в колоду
    СЛУЧАЙНУЮ карту из пула класса. Моделирует игрока без плана сборки —
    «базовая стена». Удаление/апгрейд не моделируем."""
    if random.random() < _CARD_REWARD_CHANCE:
        pool = get_pool_for_class(class_name)
        deck.append(random.choice(pool)())


class _StubGM:
    """Минимальный игровой контекст для боя вне UI.
    CombatManager читает gm.stats / gm.relics / gm.current_floor.
    Экономические поля (gold/keys/removal_count) — зеркало GameManager,
    нужны EconomyPolicy (шаг №6 фреймворка); в бою не используются."""

    def __init__(self, relics=None):
        self.relics        = relics if relics is not None else []
        self.current_floor = 1
        self.current_state = "COMBAT"
        # Слой «правок правил» (RuleStack): пустой = базовый забег (инертно для урона).
        # Ставки/парадоксы пушат сюда моды; EffectCalculator консультирует DAMAGE-scope.
        from core.rules import RuleStack
        self.rulestack     = RuleStack()
        # Экономика (зеркало GameManager). Дефолты совпадают с реальной игрой.
        self.player_gold   = 100
        self.player_keys   = 0
        self.removal_count = 0
        self.stats = {
            "monsters_killed":  0,
            "bosses_killed":    0,
            "max_damage_dealt": 0,
            "max_floor":        1,
        }

    def get_removal_price(self) -> int:
        """Цена удаления карты — точное зеркало GameManager.get_removal_price
        (растёт с этажом и числом прошлых удалений; Корона удваивает)."""
        base = (15 + self.current_floor * 2) + self.removal_count * 25
        if any(r.name == "Проклятая Корона" for r in self.relics):
            base *= 2
        return base


def run_single_run(player_class, max_floor: int = 100, *,
                   draft=None, extra_cards=None, relics=None, economy=None,
                   forge=None, events=None, stakes=None, debt=False) -> dict:
    """Один забег: бот идёт floor=1..max_floor одной колодой.

    Параметры билда (дефолты = метрика WALL, прежнее поведение):
      draft       — функция (deck, class_name) -> None, зовётся после каждого
                    выжитого боя (прогрессия колоды). По умолчанию default_draft
                    (случайная награда).
      extra_cards — список ФАБРИК карт, добавляемых в СТАРТОВУЮ колоду (ядро
                    билда для метрики ceiling). По умолчанию пусто.
      relics      — список ФАБРИК/классов реликвий; инстанцируются на забег и
                    кладутся в gm.relics (хуки реликвий работают в бою).
                    По умолчанию пусто.
      economy     — EconomyPolicy или None. Если задана: после боя начисляется
                    золото, раз в акт оно тратится на удаление слабых карт
                    (шаг №6 фреймворка). По умолчанию None → экономика выключена
                    (регресс-нейтрально, A/B «с/без» чист).
      forge       — ForgePolicy или None (Сессия 39, _upgrade_design.md). Если
                    задана: бот копит FP за бои, на костре прокачивает ядро билда
                    (линейный слой δ), боссы снимают кап уровня. По умолчанию
                    None → ковка выключена (регресс-нейтрально, baseline зелёный).
      events      — EventPolicy или None (Сессия 39.3, «скачки» триединства). Если
                    задана: на фикс. EVENT-этажах бот играет азартный %-размен
                    (стохастический приток MaxHP/FP по акт-скейлу). По умолчанию
                    None → события выключены (регресс-нейтрально, baseline зелёный).
      stakes      — список Ставок (core.rules.Stake или их id) или None. Если задан:
                    на старте забега активируются (RuleStack: моды + одноразовый
                    DECKBUILD — обрезка колоды / правка игрока). По умолчанию None →
                    стек пуст, регресс-нейтрально. Делает RuleStack сим-нативным.
      debt        — bool (Долговой движок §7). True → бот может уходить в долг по
                    энергии (овердрафт: power now → HP-гашение pay later). По
                    умолчанию False → флаг не ставится, бот играет как раньше
                    (регресс-нейтрально, baseline зелёный).

    Возвращает {'death_floor': int|None, 'hp_by_floor': {floor: %hp}}.
    death_floor=None означает, что бот дошёл до max_floor живым.
    """
    draft = draft or default_draft

    player     = player_class()
    class_name = player_class.__name__

    # Ядро билда — карты-фабрики в стартовую колоду (ceiling).
    for factory in (extra_cards or []):
        player.add_to_starter_deck(factory())
    deck = player.get_starter_deck()

    # Реликвии билда — свежие инстансы на забег (хранят состояние, напр. _applied).
    relic_objs = [r() for r in (relics or [])]
    gm = _StubGM(relics=relic_objs)

    # Ставки (RuleStack): пушим моды + одноразовый DECKBUILD (обрезка колоды / правка
    # игрока на старте). stakes=None → стек пуст → регресс-нейтрально (baseline зелёный).
    # Делает RuleStack симулятор-нативным: бот «надевает» правила → сим меряет
    # выживаемость сломанного рулсета (спека _rulestack_design.md §5).
    if stakes:
        from core.rules import STAKES
        gm.player       = player
        gm.current_deck = deck
        for st in stakes:
            (STAKES[st] if isinstance(st, str) else st).activate(gm)

    # Долговой движок (§7): овердрафт энергии. debt=False → флаг не ставится → бот
    # играет как раньше (регресс-нейтрально, baseline зелёный). debt=True → бот
    # уходит в долг (bot.py фильтр) → сим меряет «power now, pay later».
    if debt:
        player.energy_overdraft = True

    hp_by_floor: dict = {}

    for floor in range(1, max_floor + 1):
        gm.current_floor = floor
        local_step = (floor - 1) % FLOORS_PER_ACT + 1
        is_boss    = (local_step == FLOORS_PER_ACT)

        # Элитный бой (Этап B): не-босс этаж ≥ _ELITE_FROM_FLOOR, по шансу.
        # Архетипы-контры билдам видны симу — баланс мерит их сложность.
        is_elite_floor = (
            not is_boss
            and floor >= _ELITE_FROM_FLOOR
            and random.random() < _ELITE_ROOM_CHANCE
        )

        enemies = build_enemy_group(floor, is_elite=is_elite_floor)
        combat  = BotCombatManager(player, enemies, list(deck), game_manager=gm)
        survived = combat.run_bot_loop()

        hp_by_floor[floor] = max(0.0, player.hp / player.max_hp)

        if not survived or player.hp <= 0:
            return {"death_floor": floor, "hp_by_floor": hp_by_floor}

        # Персистентный слой по забегу: хук on_boss_defeated на босс-этажах
        # (20/40/60/80/100) — растущие реликвии копят компаунд по забегу.
        # Зеркалит GameManager.distribute_combat_rewards (предусловие boss-filter:
        # сим обязан видеть чекпойнты-ворота, иначе тюнинг вслепую).
        if is_boss:
            for relic in relic_objs:
                relic.on_boss_defeated(player, combat)
            # Ковка (Сессия 39): босс снимает кап уровня карт (увязка шкал §3).
            if forge is not None:
                forge.on_boss_defeated(player, floor)

        # Сброс боевых статусов между боями (как distribute_combat_rewards в игре):
        # внутрибоевые движки (barrier/mastery/echo) НЕ переносятся по забегу.
        player.reset_combat_statuses()

        # Экономика (шаг №6): начислить золото за бой (зеркало build_rewards).
        if economy is not None:
            economy.on_combat_won(gm, floor)

        # Ковка (Сессия 39): начислить FP за выжитый бой (+бонус за босса).
        if forge is not None:
            forge.on_combat_won(player, floor, is_boss=is_boss)
            # ПОСТ-БОСС ковка (каденция §3, _upgrade_design): сразу после босса
            # игрок распределяет накопленный банк FP, не дожидаясь костра, —
            # убирает мёртвую зону в 19 этажей. Кап только что поднят (выше) →
            # ковка достигает свежеоткрытого майлстоуна в тот же миг.
            if is_boss:
                forge.forge_between_acts(player, deck, class_name)

        # Прогрессия колоды: карта-награда за бой (стратегия драфта).
        draft(deck, class_name)

        # %-Событие (39.3, «скачки» триединства): на фикс. EVENT-этажах бот
        # играет азартный размен (стохастический приток MaxHP/FP по акт-скейлу).
        if events is not None:
            events.maybe_event(player, gm, floor, max_floor)

        # Костёр на предбоссовом этаже: частичное лечение + экономика акта.
        if local_step == FLOORS_PER_ACT - 1:
            # Сток выживаемости на костре (§3, С39.4): если урон следующего акта
            # угрожает, бот ЖЕРТВУЕТ FP — ТЕМА-ГЕЙТ по колоде выбирает движок:
            # офенс-колода точит урон (Заточка), оборонная копит Max HP (Закалка).
            # Решение ДО ковки — потраченные FP не уйдут в карты.
            if forge is not None:
                forge.invest_if_threatened(player, floor, deck, class_name)
            heal = int(player.max_hp * _CAMPFIRE_HEAL)
            player.hp = min(player.max_hp, player.hp + heal)
            # Раз в акт: потратить накопленное золото на прореживание колоды.
            if economy is not None:
                economy.between_acts(gm, deck, class_name)
            # Раз в акт: ковка ядра билда на накопленные FP (линейный слой δ).
            if forge is not None:
                forge.forge_between_acts(player, deck, class_name)

    return {"death_floor": None, "hp_by_floor": hp_by_floor}
