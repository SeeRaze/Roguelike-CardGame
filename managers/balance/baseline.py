# managers/balance/baseline.py
# РЕГРЕСС-ГАРД БАЛАНСА — «шаблон точечной балансировки под новый контент».
#
# ЗАЧЕМ: симулятор умеет мерить силу класса (wall+ceiling), но раньше ничто не
# КРИЧАЛО, если новая карта/статус/реликвия обвалили класс («стена Друида с эт.26
# упала на эт.12»). Этот модуль пиннит медианы этажа смерти каждого класса к
# эталону BASELINE и краснеет при выходе за допуск.
#
# КАК ЧИТАТЬ ДОПУСК:
#   BASELINE_MAX_DROP — насколько класс может ПРОСЕСТЬ (этажей) до тревоги.
#                       Ловит регресс: контент случайно ослабил класс.
#   BASELINE_MAX_RISE — насколько может ВЫРАСТИ до тревоги. Ловит баг-всплеск
#                       (исторический пример: статусы не сбрасывались между боями
#                       → ложный «непобедимый» Воин). Шире, чем DROP: рост обычно
#                       легитимен (новая сильная карта), тревога — только на резкий.
#
# КАК ПЕРЕБЛАГОСЛОВИТЬ после ОСОЗНАННОГО изменения баланса:
#   python -m managers.balance.baseline
#       → печатает текущие медианы + дельты; скопируй блок BASELINE сюда.
#
# ЗАПУСК ГАРДА:
#   python -m managers.balance.baseline --check   (CI: plain-python, без pytest)
#   pytest -m balance                              (локально, через обёртку-тест)
import contextlib
import os
import random
import statistics
import sys

from core.players import Warrior, Rogue, Mage, Druid, Berserker, Summoner, Chemist
from managers.balance.builds import get_ceiling_build
from managers.balance.economy import EconomyPolicy
from managers.balance.forge import ForgePolicy
from managers.balance.runner import run_single_run

CLASSES = [Warrior, Rogue, Mage, Druid, Berserker, Summoner, Chemist]

# Параметры замера. Seed фиксирован → медиана детерминирована на неизменном коде.
# N=40 — компромисс стабильность медианы ↔ скорость (~15с на все 6 классов).
BASELINE_N    = 40
BASELINE_SEED = 99

# Допуски в этажах (см. шапку). DROP — узкий (ловим обвал), RISE — широкий.
BASELINE_MAX_DROP = 6
BASELINE_MAX_RISE = 12

# Эталонные медианы этажа смерти. wall = случайный драфт (базовая «стена»),
# ceiling = скриптовый идеальный билд (потолок). Экономика ВЫКЛ (каноничный замер).
# Элитные бои ВКЛ в runner (Этап B, шанс _ELITE_ROOM_CHANCE на этажах ≥8) —
# архетипы-контры билдам учитываются в сложности.
# Регенерация: python -m managers.balance.baseline
BASELINE = {
    "Warrior":   {"wall": 28,   "ceiling": 42},
    "Rogue":     {"wall": 15,   "ceiling": 19},
    "Mage":      {"wall": 18,   "ceiling": 28},
    "Druid":     {"wall": 20,   "ceiling": 28.5},
    "Berserker": {"wall": 9,    "ceiling": 13.5},
    "Summoner":  {"wall": 63,   "ceiling": 67},
    "Chemist":   {"wall": 20.5, "ceiling": 18.5},
}

