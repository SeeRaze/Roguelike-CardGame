# managers/balance/sweep.py
# СЕССИЯ 39.3 — КАЛИБРОВОЧНЫЙ СВИП «триединства экономики» против роста врага g.
#
# ЗАЧЕМ: Закалка +15%/15 FP математически ОТСТАЁТ от врага в актах 1-2 (обгоняет
# лишь к акту 3, впритык). Нужно автоматически найти точку (цена Закалки, сила %,
# проактивный порог, частота событий), где стохастическая экспонента MaxHP
# СОКРУШАЕТ урон врага (DMG_GROWTH=1.026), НЕ ломая раннюю стену (акт-скейл
# событий 5-15% защищает этажи 1-20).
#
# МОДЕЛЬ ЗАМЕРА:
#   • ceiling — идеальный билд + ВЕСЬ движок (forge + economy + events). «Потолок».
#   • wall    — случайный драфт, движок ВЫКЛ. «Базовая стена» (контроль).
#   Свип крутит ручки forge.TEMPER_* и частоту EventPolicy, мерит, флипает ли
#   потолок вглубь (медиана этажа смерти) при сохранной ранней стене.
#   Стохастика событий → варьируем seed по N прогонам (дисперсия = свинг живучести).
#
# ЗАПУСК:
#   python -m managers.balance.sweep                  # дефолт: Берсерк, краткий грид
#   python -m managers.balance.sweep --class Druid --n 30
#   python -m managers.balance.sweep --full           # все 6 классов (медленно)
import argparse
import contextlib
import os
import random
import statistics
import sys

from core.players import Warrior, Rogue, Mage, Druid, Berserker, Summoner
from managers.balance import events as events_mod
from managers.balance import forge as forge_mod   # noqa: F401 (бот-политика)
from core import forge as core_forge              # источник правды ручек ковки (мутируем ТУТ)
from managers.balance.builds import get_ceiling_build
from managers.balance.economy import EconomyPolicy
from managers.balance.events import EventPolicy
from managers.balance.forge import ForgePolicy
from managers.balance.runner import run_single_run

CLASSES = {c.__name__: c for c in
           (Warrior, Rogue, Mage, Druid, Berserker, Summoner)}

# ─── ГРИД СВИПА (оси калибровки триединства) ──────────────────────────────────
# Закалка зафиксирована около найденного оптимума (этап А: проактивный порог 0.6
# = лучший потолок; pct/cost — вторичны). Свип теперь крутит РЫЧАГИ ТРИЕДИНСТВА,
# которые были заперты на нейтрали: отдачу событий и заглушку-катализатор
# артефактов (запас под лейт-раскорм реликвиями, §3).
GRID_TEMPER_RATIO  = (0.8, 0.6)         # проактивный порог Закалки
GRID_TEMPER_PCT    = (0.20,)            # сила Закалки (% к max_hp)
GRID_TEMPER_COST   = (10,)              # цена Закалки (FP)
GRID_EVENTS        = (1, 2)             # EVENT-нод за акт
GRID_EVENT_REWARD  = (2.0, 3.0)         # множитель отдачи события («супер-рычаг»)
GRID_ARTIFACT_FP   = (1.0, 1.2)         # заглушка-катализатор FP-притока артефактов

# Порог «флипа» потолка: медиана этажа смерти, считающаяся прорывом в акт 3.
FLIP_TARGET_FLOOR = 60
# Ранняя стена цела, если доля доживших до эт.10 НЕ тривиальна (< этого порога).
EARLY_WALL_WR_MAX = 95.0


def _depths(player_class, n, seed0, *, ceiling, events_per_act):
    """N этажей смерти для конфигурации. ceiling=True → билд+движок; иначе wall.
    Боевой лог глушим (redirect_stdout), как в baseline."""
    name = player_class.__name__
    draft, extra, relics = (get_ceiling_build(name) if ceiling
                            else (None, None, None))
    out = []
    with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
        for i in range(n):
            random.seed(seed0 + i)
            kw = {}
            if ceiling:
                kw = dict(draft=draft, extra_cards=extra, relics=relics,
                          economy=EconomyPolicy(), forge=ForgePolicy(),
                          events=EventPolicy(events_per_act=events_per_act))
            r = run_single_run(player_class, 100, **kw)
            out.append(r["death_floor"] or 100)
    return out


def _winrates(depths, checkpoints=(10, 25, 50, 60, 75, 100)):
    n = len(depths)
    return {cp: sum(1 for d in depths if d > cp) / n * 100 for cp in checkpoints}


