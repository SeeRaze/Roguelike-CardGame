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
    CombatManager читает gm.stats / gm.relics / gm.current_floor."""

    def __init__(self, relics=None):
        self.relics        = relics if relics is not None else []
        self.current_floor = 1
        self.current_state = "COMBAT"
        self.stats = {
            "monsters_killed":  0,
            "bosses_killed":    0,
            "max_damage_dealt": 0,
            "max_floor":        1,
        }


def run_single_run(player_class, max_floor: int = 100, *,
                   draft=None, extra_cards=None, relics=None) -> dict:
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

        # Прогрессия колоды: карта-награда за бой (стратегия драфта).
        draft(deck, class_name)

        # Костёр на предбоссовом этаже: частичное лечение.
        if local_step == FLOORS_PER_ACT - 1:
            heal = int(player.max_hp * _CAMPFIRE_HEAL)
            player.hp = min(player.max_hp, player.hp + heal)

    return {"death_floor": None, "hp_by_floor": hp_by_floor}