# ── FORGE-ON ДВИЖОК (С50, доп. метрика тройки яруса 1) ─────────────────────────
# Метрики wall/ceiling выше — forge-OFF (каноничный замер). Для Берсерка («Ломай»,
# гласс-пушка) это СКРЫВАЕТ движок: его потолок живёт в ковке (|HP-долг|→FP→прокачка),
# а forge-off конверсия FP не делает ничего → ceiling-off выглядит слабым (структурно).
# Эта метрика мерит ДОХОДИМОСТЬ ceiling-билда с ВКЛ ковкой до FORGE_REACH_FLOOR (%):
#   • С57 (1d-pre): из ceiling-билдов убрана Проклятая Корона (×2 урон) — она почти в
#     одиночку протаскивала Воина за эт.50 (forge-reach 90→42%, Δ−48). Честные числа:
#     потолок теперь строится ЭКОНОМИКОЙ (ковка-теги/Закалка→золото/HP-ось), а не одной
#     сломанной легендаркой. Калибровка ceiling-билдов = капстоун (шаг 4 эконом-дуги).
#   • Воин ~42% / Маг ~65% долетают (Маг ниже до достройки HP-оси — HP-гамбл Разгона
#     просаживает доходимость, [[economy-axis-trinity]]).
#   • Берсерк = рисковый движок: ~8% забегов раскручивается (доказанная гласс-пушка,
#     не тильт — см. balance-findings-berserker-glasscannon). Медиана/p90 тут не годятся:
#     медиана прячет движок (мрёт рано), p90 упирается в кап у всех. Доля-доходимость =
#     единственный РАЗЛИЧАЮЩИЙ сигнал «как часто раскрученный билд долетает».
FORGE_REACH_FLOOR = 50
BASELINE_FORGE = {
    "Warrior":   42,
    "Mage":      65,
    "Berserker": 25,   # С57: %-ось долга + Кранч (сустейн-добивание) → движок чаще раскручивается
}
# Тревожит ТОЛЬКО просадка (движок ковки сломался); рост доходимости всегда легитимен.
# Допуск широкий: доля по N=40 шумна (каждый забег — бинарный 0/1 «долетел/нет»).
BASELINE_FORGE_MAX_DROP = 18

# ── СТАРТЕР-ЭТАЛОН (С57, шаг 2 капстоун-реордера) ─────────────────────────────
# Метрики BASELINE/BASELINE_FORGE выше — FULL-ACCESS (весь пул разлочен) = «потенциал
# класса ПОСЛЕ мета-прогрессии». Но день-1 игрок видит лишь УЗКИЙ стартовый пул
# ([[capstone-reorder-content-first]], узкий пул + анлоки): бо́льшая часть карт/реликвий
# заперта за достижениями/казино. Эта метрика мерит ЧЕСТНЫЙ опыт дня-1 — прогон с
# meta.unlocks=∅ → драфт и ручное ядро фильтруются по анлокам.
#
# ТОЛЬКО ТРОЙКА ЯРУСА 1 (Воин/Маг/Берсерк) — они играются с первого запуска, поэтому
# meta=∅ для них РЕАЛИСТИЧЕН. Тир-2 (Раз/Друид/Призыв/Химик) заперты до анлока класса,
# а к их разлочке игрок уже накопил анлоки карт → meta=∅ им нереалистичен (мерим их
# full-access выше). Зеркалит трио-only структуру BASELINE_FORGE.
#
# КОНТРАСТ starter↔full = «сколько силы класса заперто за мета-прогрессией»:
#   • Ядра потолка тройки опираются почти целиком на ЗАЛОЧЕННЫЕ реликвии-движки
#     (Воин 3/3, Маг/Берс 2/3) → стартер-потолок честно НИЖЕ full-потолка.
#   • Берсерк: ядро [battle_cry] заперто → стартер-ядро пусто → ceiling≈wall.
#     ⚠️ Берсерк всё равно меряется ботом КРИВО ([[balance-findings-berserker-autopsy]]):
#     greedy-бот истекает в акте 1 без сустейна → не привязывать калибровку к этой медиане.
# Регенерация: python -m managers.balance.baseline
STARTER_META = {"unlocks": []}
STARTER_CLASSES = (Warrior, Mage, Berserker)
BASELINE_STARTER = {
    # ВАЖНО (находка С57): стартер-числа местами ≥ full — НЕ баг. Узкий стартовый
    # пул меньше разбавляет колоду синергийными картами, которые бот не пилотирует
    # ([[balance-findings-shock-dilution]]), а залоченный контент = в основном
    # РЕЛИКВИИ → их теряет сильнее всех Воин (потолок 42→29, движок Дисциплины
    # живёт в залоченных реликвиях ЖелезнаяВоля/ШипастаяБроня/ЭнергоЯдро).
    "Warrior":   {"wall": 31, "ceiling": 29},
    "Mage":      {"wall": 18, "ceiling": 30.5},  # потолок ~не зависит от залоченного
    "Berserker": {"wall": 8.5, "ceiling": 9},    # +Кранч в стартдеке: день-1 сустейн
}