def run_sweep(class_names, n, seed0=1):
    """Прогнать грид по классам. Возвращает список dict-строк результата."""
    rows = []
    # Базовая стена (движок ВЫКЛ) — одна на класс, не зависит от ручек.
    wall = {name: statistics.median(
                _depths(CLASSES[name], n, seed0, ceiling=False, events_per_act=0))
            for name in class_names}

    for ratio in GRID_TEMPER_RATIO:
        for pct in GRID_TEMPER_PCT:
            for cost in GRID_TEMPER_COST:
                for ev in GRID_EVENTS:
                    for reward in GRID_EVENT_REWARD:
                        for afp in GRID_ARTIFACT_FP:
                            # Ручки читаются модулями в рантайме → мутируем globals.
                            core_forge.TEMPER_PROACTIVE_RATIO = ratio
                            core_forge.TEMPER_HP_PCT          = pct
                            core_forge.TEMPER_FP_COST         = cost
                            core_forge.ARTIFACT_FP_MULT       = afp
                            events_mod.EVENT_REWARD_MULT     = reward
                            for name in class_names:
                                d = _depths(CLASSES[name], n, seed0,
                                            ceiling=True, events_per_act=ev)
                                med = statistics.median(d)
                                wr = _winrates(d)
                                rows.append({
                                    "class": name, "ratio": ratio, "pct": pct,
                                    "cost": cost, "events": ev, "reward": reward,
                                    "afp": afp,
                                    "ceil_med": med, "ceil_min": min(d),
                                    "ceil_max": max(d),
                                    "stdev": statistics.pstdev(d),
                                    "wall_med": wall[name],
                                    "gap": med - wall[name],
                                    "wr10": wr[10], "wr60": wr[60],
                                    "wr100": wr[100],
                                })
    return rows


def _score(row):
    """Сорт-ключ «лучшего баланса»: глубокий потолок, но РАННЯЯ СТЕНА ЦЕЛА
    (штраф, если до эт.10 доживают почти все → акт 1 стал тривиальным)."""
    penalty = 0 if row["wr10"] < EARLY_WALL_WR_MAX else -1000
    return row["ceil_med"] + penalty


def format_table(rows):
    rows = sorted(rows, key=_score, reverse=True)
    lines = [
        "ratio ev rew afp | cls        ceilMed gap  wr10 wr60 wr100 stdev  флип",
        "-" * 80,
    ]
    for r in rows:
        flip = "ФЛИП" if r["ceil_med"] >= FLIP_TARGET_FLOOR else ""
        wall_ok = " " if r["wr10"] < EARLY_WALL_WR_MAX else "⚠ранняя"
        lines.append(
            f"{r['ratio']:.1f}   {r['events']}  {r['reward']:.1f} {r['afp']:.1f} | "
            f"{r['class']:<10} {r['ceil_med']:>5g}  {r['gap']:>+4g} "
            f"{r['wr10']:>4.0f} {r['wr60']:>4.0f} {r['wr100']:>4.0f} "
            f"{r['stdev']:>5.1f}  {flip}{wall_ok}"
        )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Калибровочный свип триединства (39.3)")
    ap.add_argument("--class", dest="cls", default="Berserker",
                    help="класс для свипа (по умолч. Berserker — стресс живучести)")
    ap.add_argument("--n", type=int, default=24, help="прогонов на конфигурацию")
    ap.add_argument("--full", action="store_true", help="все 6 классов (медленно)")
    args = ap.parse_args()

    names = list(CLASSES) if args.full else [args.cls]
    if not args.full and args.cls not in CLASSES:
        print(f"Неизвестный класс {args.cls!r}. Доступны: {', '.join(CLASSES)}")
        sys.exit(1)

    grid_size = (len(GRID_TEMPER_RATIO) * len(GRID_TEMPER_PCT)
                 * len(GRID_TEMPER_COST) * len(GRID_EVENTS)
                 * len(GRID_EVENT_REWARD) * len(GRID_ARTIFACT_FP))
    print(f"# Свип: классы={names}  N={args.n}  конфигов={grid_size} "
          f"(всего ~{grid_size * len(names) * args.n} прогонов)")
    print(f"# Цель флипа: ceilMed ≥ {FLIP_TARGET_FLOOR} (акт 3); "
          f"ранняя стена цела при wr10 < {EARLY_WALL_WR_MAX:.0f}%\n")

    rows = run_sweep(names, args.n)
    print(format_table(rows))


if __name__ == "__main__":
    main()
