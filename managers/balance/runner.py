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
                   forge=None) -> dict:
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

    hp_by_floor: dict = {}

    for floor in range(1, max_floor + 1):
        gm.current_floor = floor
        local_step = (floor - 1) % FLOORS_PER_ACT + 1

        enemies = build_enemy_group(floor, is_elite=False)
        combat  = BotCombatManager(player, enemies, list(deck), game_manager=gm)
        survived = combat.run_bot_loop()

        hp_by_floor[floor] = max(0.0, player.hp / player.max_hp)

        if not survived or player.hp <= 0:
            return {"death_floor": floor, "hp_by_floor": hp_by_floor}

        is_boss = (local_step == FLOORS_PER_ACT)

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

        # Прогрессия колоды: карта-награда за бой (стратегия драфта).
        draft(deck, class_name)

        # Костёр на предбоссовом этаже: частичное лечение + экономика акта.
        if local_step == FLOORS_PER_ACT - 1:
            heal = int(player.max_hp * _CAMPFIRE_HEAL)
            player.hp = min(player.max_hp, player.hp + heal)
            # Раз в акт: потратить накопленное золото на прореживание колоды.
            if economy is not None:
                economy.between_acts(gm, deck, class_name)
            # Раз в акт: ковка ядра билда на накопленные FP (линейный слой δ).
            if forge is not None:
                forge.forge_between_acts(player, deck, class_name)

    return {"death_floor": None, "hp_by_floor": hp_by_floor}
