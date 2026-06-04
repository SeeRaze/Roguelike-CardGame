# managers/balance/runner.py
# Симуляция СКВОЗНОГО забега: бот идёт этаж за этажом одной колодой,
# HP переносится между боями, костры лечат, колода РАСТЁТ (карты-награды).
# Использует РЕАЛЬНУЮ сборку врагов (EnemySpawner) — чтобы мерить настоящие
# формулы сложности.
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


def _maybe_reward_card(deck: list, class_name: str) -> None:
    """С вероятностью _CARD_REWARD_CHANCE добавить в колоду случайную карту
    из пула класса (generic + классовые). Удаление/апгрейд не моделируем."""
    if random.random() < _CARD_REWARD_CHANCE:
        pool = get_pool_for_class(class_name)
        deck.append(random.choice(pool)())


class _StubGM:
    """Минимальный игровой контекст для боя вне UI.
    CombatManager читает gm.stats / gm.relics / gm.current_floor."""

    def __init__(self):
        self.relics        = []
        self.current_floor = 1
        self.current_state = "COMBAT"
        self.stats = {
            "monsters_killed":  0,
            "bosses_killed":    0,
            "max_damage_dealt": 0,
            "max_floor":        1,
        }


def run_single_run(player_class, max_floor: int = 100) -> dict:
    """Один забег: бот идёт floor=1..max_floor одной колодой.

    Возвращает {'death_floor': int|None, 'hp_by_floor': {floor: %hp}}.
    death_floor=None означает, что бот дошёл до max_floor живым.
    """
    player     = player_class()
    deck       = player.get_starter_deck()
    class_name = player_class.__name__
    gm         = _StubGM()

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

        # Прогрессия колоды: карта-награда за бой.
        _maybe_reward_card(deck, class_name)

        # Костёр на предбоссовом этаже: частичное лечение.
        if local_step == FLOORS_PER_ACT - 1:
            heal = int(player.max_hp * _CAMPFIRE_HEAL)
            player.hp = min(player.max_hp, player.hp + heal)

    return {"death_floor": None, "hp_by_floor": hp_by_floor}
