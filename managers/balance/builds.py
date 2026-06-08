# managers/balance/builds.py
# Метрика CEILING (см. balance-curve-framework — двойная экспонента).
# «Потолок» = собранный «сломанный» билд: ручное ЯДРО архетипа (ключевые карты +
# профильные реликвии) ПЛЮС жадный драфт (бот добирает не случайную, а лучшую по
# простой эвристике карту). Контрастирует с метрикой wall (случайный драфт):
# зазор стена↔потолок = всё пространство геймплея.
#
# Ядра НЕ обязаны быть идеально оттюнены — они задают «к чему игрок собирался».
# Это прокси верхней границы класса, а не точная модель лучшей игры.
import random

from core.cards import (
    create_retribution, create_iron_wall, create_steel_barricade, create_bastion,
    create_boil, create_arcane_focus, create_elemental_surge, create_ignite,
    create_splash, create_toxic_cloud, create_poison_stab, create_lacerate,
    create_open_wound, create_hemorrhage, create_battle_cry,
    create_bloodlust, create_serrated_edge,
    create_summon_wolf, create_summon_golem,
    create_virulent_strain,
)
from core.cards.base import (
    DamageEffect, ShieldEffect, StatusEffect, PoisonEffect,
    DetonateEffect, RegenEffect, HealEffect, BarrierEffect,
)
from core.cards.air import FlowEffect
from core.cards.summon import SummonEffect
from core.cards.warrior import ShieldDamageEffect
from core.cards.debuff.bleed import BleedEffect
from core.cards.echo import EchoEffect, EchoPayoffEffect
from core.cards.mage import MasteryEffect
from core.cards.rogue import FrenzyEffect
from core.cards.druid import VirulenceEffect
from core.cards.berserker import (
    DebtScalingDamageEffect, SelfHarmEffect, DebtToForgeOnKillEffect,
)
from core.relics import (
    ПроклятаяКорона, ЭнергоЯдро, ТочильныйКамень, ЖелезнаяВоля, ШипастаяБроня,
    ДревнееОгниво, ФлаконСЖелчью, СердцеТитана, ГнилойКлык, ОкровавленныйШприц,
    ТрофейныйКлык,
)

# Сколько кандидатов семплируется из пула при каждом жадном доборе (берётся
# лучший по эвристике). 1 = случайно (как wall); больше = «игрок выбирает».
_DRAFT_SAMPLE = 5
# Тот же шанс-добора, что у wall (default_draft) — чтобы размер колоды (а значит
# и стабильность добора ключевых карт) был сопоставим, и ceiling мерил КАЧЕСТВО
# выбора, а не объём. Импортируется лениво, чтобы не плодить связи.
_THEME_BONUS = 3.0   # надбавка кандидату за совпадение со «темой» колоды

# Профильные статусы и их «ценность» для эвристики драфта (масштабируемость).
_STATUS_VALUE = {
    "vulnerable": 4, "poison": 3, "shock": 3, "ignited": 3,
    "wet": 3, "shatter": 3, "bleed": 3, "weak": 2, "strength": 4,
}

# ─── Ядра билдов: фабрики карт в стартовую колоду + профильные реликвии ───────
# Каждое ядро = (extra_cards, relics). Архетип «к чему класс собирается».
CLASS_CORES = {
    "Warrior": (
        [create_retribution, create_iron_wall, create_steel_barricade,
         create_bastion, create_retribution],
        [ЖелезнаяВоля, ШипастаяБроня, ЭнергоЯдро, ПроклятаяКорона],
    ),
    "Mage": (
        [create_boil, create_ignite, create_splash, create_arcane_focus,
         create_elemental_surge],
        [ДревнееОгниво, ЭнергоЯдро, ТочильныйКамень, ПроклятаяКорона],
    ),
    "Druid": (
        [create_virulent_strain, create_toxic_cloud, create_poison_stab,
         create_toxic_cloud, create_toxic_cloud],
        [ФлаконСЖелчью, СердцеТитана, ЭнергоЯдро],
    ),
    "Rogue": (
        [create_bloodlust, create_lacerate, create_serrated_edge,
         create_open_wound, create_hemorrhage],
        [ГнилойКлык, ОкровавленныйШприц, ЭнергоЯдро, ТочильныйКамень],
    ),
    "Berserker": (
        [create_battle_cry],
        [ПроклятаяКорона, ЭнергоЯдро, СердцеТитана, ТочильныйКамень],
    ),
    "Summoner": (
        [create_summon_golem, create_summon_wolf, create_summon_golem],
        [ЭнергоЯдро, ТрофейныйКлык, СердцеТитана],
    ),
}


