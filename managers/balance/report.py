# managers/balance/report.py
# Агрегация результатов забегов в читаемый отчёт по балансу.
# Главная метрика — на каком этаже гибнет бот (кривая сложности).

# Контрольные этажи для замера win-rate «дошёл живым до N».
CHECKPOINTS = [10, 25, 50, 75, 100]


def _percentile(sorted_vals, pct):
    """Перцентиль (nearest-rank) по отсортированному списку."""
    if not sorted_vals:
        return 0
    k = max(0, min(len(sorted_vals) - 1,
                   int(round(pct / 100 * (len(sorted_vals) - 1)))))
    return sorted_vals[k]


def summarize(runs: list, max_floor: int = 100) -> dict:
    """Свести список результатов run_single_run в метрики."""
    n = len(runs)
    # Глубина забега: этаж смерти, либо max_floor (дошёл живым).
    depths = sorted((r["death_floor"] or max_floor) for r in runs)

    # Win-rate по чекпоинтам: доля забегов, переживших этаж N.
    winrates = {}
    for cp in CHECKPOINTS:
        survived = sum(1 for r in runs
                       if (r["death_floor"] is None or r["death_floor"] > cp))
        winrates[cp] = survived / n * 100 if n else 0

    # Средний %HP по этажам (только пока бот ещё жив на этаже).
    hp_sum:  dict = {}
    hp_cnt:  dict = {}
    for r in runs:
        for floor, hp in r["hp_by_floor"].items():
            hp_sum[floor] = hp_sum.get(floor, 0.0) + hp
            hp_cnt[floor] = hp_cnt.get(floor, 0) + 1
    avg_hp = {f: hp_sum[f] / hp_cnt[f] for f in sorted(hp_sum)}

    return {
        "runs":      n,
        "depth_min": depths[0],
        "depth_p25": _percentile(depths, 25),
        "depth_med": _percentile(depths, 50),
        "depth_p75": _percentile(depths, 75),
        "depth_max": depths[-1],
        "winrates":  winrates,
        "avg_hp":    avg_hp,
    }


def format_report(class_name: str, stats: dict, max_floor: int = 100) -> str:
    """Текстовый отчёт по одному классу."""
    lines = []
    lines.append(f"=== {class_name} × {stats['runs']} забегов ===")
    lines.append(
        f"  Глубина (этаж смерти): "
        f"min={stats['depth_min']}  p25={stats['depth_p25']}  "
        f"med={stats['depth_med']}  p75={stats['depth_p75']}  max={stats['depth_max']}"
    )
    wr = "  ".join(f"эт.{cp}: {stats['winrates'][cp]:.0f}%" for cp in CHECKPOINTS)
    lines.append(f"  Дошёл живым:  {wr}")

    # Кривая %HP — выборочно по контрольным этажам.
    hp = stats["avg_hp"]
    sample_floors = [f for f in (1, 5, 10, 20, 40, 60, 80, 100) if f in hp]
    hp_line = "  ".join(f"эт.{f}:{hp[f] * 100:.0f}%" for f in sample_floors)
    lines.append(f"  Ср. HP:       {hp_line}")
    lines.append("=" * 60)
    return "\n".join(lines)
