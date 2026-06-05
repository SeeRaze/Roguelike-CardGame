# managers/BalanceSimulator.py
# Тонкий фасад балансировщика. Логика — в пакете managers/balance/.
# Модель: СКВОЗНОЙ забег (бот идёт этаж за этажом одной колодой, HP
# переносится, костры лечат) на РЕАЛЬНЫХ формулах врагов (EnemySpawner).
#
# ДВЕ МЕТРИКИ (двойная экспонента, см. balance-curve-framework):
#   • wall    — случайный драфт: «базовая стена» без билда (одна кривая на всех).
#   • ceiling — собранный билд (ядро+жадный драфт+реликвии): «потолок» класса.
#   Зазор стена↔потолок = всё пространство геймплея.
#
# Запуск:  python -m managers.BalanceSimulator
import builtins

from core.players import Warrior, Rogue, Mage, Druid, Berserker, Summoner
from managers.balance import (
    run_single_run, get_ceiling_build, summarize, format_dual_report,
    EconomyPolicy,
)

ALL_CLASSES = [Warrior, Rogue, Mage, Druid, Berserker, Summoner]


def _silently(fn, *args, **kwargs):
    """Прогнать fn с заглушённым боевым print."""
    _print = builtins.print
    builtins.print = lambda *a, **kw: None
    try:
        return fn(*args, **kwargs)
    finally:
        builtins.print = _print


def run_dual(player_class, number_of_runs=200, max_floor=100, *, economy=None):
    """Прогнать обе метрики (wall + ceiling) и напечатать сравнительный отчёт.

    economy — EconomyPolicy (золото+прореживание, шаг №6) или None. Вливается в
    ОБЕ метрики: прореживание ускоряет сборку и стены, и потолка."""
    name = player_class.__name__

    def _wall():
        return [run_single_run(player_class, max_floor, economy=economy)
                for _ in range(number_of_runs)]

    def _ceiling():
        draft, extra, relics = get_ceiling_build(name)
        return [run_single_run(player_class, max_floor,
                               draft=draft, extra_cards=extra, relics=relics,
                               economy=economy)
                for _ in range(number_of_runs)]

    wall_stats    = summarize(_silently(_wall), max_floor)
    ceiling_stats = summarize(_silently(_ceiling), max_floor)
    print(format_dual_report(name, wall_stats, ceiling_stats))
    return wall_stats, ceiling_stats


if __name__ == "__main__":
    economy = EconomyPolicy()      # золото + прореживание (шаг №6 фреймворка)
    for cls in ALL_CLASSES:
        run_dual(cls, number_of_runs=200, max_floor=100, economy=economy)