def _median_death(results: list) -> float:
    """Медиана этажа смерти; дошедшие до конца = max_floor (100)."""
    vals = [r["death_floor"] if r["death_floor"] is not None else 100 for r in results]
    return statistics.median(vals)


def measure_class(player_class) -> dict:
    """Медианы этажа смерти класса по обеим метрикам (детерминированно при
    BASELINE_SEED). Бой печатает в лог — глушим через redirect_stdout."""
    name = player_class.__name__

    def _run(**kw) -> float:
        random.seed(BASELINE_SEED)
        with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
            return _median_death(
                [run_single_run(player_class, 100, **kw) for _ in range(BASELINE_N)]
            )

    wall = _run()                                       # случайный драфт
    draft, extra, relics = get_ceiling_build(name)      # идеальный билд
    ceiling = _run(draft=draft, extra_cards=extra, relics=relics)
    return {"wall": wall, "ceiling": ceiling}


def measure_starter(player_class) -> dict:
    """Медианы этажа смерти в СТАРТЕР-режиме (meta=∅) — честный опыт дня-1.
    wall = случайный драфт из СТАРТОВОГО пула; ceiling = стартер-ядро (залоченные
    карты/реликвии отфильтрованы) + жадный драфт из стартового пула. Детерминирована
    при BASELINE_SEED. Контраст с full-access measure_class = вклад мета-прогрессии."""
    name = player_class.__name__

    def _run(**kw) -> float:
        random.seed(BASELINE_SEED)
        with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
            return _median_death(
                [run_single_run(player_class, 100, meta=STARTER_META, **kw)
                 for _ in range(BASELINE_N)]
            )

    wall = _run()                                                 # стартовый пул
    draft, extra, relics = get_ceiling_build(name, meta=STARTER_META)  # стартер-ядро
    ceiling = _run(draft=draft, extra_cards=extra, relics=relics)
    return {"wall": wall, "ceiling": ceiling}


def measure_forge_reach(player_class) -> int:
    """Доля (%) forge-ON ceiling-забегов класса, доживших до FORGE_REACH_FLOOR.
    Видимость движка ковки — forge-off метрики его не показывают (особенно у Берсерка).
    Детерминирована при BASELINE_SEED. None death_floor = дошёл до конца (≥ порога).

    С57: даём ПОЛНЫЙ движок (forge + economy) — Закалка переехала на ЗОЛОТО в
    EconomyPolicy ([[economy-axis-trinity]]), без economy метрика слепа к оборонной
    оси (Воин). Эмпирически до эт.50 Закалка маргинальна (её компаунд живёт в акте 3),
    поэтому числа не сдвинулись — но метрика теперь видит обе оси корректно."""
    name = player_class.__name__
    draft, extra, relics = get_ceiling_build(name)
    random.seed(BASELINE_SEED)
    with open(os.devnull, "w") as dn, contextlib.redirect_stdout(dn):
        results = [
            run_single_run(player_class, 100, draft=draft, extra_cards=extra,
                           relics=relics, forge=ForgePolicy(), economy=EconomyPolicy())
            for _ in range(BASELINE_N)
        ]
    reached = sum(
        1 for r in results
        if r["death_floor"] is None or r["death_floor"] >= FORGE_REACH_FLOOR
    )
    return round(100 * reached / BASELINE_N)


