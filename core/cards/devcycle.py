# core/cards/devcycle.py
# ПОЛ СТАРТОВОГО ПУЛА = ЦИКЛ РАЗРАБОТКИ (ярус 1, С59). Заменяют флат Удар/Защита/
# Тяжёлый Клинок/Железная Стена под IT-сеттинг. Числа = шаблон старого флата (крутим
# ИДЕНТИЧНОСТЬ, не баланс — калибровка в капстоуне).
#
# Петля видна с 1-го боя: Коммит (пишешь код) → Пуш в прод (мощь оставляет долг,
# ACCRUE) → Код-ревью (ловишь баги, DEBUG counterplay). Песочница = изоляция
# (щит + несгораемый Барьер). ACCRUE/DEBUG = РАЙДЕР идентичности (одна доп.строка),
# не второй движок — лаконичность под ковку/майлстоуны.
#
# Регистрация: RAW_FACTORIES (catalog) — сейв-совместимость. В стартдеки/GENERIC-пул
# переезжают в задаче 4 (снос флата). Имена согласованы с юзером (С60).
from core.cards.base import Card, DamageEffect, ShieldEffect, BarrierEffect
from core.cards.bug import AccrueBugEffect, DebugBugEffect


def create_commit():
    """«Коммит» (← Удар) — пол-воркхорс: чистый урон, онбординг. Пишешь код."""
    return Card(
        name="Коммит",
        cost=1,
        card_type="attack",
        description="Урон 6(9).",
        effects=[DamageEffect(6, 9)],
    )


def create_push_to_prod():
    """«Пуш в прод» (← Тяжёлый Клинок) — ACCRUE: мощь оставляет долг. Большой урон
    ценой техдолга (+1 Баг в колоду забега). «move fast & break things»."""
    return Card(
        name="Пуш в прод",
        cost=2,
        card_type="attack",
        description="Урон 14(20). Навешивает 1 Баг.",
        effects=[DamageEffect(14, 20), AccrueBugEffect(1)],
    )


def create_code_review():
    """«Код-ревью» (← Защита) — DEBUG counterplay: щит + вычистить 1 Баг из руки
    (и перманентно из колоды забега). Ловишь баги."""
    return Card(
        name="Код-ревью",
        cost=1,
        card_type="defense",
        description="Щит 5(8). Дебажит 1 Баг из руки.",
        effects=[ShieldEffect(5, 8), DebugBugEffect(1)],
    )


def create_sandbox():
    """«Песочница» (← Железная Стена) — изоляция: щит + половина в несгораемый Барьер
    (синергия выживаемости, копится ход-за-ходом)."""
    return Card(
        name="Песочница",
        cost=2,
        card_type="defense",
        description="Щит 12(18). Барьер 6(9).",
        effects=[ShieldEffect(12, 18), BarrierEffect(6, 9)],
    )
