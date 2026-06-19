# core/achievements.py
# РЕЕСТР ачивок MVP (С70, Этап 3 мета-прогрессии) — 6 билд-форсёров под
# тройку яруса 1, плюс одна общая. Каждая выполненная ачивка ГРАНТИТ конкретный
# залоченный предмет в meta['unlocks'] + 50 Опыта. Анти-дубль через
# meta['achievements'] (id выполненных).
#
# Архитектура: AchievementDef = id + текст + грант + функция-предикат `check(facts)`.
# `_on_combat_finished` подписан на шину meta_events и при каждом бое прогоняет
# все ачивки, грантя выполненные. Идемпотентно — grant вернёт False на дубле.
#
# Грантовый id шарит namespace c casino_seen через meta['unlocks']:
# is_card_unlocked/is_relic_unlocked видят его автоматически. Это означает,
# что ACHIEVEMENT_GRANT_* в progression.py должны быть НЕпересекающимися с
# casino_pool_*() — иначе один и тот же предмет придёт обоими путями.
# Инвариант (assert при импорте progression.py) защищает.

from dataclasses import dataclass
from typing import Callable

from core import meta_currency, meta_events


@dataclass(frozen=True)
class AchievementDef:
    """Описание ачивки.

    check(facts: dict) -> bool — предикат над снапшотом боя `CombatFacts` (см.
    CombatManager.combat_facts). Должен быть ЧИСТОЙ функцией: не мутирует мету,
    не публикует событий. Грант — единая точка в _grant().
    """
    id: str
    title: str
    description: str
    grant_kind: str               # 'card' | 'relic'
    grant_id: str                 # id предмета (card_id или класс реликвии)
    check: Callable[[dict], bool]
    # Бонус Опыта за выполнение ачивки (поверх потока +10/+30/+50 за бой/босс/забег).
    xp_reward: int = 50


# ─── Предикаты (чистые функции над фактами боя) ───────────────────────────────

def _victory(facts) -> bool:
    return bool(facts.get("victory", False))


def _check_clean_review(facts) -> bool:
    """Чистый ревью: Тестировщик победил БЕЗ потери HP (и не на 1м этаже —
    первый этаж тривиален, не достижение)."""
    return (
        facts.get("player_class") == "Warrior"
        and _victory(facts)
        and facts.get("floor", 1) > 1
        and facts.get("hp_end", 0) >= facts.get("hp_start", 0)
    )


def _check_discipline_8(facts) -> bool:
    """Регламент соблюдён: Тестировщик удержал «Дисциплина» ≥ 8 в одном бою
    (выжил, не свалил билд)."""
    return (
        facts.get("player_class") == "Warrior"
        and _victory(facts)
        and facts.get("peak_discipline", 0) >= 8
    )


def _check_lucky_prompt_mastery(facts) -> bool:
    """Удачный промпт: Вайб-кодер сыграл «Удачный промпт» при «Мастерство ≥ 5»."""
    return (
        facts.get("player_class") == "Mage"
        and _victory(facts)
        and facts.get("lucky_prompt_high_mastery", False)
    )


def _check_big_boil(facts) -> bool:
    """Заплыв в проде: Вайб-кодер сыграл «Залить в прод» с уроном ≥ 60.

    MVP-упрощение: ловим «удар ≥60» через дельту gm.stats['max_damage_dealt']
    в момент розыгрыша карты. Не требует трекинга индивидуального урона карт."""
    return (
        facts.get("player_class") == "Mage"
        and _victory(facts)
        and facts.get("big_boil_hit", False)
    )


def _check_hp_debt_crunch(facts) -> bool:
    """Кранч окупился: Стажёр выжил в бою после провала HP в долг ≥ 20."""
    return (
        facts.get("player_class") == "Berserker"
        and _victory(facts)
        and facts.get("peak_hp_debt", 0) >= 20
    )


def _check_first_boss(facts) -> bool:
    """Первый деплой: победить босса (любого класса). Анти-дубль через
    meta['achievements'] — грант сработает один раз = на первом победном боссе."""
    return _victory(facts) and bool(facts.get("is_boss", False))


# ─── Контент гл.1 — карты-якоря (С71) ─────────────────────────────────────────
# Каждый предикат достижим на СТАРТОВЫХ инструментах (не требует залоченной карты,
# которую сам же открывает) — сигнал «ты готов к этому билду». Пороги — заглушки
# (калибровка после альфа-теста). Класс-агностичны (любой класс), кроме страховки
# Стажёра. Темы смежны архетипу карты-награды.