def check() -> list:
    """Сравнить текущие медианы с BASELINE. Вернуть список строк-нарушений
    (пустой = баланс в допуске). Общий движок для CLI `--check` и pytest-обёртки."""
    failures = []
    for cls in CLASSES:
        name = cls.__name__
        cur = measure_class(cls)
        base = BASELINE[name]
        for metric in ("wall", "ceiling"):
            diff = cur[metric] - base[metric]           # <0 просадка, >0 рост
            if diff < -BASELINE_MAX_DROP:
                failures.append(
                    f"{name} {metric}: ОБВАЛ {cur[metric]:g} vs эталон {base[metric]:g} "
                    f"(просадка {-diff:g} > допуск {BASELINE_MAX_DROP})")
            elif diff > BASELINE_MAX_RISE:
                failures.append(
                    f"{name} {metric}: ВСПЛЕСК {cur[metric]:g} vs эталон {base[metric]:g} "
                    f"(рост {diff:g} > допуск {BASELINE_MAX_RISE} — возможен баг)")

    # FORGE-ON движок (тройка яруса 1): тревожит только ОБВАЛ доходимости (движок сломан).
    by_name = {c.__name__: c for c in CLASSES}
    for name, base_reach in BASELINE_FORGE.items():
        cur_reach = measure_forge_reach(by_name[name])
        drop = base_reach - cur_reach
        if drop > BASELINE_FORGE_MAX_DROP:
            failures.append(
                f"{name} forge-reach{FORGE_REACH_FLOOR}: ОБВАЛ ДВИЖКА {cur_reach}% vs "
                f"эталон {base_reach}% (просадка {drop} > допуск {BASELINE_FORGE_MAX_DROP})")

    # СТАРТЕР-режим (тройка яруса 1): честный день-1. Допуск тот же, что у full-метрик
    # (DROP узкий — ловим обвал стартера контентом; RISE широкий — буст легитимен).
    for cls in STARTER_CLASSES:
        name = cls.__name__
        cur = measure_starter(cls)
        base = BASELINE_STARTER[name]
        for metric in ("wall", "ceiling"):
            diff = cur[metric] - base[metric]
            if diff < -BASELINE_MAX_DROP:
                failures.append(
                    f"{name} starter-{metric}: ОБВАЛ {cur[metric]:g} vs эталон "
                    f"{base[metric]:g} (просадка {-diff:g} > допуск {BASELINE_MAX_DROP})")
            elif diff > BASELINE_MAX_RISE:
                failures.append(
                    f"{name} starter-{metric}: ВСПЛЕСК {cur[metric]:g} vs эталон "
                    f"{base[metric]:g} (рост {diff:g} > допуск {BASELINE_MAX_RISE} — возможен баг)")
    return failures


def _regen() -> None:
    """Печать текущих медиан в формате BASELINE + дельты (для переблагословения)."""
    print(f"# Текущие медианы (N={BASELINE_N}, seed={BASELINE_SEED}):")
    print("BASELINE = {")
    for cls in CLASSES:
        name = cls.__name__
        cur = measure_class(cls)
        base = BASELINE.get(name, {})
        dw = cur["wall"]    - base.get("wall",    cur["wall"])
        dc = cur["ceiling"] - base.get("ceiling", cur["ceiling"])
        print(f'    "{name}": {{"wall": {cur["wall"]:g}, "ceiling": {cur["ceiling"]:g}}},'
              f'   # Δwall {dw:+g}, Δceil {dc:+g}')
    print("}")

    by_name = {c.__name__: c for c in CLASSES}
    print(f"\n# Forge-ON доходимость до эт.{FORGE_REACH_FLOOR} (%, движок ковки):")
    print("BASELINE_FORGE = {")
    for name in BASELINE_FORGE:
        cur = measure_forge_reach(by_name[name])
        base = BASELINE_FORGE.get(name, cur)
        print(f'    "{name}": {cur},   # Δ {cur - base:+g}')
    print("}")

    print("\n# Стартер-режим (meta=∅, честный день-1; тройка яруса 1):")
    print("BASELINE_STARTER = {")
    for cls in STARTER_CLASSES:
        name = cls.__name__
        cur = measure_starter(cls)
        base = BASELINE_STARTER.get(name, {})
        dw = cur["wall"]    - base.get("wall",    cur["wall"])
        dc = cur["ceiling"] - base.get("ceiling", cur["ceiling"])
        print(f'    "{name}": {{"wall": {cur["wall"]:g}, "ceiling": {cur["ceiling"]:g}}},'
              f'   # Δwall {dw:+g}, Δceil {dc:+g}')
    print("}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        fails = check()
        if fails:
            print("❌ РЕГРЕСС-ГАРД БАЛАНСА: ПРОВАЛ")
            for f in fails:
                print("  - " + f)
            print("\nЕсли изменение осознанное — переблагослови эталон:\n"
                  "    python -m managers.balance.baseline")
            sys.exit(1)
        print(f"✅ Регресс-гард баланса: все {len(CLASSES)} классов в допуске "
              f"(DROP≤{BASELINE_MAX_DROP}, RISE≤{BASELINE_MAX_RISE}); "
              f"+ forge-движок ({len(BASELINE_FORGE)}) + стартер-режим "
              f"({len(BASELINE_STARTER)}, день-1).")
    else:
        _regen()