def _card_themes(card) -> set:
    """«Темы» карты — грубые ярлыки её эффектов. Используются, чтобы драфт
    усиливал то, к чему колода УЖЕ склонна (а не ломал архетип универсальным
    «больше урона»). Сустейн-колода ценит хил/щит, ядовитая — яд и т.д."""
    t = set()
    for e in card.effects:
        if isinstance(e, (PoisonEffect, VirulenceEffect)):
            t.add("poison")
        elif isinstance(e, StatusEffect):
            t.add(e.status_type)
        elif isinstance(e, (RegenEffect, HealEffect)):
            t.add("sustain")
        elif isinstance(e, (ShieldEffect, ShieldDamageEffect)):
            t.add("shield")
        elif isinstance(e, SummonEffect):
            t.add("summon")
        elif isinstance(e, DamageEffect):
            t.add("attack")
        elif isinstance(e, (DetonateEffect, FlowEffect)):
            t.add("synergy")
        elif isinstance(e, (BleedEffect, FrenzyEffect)):
            t.add("bleed")
        elif isinstance(e, MasteryEffect):
            t.add("mastery")
        elif isinstance(e, BarrierEffect):
            t.add("shield")
        elif isinstance(e, (EchoEffect, EchoPayoffEffect)):
            t.add("echo")
        elif isinstance(e, DebtScalingDamageEffect):
            t.update(("attack", "debt"))        # атака, масштаб от HP-долга
        elif isinstance(e, (SelfHarmEffect, DebtToForgeOnKillEffect)):
            t.add("debt")                       # движок «кровь в мощь» (Берсерк)
    return t


def _deck_themes(deck: list) -> set:
    """Темы, на которые колода опирается (присутствуют в ≥2 картах). Порог 2
    отсекает шум одиночных карт — отражает реальный архетип, а не случайность."""
    counts: dict = {}
    for card in deck:
        for theme in _card_themes(card):
            counts[theme] = counts.get(theme, 0) + 1
    return {theme for theme, n in counts.items() if n >= 2}


def _card_score(card) -> float:
    """«Сила» карты для жадного драфта = отдача эффектов НА ЕДИНИЦУ энергии.
    Эффективность важнее абсолюта: при лимите энергии лин лёгких карт бьёт
    кучу дорогих бомб (и кормит дешёвые архетипы вроде Берсерка). Поэтому делим
    на стоимость, а не вычитаем её."""
    value = 0.0
    for e in card.effects:
        if isinstance(e, DamageEffect):
            value += e.base_val
        elif isinstance(e, PoisonEffect):
            value += e.base_val * 1.5          # масштабируется по ходам
        elif isinstance(e, StatusEffect):
            value += _STATUS_VALUE.get(e.status_type, 2) * max(1, e.base_turns)
        elif isinstance(e, ShieldEffect):
            value += e.base_val * 0.7
        elif isinstance(e, (RegenEffect, HealEffect)):
            value += e.base_val * 0.5
        elif isinstance(e, SummonEffect):
            value += e.hp * 0.2 + e.attack_power * 2
        elif isinstance(e, ShieldDamageEffect):
            value += 6                          # AoE по щиту
        elif isinstance(e, BleedEffect):
            value += e.base_val * 1.5           # dot, масштабируется по ходам/frenzy
        elif isinstance(e, (DetonateEffect, FlowEffect)):
            value += 4                          # синергия/темпо
        elif isinstance(e, (EchoEffect, EchoPayoffEffect)):
            value += 5                          # ретриггер-множитель (кат.4)
        elif isinstance(e, MasteryEffect):
            value += e.base_val * 3             # +урон ВСЕХ атак до конца боя
        elif isinstance(e, BarrierEffect):
            value += e.base_val * 2.5           # несгораемый щит (компаунд)
        elif isinstance(e, FrenzyEffect):
            value += e.base_val * 2             # усиливает все будущие bleed
        elif isinstance(e, VirulenceEffect):
            value += e.base_val * 2             # усиливает все будущие наложения яда
        elif isinstance(e, DebtScalingDamageEffect):
            value += e.base_val + e.per_depth * 5  # база + оценка глубины долга (~серед.)
        elif isinstance(e, DebtToForgeOnKillEffect):
            value += 3                          # пик долг→FP при добивании (ceiling-движок)
        # SelfHarmEffect — цена (нырок), не пенализируем: урон карты ценится отдельно.
    return value / max(1, card.cost)            # отдача за единицу энергии


def greedy_draft(deck: list, class_name: str) -> None:
    """Драфт метрики CEILING: с тем же шансом-добора, что у wall, семплируем
    _DRAFT_SAMPLE карт и берём ЛУЧШУЮ по эвристике, усиленной «темами» колоды
    (АРХЕТИП-осознанный выбор). Моделирует игрока, собирающего билд вокруг
    своего ядра, а не случайный набор."""
    from managers.balance.runner import _CARD_REWARD_CHANCE
    if random.random() >= _CARD_REWARD_CHANCE:
        return
    from core.cards.catalog import get_pool_for_class
    pool = get_pool_for_class(class_name)
    themes = _deck_themes(deck)
    candidates = [random.choice(pool)() for _ in range(_DRAFT_SAMPLE)]

    def scored(card):
        bonus = _THEME_BONUS * len(_card_themes(card) & themes)
        return _card_score(card) + bonus

    deck.append(max(candidates, key=scored))


def get_ceiling_build(class_name: str):
    """Параметры идеального билда для run_single_run: (draft, extra_cards, relics).
    Если ядро для класса не задано — только жадный драфт (без ручного ядра)."""
    extra_cards, relics = CLASS_CORES.get(class_name, ([], []))
    return greedy_draft, extra_cards, relics
