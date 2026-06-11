# core/ComboRegistry.py
# Data-driven реестр множительных комбо (стихия A + стихия B = ×множитель).
# Аналог StatusRegistry — будущее комбо = одна запись в COMBOS.
#
# Множительные комбо (семейство ХОТФИКС): увеличивают итоговый урон атаки ×multiplier,
# тратят по consume стаков каждого ключа и логируются. EffectCalculator перебирает
# реестр в calculate_damage — никаких жёстких if по каждой паре.
#
# Детонационные комбо (Замыкание-позвоночник) — ДРУГОЙ триггер-архетип (DetonationRegistry),
# здесь не живут.

COMBOS = {
    "hotfix": {
        "name":        "ХОТФИКС",
        "requires":    ("coffee", "legacy"),  # все должны быть > 0 на цели
        "multiplier":  2.0,                   # множитель итогового урона (knob, дизайн-док)
        "consume":     1,                     # снять стаков при срабатывании
        "log":         "[!!! КОМБО: ХОТФИКС (х2.0) !!!]",
    },
}


def all_combos() -> dict:
    """Возвращает все зарегистрированные комбо (для обхода в EffectCalculator)."""
    return COMBOS


def get_combo(key: str) -> dict:
    """Комбо по ключу. KeyError если не найдено."""
    return COMBOS[key]
