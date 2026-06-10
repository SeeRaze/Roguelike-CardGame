# core/DetonationRegistry.py
# ЗАМЫКАНИЕ-ПОЗВОНОЧНИК (С58). Короткое замыкание (`shortcircuit`) = универсальный
# ДЕТОНАТОР. Со-присутствующий элемент решает, ВО ЧТО детонирует («вкус»). Вместо N
# независимых записей — ОДИН путь detonate(), ветка по присутствующим статусам.
#
# БАЗА (всегда при детонации): снос щита + бурст = заряды × DMG_PER_CHARGE по цели.
# ВКУСЫ (каждый, если со-элемент present на цели):
#   Кофе   → ЭЛЕКТРОЛИЗ        — бурст ещё и сплэшит по ВСЕМ прочим врагам (AoE).
#   Legacy → ЦИКЛИЧНЫЙ ПОВТОР  — детонирует накопленный Legacy-DoT (×CYCLIC), сжигает.
#   Токс   → НЕЙРОТОКСИН       — стан на 1 ход («Crash»).
#   Утечка → АППАРАТНЫЙ СБОЙ   — стаки Утечки → энергия игрока (кап +HARDFAULT/ход).
#
# Триггеры детонации: (1) карта-детонатор через DetonateEffect; (2) авто при достижении
# порога SHORTCIRCUIT_THRESHOLD (см. end_turn_phase). Все числа — СТАРТОВЫЕ (Блок 4).

SHORTCIRCUIT_THRESHOLD   = 5     # порог авто-детонации (зарядов)
DMG_PER_CHARGE           = 2     # базовый бурст за стак заряда
ELECTROLYSIS_SPLASH      = 1     # AoE-сплэш по прочим врагам за стак (вкус Кофе)
CYCLIC_LEGACY_MULT       = 2     # детонация накопленного Legacy (вкус Legacy)
HARDFAULT_ENERGY_CAP     = 3     # кап конверсии Утечки → энергия за детонацию


def _deal_raw(victim, amount, player, combat_manager):
    """RAW-урон через take_damage (без EffectCalculator — детонация не рекурсит
    реакции). Уважает щит цели (если он ещё есть)."""
    if amount > 0:
        victim.take_damage(amount, attacker=player, combat_manager=combat_manager)


def detonate(target, combat_manager):
    """Подорвать Короткое замыкание на цели. Возвращает суммарный мгнов. урон.
    Инертно (0), если на цели нет заряда `shortcircuit`."""
    if combat_manager is None:
        return 0
    sc = target.get_status("shortcircuit")
    if sc <= 0:
        return 0
    player  = getattr(combat_manager, "player", None)
    enemies = getattr(combat_manager, "enemies", [target])
    target.set_status("shortcircuit", 0)          # заряд потрачен
    combat_manager.add_log_message("[!!! ДЕТОНАЦИЯ: КОРОТКОЕ ЗАМЫКАНИЕ !!!]")

    # БАЗА: снос щита + бурст по цели.
    target.shield = 0
    base = sc * DMG_PER_CHARGE
    _deal_raw(target, base, player, combat_manager)
    total = base
    combat_manager.add_log_message(f" -> Снос щита + {base} урона по цели.")

    # ВКУС: Кофе → ЭЛЕКТРОЛИЗ (AoE-сплэш по прочим врагам). Кофе тратится.
    if target.get_status("coffee") > 0:
        splash = sc * ELECTROLYSIS_SPLASH
        for o in list(enemies):
            if o is not target and o.hp > 0:
                _deal_raw(o, splash, player, combat_manager)
                total += splash
        target.set_status("coffee", 0)
        combat_manager.add_log_message(
            f" -> ЭЛЕКТРОЛИЗ: {splash} урона по всем прочим врагам."
        )

    # ВКУС: Legacy → ЦИКЛИЧНЫЙ ПОВТОР (детонация накопленного DoT, ×CYCLIC). Legacy сожжён.
    leg = target.get_status("legacy")
    if leg > 0:
        burst = leg * CYCLIC_LEGACY_MULT
        _deal_raw(target, burst, player, combat_manager)
        target.set_status("legacy", 0)
        total += burst
        combat_manager.add_log_message(
            f" -> ЦИКЛИЧНЫЙ ПОВТОР: {burst} урона (Legacy-код сожжён)."
        )

    # ВКУС: Токс → НЕЙРОТОКСИН (стан 1 ход). Токс остаётся саботировать урон.
    if target.get_status("tox") > 0:
        target.set_status("stunned", 1)
        combat_manager.add_log_message(
            f" -> НЕЙРОТОКСИН: {target.name} оглушён (Crash)."
        )

    # ВКУС: Утечка → АППАРАТНЫЙ СБОЙ (Утечка → энергия, кап +HARDFAULT/ход). Частично сжигает.
    leak = target.get_status("leak")
    if leak > 0 and player is not None:
        gain = min(HARDFAULT_ENERGY_CAP, leak)
        player.gain_energy(gain)
        target.set_status("leak", leak - gain)
        combat_manager.add_log_message(
            f" -> АППАРАТНЫЙ СБОЙ: Утечка → +{gain} энергии."
        )

    return total


def all_detonations() -> dict:
    """DEPRECATED (С58): data-driven реестр заменён функцией-позвоночником detonate().
    Пустой dict — совместимость с бот-политикой (managers/balance/policy.py) до её
    re-bless в G1. Не использовать в новом коде."""
    return {}
