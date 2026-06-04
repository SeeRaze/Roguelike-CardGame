# core/DetonationRegistry.py
# Data-driven реестр ДЕТОНАЦИОННЫХ комбо — второй архетип комбо рядом с
# ComboRegistry (множительные ×N к текущей атаке).
#
# Отличие архетипов:
#   ComboRegistry      — МНОЖИТ урон текущей атаки (×N), напр. ПАР. Срабатывает
#                        в EffectCalculator.calculate_damage при ударе.
#   DetonationRegistry — мгновенный ЭФФЕКТ (бурст/AoE/распространение/обнуление
#                        щита), не привязанный к урону текущей карты. Срабатывает
#                        через эффект-кирпич DetonateEffect (карты-детонаторы).
#
# Каждая детонация = одна запись: requires (какие статусы должны быть на цели > 0)
# + handler(target, combat_manager) (что сделать; сам снимает потраченные статусы)
# + log. Будущее меж-стихийное комбо = одна запись здесь (+ опц. карта-детонатор).

# Урон Электро-взрыва за каждый стак Шока (тюнится здесь).
ELECTRO_DAMAGE_PER_SHOCK = 6


def _electro_blast(target, combat_manager):
    """Электро-взрыв (Мокрый + Шок): мокрая цель проводит разряд — урон
    = Шок × ELECTRO_DAMAGE_PER_SHOCK по ВСЕМ живым врагам. Затем снять Мокрый
    и Шок с цели (потрачены во взрыве).

    Урон — RAW (через take_damage напрямую), НЕ через EffectCalculator: детонация
    не должна рекурсивно тянуть бонус Шока/комбо/уязвимость с самой себя."""
    shock = target.get_status("shock")
    burst = shock * ELECTRO_DAMAGE_PER_SHOCK
    player = getattr(combat_manager, "player", None)

    for enemy in list(getattr(combat_manager, "enemies", [])):
        if enemy.hp > 0:
            enemy.take_damage(burst, attacker=player, combat_manager=combat_manager)

    target.set_status("wet", 0)
    target.set_status("shock", 0)

    combat_manager.add_log_message(
        f" -> Электро-взрыв: {burst} урона по всем врагам!"
    )
    return burst


DETONATIONS = {
    "electro_blast": {
        "name":     "ЭЛЕКТРО-ВЗРЫВ",
        "requires": ("wet", "shock"),    # оба должны быть > 0 на цели
        "handler":  _electro_blast,
        "log":      "[!!! ДЕТОНАЦИЯ: ЭЛЕКТРО-ВЗРЫВ !!!]",
    },
}


def all_detonations() -> dict:
    """Все зарегистрированные детонации (для обхода в DetonateEffect)."""
    return DETONATIONS


def get_detonation(key: str) -> dict:
    """Детонация по ключу. KeyError если не найдена."""
    return DETONATIONS[key]