def _check_parallelism(facts) -> bool:
    """Параллелизм → Диспетчер задач (множитель Эхо ×2): сыграть ≥5 карт за один ход
    (показал темп, готов к множителю)."""
    return _victory(facts) and facts.get("peak_cards_per_turn", 0) >= 5


def _check_accumulated(facts) -> bool:
    """Накопилось → Контроль версий (удвоитель стихийных стаков): довести стак одной
    стихии на враге до ≥6 (есть что удваивать). Порог 6 — мягкий (не душит анлок)."""
    return _victory(facts) and facts.get("peak_element_stack", 0) >= 6


def _check_core_dump(facts) -> bool:
    """Дамп ядра → Дамп памяти (decomp-payoff): добить врага с активной
    Декомпиляцией (decomp на цели в момент смерти)."""
    return _victory(facts) and bool(facts.get("killed_with_decomp", False))


def _check_deja_vu(facts) -> bool:
    """Дежавю → Каскад (Эхо-payoff ×2): сыграть одну и ту же карту 3 раза ЗА ОДИН ХОД
    (форсит ретриггер/удешевление — путь к Эхо-билду)."""
    return _victory(facts) and facts.get("max_same_card_in_turn", 0) >= 3


def _check_bug_zoo(facts) -> bool:
    """Зоопарк багов → Технический регресс (радуга-payoff): держать ≥3 РАЗНЫЕ стихии
    на одной цели одновременно (готов к +урон-за-стихию)."""
    return _victory(facts) and facts.get("peak_distinct_elements", 0) >= 3


def _check_on_a_prayer(facts) -> bool:
    """На честном слове → Костыль на Проде (Стажёр-страховка): Стажёр победил бой с
    HP ≤ 5 (клатч — оценил бы страховку от смерти)."""
    return (
        facts.get("player_class") == "Berserker"
        and _victory(facts)
        and facts.get("hp_end", 999) <= 5
    )


# ─── Контент гл.1 — релик-якоря (С71, casino-heavy: лишь маркерные движки) ─────
# Релики = пассивные снежные комья → предикаты-ВЕХИ (дойти/одолеть), а не «покажи
# механику» как у карт. Переиспользуют существующие факты (floor, bosses_this_run).

def _check_career_growth(facts) -> bool:
    """Карьерный рост → Повышение грейда (+25% урон/босс): победить 2 боссов за
    ОДИН забег (показал, что доживаешь до снежного кома)."""
    return _victory(facts) and facts.get("bosses_this_run", 0) >= 2


def _check_marathoner(facts) -> bool:
    """Марафонец → Стрессоустойчивость (+15% HP/босс): дойти до этажа 20
    (выживаемость окупит HP-снежный ком). Порог — заглушка."""
    return _victory(facts) and facts.get("floor", 1) >= 20


# ─── Реестр 6 MVP ачивок ──────────────────────────────────────────────────────

