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

# ─── Константы тюнинга детонаций ─────────────────────────────────────────────
ELECTRO_DAMAGE_PER_SHOCK = 6     # Электро-взрыв: урон за стак Шока
LAVA_DAMAGE_PER_IGNITE   = 4     # Лава: урон за стак Горения
THERMO_DAMAGE_MULT       = 3     # Термовзрыв: множитель (Горение+Шок)


def _deal_raw(target, amount, combat_manager, aoe=False):
    """Нанести RAW-урон (через take_damage, БЕЗ EffectCalculator — детонация не
    рекурсит Шок/комбо). aoe=True бьёт всех живых врагов, иначе только цель."""
    player = getattr(combat_manager, "player", None)
    if aoe:
        victims = [e for e in getattr(combat_manager, "enemies", []) if e.hp > 0]
    else:
        victims = [target]
    for v in victims:
        v.take_damage(amount, attacker=player, combat_manager=combat_manager)


def _electro_blast(target, combat_manager):
    """Электро-взрыв (Мокрый + Шок): мокрая цель проводит разряд — урон
    = Шок × ELECTRO_DAMAGE_PER_SHOCK по ВСЕМ живым врагам. Снять Мокрый и Шок."""
    burst = target.get_status("shock") * ELECTRO_DAMAGE_PER_SHOCK
    _deal_raw(target, burst, combat_manager, aoe=True)
    target.set_status("wet", 0)
    target.set_status("shock", 0)
    combat_manager.add_log_message(
        f" -> Электро-взрыв: {burst} урона по всем врагам!"
    )
    return burst


def _lava(target, combat_manager):
    """Лава (Раскол + Горение): мгновенный урон = Горение × LAVA_DAMAGE_PER_IGNITE
    по цели + снижение её намерения атаки вдвое (расплавленная не может бить в
    полную силу). Снять Раскол и Горение."""
    burst = target.get_status("ignited") * LAVA_DAMAGE_PER_IGNITE
    _deal_raw(target, burst, combat_manager)

    intent = getattr(target, "intent", None)
    if intent is not None and getattr(intent, "type", None) == "attack":
        intent.value = intent.value // 2
        combat_manager.add_log_message(
            f" -> Лава: намерение атаки {target.name} ослаблено до {intent.value}."
        )

    target.set_status("shatter", 0)
    target.set_status("ignited", 0)
    combat_manager.add_log_message(f" -> Лава: {burst} урона!")
    return burst


def _thermo_blast(target, combat_manager):
    """Термодинамический взрыв (Горение + Шок): мгновенный урон
    = (Горение + Шок) × THERMO_DAMAGE_MULT по цели. Снять Горение и Шок."""
    burst = (target.get_status("ignited")
             + target.get_status("shock")) * THERMO_DAMAGE_MULT
    _deal_raw(target, burst, combat_manager)
    target.set_status("ignited", 0)
    target.set_status("shock", 0)
    combat_manager.add_log_message(f" -> Термовзрыв: {burst} урона!")
    return burst


def _acid(target, combat_manager):
    """Кислота (Мокрый + Яд): растворяет броню — щит цели в ноль. Снять Мокрый
    (катализатор потрачен); Яд ОСТАЁТСЯ тикать сквозь обнулённый щит."""
    target.shield = 0
    target.set_status("wet", 0)
    combat_manager.add_log_message(f" -> Кислота: щит {target.name} растворён!")
    return 0


def _poison_blast(target, combat_manager):
    """Ядовзрыв (Яд + Горение): детонирует ВЕСЬ яд мгновенно СКВОЗЬ щит
    (= стаки Яда уроном прямо в HP, как тик яда), снимает Яд и УДВАИВАЕТ Горение
    (пламя раздувает токсичные пары)."""
    burst = target.get_status("poison")
    target.hp = max(0, target.hp - burst)          # сквозь щит (прямо в HP)
    target.set_status("poison", 0)
    target.set_status("ignited", target.get_status("ignited") * 2)
    combat_manager.add_log_message(
        f" -> Ядовзрыв: {burst} урона сквозь щит, Горение удвоено!"
    )
    return burst


DETONATIONS = {
    # Порядок = ПРИОРИТЕТ при общих статусах: детонация, потратившая общий статус,
    # гасит зависящие от него последующие (requires проверяется заново в DetonateEffect).
    "electro_blast": {
        "name":     "ЭЛЕКТРО-ВЗРЫВ",
        "requires": ("wet", "shock"),
        "handler":  _electro_blast,
        "log":      "[!!! ДЕТОНАЦИЯ: ЭЛЕКТРО-ВЗРЫВ !!!]",
    },
    "thermo_blast": {
        "name":     "ТЕРМОВЗРЫВ",
        "requires": ("ignited", "shock"),
        "handler":  _thermo_blast,
        "log":      "[!!! ДЕТОНАЦИЯ: ТЕРМОВЗРЫВ !!!]",
    },
    "lava": {
        "name":     "ЛАВА",
        "requires": ("shatter", "ignited"),
        "handler":  _lava,
        "log":      "[!!! ДЕТОНАЦИЯ: ЛАВА !!!]",
    },
    "acid": {
        "name":     "КИСЛОТА",
        "requires": ("wet", "poison"),
        "handler":  _acid,
        "log":      "[!!! ДЕТОНАЦИЯ: КИСЛОТА !!!]",
    },
    "poison_blast": {
        "name":     "ЯДОВЗРЫВ",
        "requires": ("poison", "ignited"),
        "handler":  _poison_blast,
        "log":      "[!!! ДЕТОНАЦИЯ: ЯДОВЗРЫВ !!!]",
    },
}


def all_detonations() -> dict:
    """Все зарегистрированные детонации (для обхода в DetonateEffect)."""
    return DETONATIONS


def get_detonation(key: str) -> dict:
    """Детонация по ключу. KeyError если не найдена."""
    return DETONATIONS[key]
