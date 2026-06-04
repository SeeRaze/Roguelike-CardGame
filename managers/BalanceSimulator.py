# managers/BalanceSimulator.py
# Тонкий фасад балансировщика. Логика — в пакете managers/balance/.
# Модель: СКВОЗНОЙ забег (бот идёт этаж за этажом одной колодой, HP
# переносится, костры лечат) на РЕАЛЬНЫХ формулах врагов (EnemySpawner).
#
# Запуск:  python -m managers.BalanceSimulator
import builtins

from core.players import Warrior, Rogue, Mage, Druid, Berserker, Summoner
from managers.balance import run_single_run, summarize, format_report

ALL_CLASSES = [Warrior, Rogue, Mage, Druid, Berserker, Summoner]


def run_simulation(player_class, number_of_runs=200, max_floor=100):
    """Прогнать N сквозных забегов класса. Возвращает stats (см. report.summarize)."""
    # Глушим шумный боевой print на время прогона.
    _print = builtins.print
    builtins.print = lambda *a, **kw: None
    try:
        runs = [run_single_run(player_class, max_floor)
                for _ in range(number_of_runs)]
    finally:
        builtins.print = _print

    stats = summarize(runs, max_floor)
    print(format_report(player_class.__name__, stats, max_floor))
    return stats


if __name__ == "__main__":
    for cls in ALL_CLASSES:
        run_simulation(cls, number_of_runs=200, max_floor=100)