ACHIEVEMENTS = (
    AchievementDef(
        id="clean_review",
        title="Чистый ревью",
        description="Тестировщик: выиграть бой без потери HP (не 1й этаж).",
        grant_kind="relic", grant_id="ДашбордМетрик",
        check=_check_clean_review,
    ),
    AchievementDef(
        id="discipline_8",
        title="Регламент соблюдён",
        description="Тестировщик: накопить «Дисциплина» ≥ 8 в одном бою.",
        grant_kind="card",  grant_id="steel_barricade",
        check=_check_discipline_8,
    ),
    AchievementDef(
        id="lucky_prompt_mastery",
        title="Удачный промпт",
        description="Вайб-кодер: сыграть «Удачный промпт» при Мастерство ≥ 5.",
        grant_kind="relic", grant_id="Автодополнение",
        check=_check_lucky_prompt_mastery,
    ),
    AchievementDef(
        id="big_boil",
        title="Заплыв в проде",
        description="Вайб-кодер: нанести «Залить в прод» ≥ 60 урона за один удар.",
        grant_kind="card",  grant_id="boil",
        check=_check_big_boil,
    ),
    AchievementDef(
        id="hp_debt_crunch",
        title="Кранч окупился",
        description="Стажёр: выжить с HP-долгом ≥ 20 в одном бою.",
        grant_kind="card",  grant_id="final_deploy",
        check=_check_hp_debt_crunch,
    ),
    AchievementDef(
        id="first_boss",
        title="Первый деплой",
        description="Победить первого босса.",
        grant_kind="relic", grant_id="ДеплойВПятницу",
        check=_check_first_boss,
    ),
    # ─── Контент гл.1 — карты-якоря (С71) ─────────────────────────────────────
    AchievementDef(
        id="parallelism",
        title="Параллелизм",
        description="Сыграть 5 карт за один ход.",
        grant_kind="card", grant_id="task_manager",
        check=_check_parallelism,
    ),
    AchievementDef(
        id="accumulated",
        title="Накопилось",
        description="Довести стак одной стихии на враге до 6.",
        grant_kind="card", grant_id="version_control",
        check=_check_accumulated,
    ),
    AchievementDef(
        id="core_dump",
        title="Дамп ядра",
        description="Добить врага с активной Декомпиляцией.",
        grant_kind="card", grant_id="memory_dump",
        check=_check_core_dump,
    ),
    AchievementDef(
        id="deja_vu",
        title="Дежавю",
        description="Сыграть одну и ту же карту 3 раза за один ход.",
        grant_kind="card", grant_id="echo_cascade",
        check=_check_deja_vu,
    ),
    AchievementDef(
        id="bug_zoo",
        title="Зоопарк багов",
        description="Держать 3 разные стихии на одной цели одновременно.",
        grant_kind="card", grant_id="tech_regression",
        check=_check_bug_zoo,
    ),
    AchievementDef(
        id="on_a_prayer",
        title="На честном слове",
        description="Стажёр: победить бой с HP ≤ 5.",
        grant_kind="card", grant_id="prod_crutch",
        check=_check_on_a_prayer,
    ),
    # ─── Контент гл.1 — релик-якоря (С71) ─────────────────────────────────────
    AchievementDef(
        id="career_growth",
        title="Карьерный рост",
        description="Победить 2 боссов за один забег.",
        grant_kind="relic", grant_id="ПовышениеГрейда",
        check=_check_career_growth,
    ),
    AchievementDef(
        id="marathoner",
        title="Марафонец",
        description="Дойти до этажа 20.",
        grant_kind="relic", grant_id="Стрессоустойчивость",
        check=_check_marathoner,
    ),
)

REGISTRY: dict = {a.id: a for a in ACHIEVEMENTS}


# ─── Грант ────────────────────────────────────────────────────────────────────

def _grant(meta, ach: AchievementDef) -> bool:
    """Выдать грант ачивки: запись в meta['achievements'] + grant_id в unlocks +
    бонус Опыта + публикация 'achievement_unlocked' для UI. Идемпотентно: дубль
    возвращает False, мета не мутируется."""
    if meta is None:
        return False
    done = meta.setdefault("achievements", [])
    if ach.id in done:
        return False
    done.append(ach.id)
    unlocks = meta.setdefault("unlocks", [])
    if ach.grant_id not in unlocks:
        unlocks.append(ach.grant_id)
    meta_currency.grant_xp(meta, ach.xp_reward)
    meta_events.publish("achievement_unlocked", ach_id=ach.id, ach=ach)
    return True


def check_all(meta, facts) -> list:
    """Прогнать все ачивки против снапшота боя; грантнуть выполненные.

    Возвращает список id ачивок, которые ИМЕННО СЕЙЧАС были выданы — UI
    использует это для всплывашек «Открыто!». При повторном бое с тем же
    условием список будет пуст (анти-дубль через meta['achievements'])."""
    if meta is None or facts is None:
        return []
    granted = []
    for ach in ACHIEVEMENTS:
        if ach.id in meta.get("achievements", []):
            continue
        if ach.check(facts):
            if _grant(meta, ach):
                granted.append(ach.id)
    return granted


# ─── Подписка на шину ─────────────────────────────────────────────────────────

def _on_combat_finished(facts=None, meta=None, **_extra) -> None:
    """Подписчик на event 'combat_finished'. Сигнатура keyword-only с дефолтами —
    устойчива к расширению payload в будущем. **_extra проглатывает доп. поля."""
    check_all(meta, facts)


_handlers_registered = False


def register_handlers() -> None:
    """Подключить подписчиков к шине meta_events. Идемпотентна: повторный вызов
    в той же сессии не задвоит подписку. Вызывается из GameManager.__init__ —
    sim/baseline не зовёт, ачивки в эталоне не срабатывают."""
    global _handlers_registered
    if _handlers_registered:
        return
    meta_events.subscribe("combat_finished", _on_combat_finished)
    _handlers_registered = True


def _reset_handlers_for_tests() -> None:
    """Только для тестов — позволяет переподписать после meta_events.clear()."""
    global _handlers_registered
    _handlers_registered = False
