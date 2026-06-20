import random
from core.cards.catalog import get_pool_for_class


def _get_relic_class(name: str):
    from core.relics.starter  import Автодополнение, РеверсПрокси, Линтер
    from core.relics.elemental import Дебаггер, ПассивнаяАгрессия
    from core.relics.advanced import (
        СборщикМусора, ОткатКБэкапу, ЗомбиПроцесс,
        МаршСмерти, GitBlame, Дедлайн,
        СнекБар, Кэшбэк, ФоновоеИндексирование,
        ДМСБазовый, УтреннийСозвон, ТочкаОтказа, ДеплойВПятницу,
    )
    registry = {
        "Автодополнение":        Автодополнение,
        "Реверс-прокси":     РеверсПрокси,
        "Линтер":    Линтер,
        "Дебаггер":      Дебаггер,
        "ПассивнаяАгрессия":   ПассивнаяАгрессия,
        "СборщикМусора": СборщикМусора,
        "ОткатКБэкапу":       ОткатКБэкапу,
        "ЗомбиПроцесс":         ЗомбиПроцесс,
        "МаршСмерти":    МаршСмерти,   # LEGENDARY за испытание (С72): изъят из рандом-выдачи → только развязкой
        "ТочкаОтказа":   ТочкаОтказа,  # LEGENDARY за испытание (С72, раскатка Z2): выдаётся развязкой «Точка отказа»
        "ДеплойВПятницу": ДеплойВПятницу,  # LEGENDARY за испытание (С72, Z3): выдаётся развязкой «Деплой в пятницу»
        "GitBlame":      GitBlame,
        "Дедлайн": Дедлайн,
        "СнекБар":       СнекБар,
        "Кэшбэк":  Кэшбэк,
        "ФоновоеИндексирование":     ФоновоеИндексирование,
        "ДМСБазовый":           ДМСБазовый,
        "УтреннийСозвон":  УтреннийСозвон,
    }
    return registry[name]


def _get_card_factory(name: str):
    from core.cards.basic  import create_strike, create_defend, create_heavy_blade, create_iron_wall
    from core.cards.coffee import create_coffee_spill, create_coffee_flood
    from core.cards.legacy import create_legacy_patch, create_tech_debt
    from core.cards.heal   import create_bandage, create_second_wind, create_elixir
    from core.cards.buff.regen     import create_regenerate, create_vitality, create_triage
    registry = {
        "create_strike":       create_strike,
        "create_defend":       create_defend,
        "create_heavy_blade":  create_heavy_blade,
        "create_iron_wall":    create_iron_wall,
        "create_coffee_spill": create_coffee_spill,
        "create_coffee_flood": create_coffee_flood,
        "create_legacy_patch": create_legacy_patch,
        "create_tech_debt":    create_tech_debt,
        "create_bandage":      create_bandage,
        "create_second_wind":  create_second_wind,
        "create_elixir":       create_elixir,
        "create_regenerate":   create_regenerate,
        "create_vitality":     create_vitality,
        "create_triage":       create_triage,
    }
    return registry[name]


def apply_effect(effect_str: str, gm) -> None:
    if ":" in effect_str:
        key, value = effect_str.split(":", 1)
    else:
        key, value = effect_str, None

    # Сброс карты-награды по умолчанию
    gm.event_result_card = None

    if key == "heal":
        amount = int(value)
        gm.player.hp = min(gm.player.hp + amount, gm.player.max_hp)
        gm.event_result = f"+{amount} HP"

    elif key == "lose_hp":
        amount = int(value)
        gm.player.hp = max(gm.player.hp - amount, 1)
        gm.event_result = f"-{amount} HP"

    elif key == "gain_gold":
        amount = int(value)
        gm.player_gold += amount
        gm.event_result = f"+{amount} золота"

    elif key == "lose_gold":
        amount = int(value)
        gm.player_gold = max(gm.player_gold - amount, 0)
        gm.event_result = f"-{amount} золота"

    # ─── %-ВАРИАНТЫ (HP-ось, шаг 2 эконом-дуги) ──────────────────────────────
    # HP-эффекты = % от MAX HP (масштаб-инвариантны: значимы и на эт.5, и на эт.90,
    # где max HP вырос). Золото держим АДДИТИВНЫМ (economy-axis-trinity): потери —
    # % от кошелька (честно при любом богатстве), прибыль — масштаб по этажу.
    elif key == "heal_pct":
        amount = max(1, int(gm.player.max_hp * float(value)))
        gm.player.hp = min(gm.player.hp + amount, gm.player.max_hp)
        gm.event_result = f"+{amount} HP"

    elif key == "lose_hp_pct":
        amount = max(1, int(gm.player.max_hp * float(value)))
        gm.player.hp = max(gm.player.hp - amount, 1)
        gm.event_result = f"-{amount} HP"

    elif key == "lose_gold_pct":
        amount = int(gm.player_gold * float(value))
        gm.player_gold = max(gm.player_gold - amount, 0)
        gm.event_result = f"-{amount} золота"

    elif key == "gain_gold_floor":
        # Прибыль золота, масштабируемая этажом (зеркало gold_reward = …+floor·K):
        # держит золото плоско-читаемым, без экспоненты на валюте.
        amount = int(float(value) * gm.current_floor)
        gm.player_gold += amount
        gm.event_result = f"+{amount} золота"

    elif key == "temper_spirit":
        # «Закалить дух»: +% к МАКС. HP навсегда (зеркало Сердца Бездны), с хилом
        # на дельту. Живой источник роста HP-оси через события.
        gain = max(1, int(gm.player.max_hp * float(value)))
        gm.player.max_hp += gain
        gm.player.hp = min(gm.player.hp + gain, gm.player.max_hp)
        gm.event_result = f"+{gain} к макс. HP"

    elif key == "gain_card":
        factory = _get_card_factory(value)
        card = factory()
        gm.add_card(card)
        gm.event_result      = "Получена карта:"
        gm.event_result_card = card

    elif key == "gain_random_card":
        pool = get_pool_for_class(type(gm.player).__name__, getattr(gm, "meta", None))
        card = random.choice(pool)()
        gm.add_card(card)
        gm.event_result      = "Получена карта:"
        gm.event_result_card = card

    elif key == "gain_relic":
        relic_cls = _get_relic_class(value)
        r = relic_cls()
        gm.relics.append(r)
        gm.event_result = f"Получена реликвия: {r.name}"

    elif key == "gain_random_relic":
        # Случайная реликвия из ВСЕГО пула (meta-фильтр по анлокам, как у карт), а не
        # из устаревшего ручного реестра _get_relic_class → события дотягиваются до
        # нового контента (Блок 3). Дедуп по уже имеющимся (не выдаём дубль).
        # Легендарки-за-испытание (С72) исключены — они только за развязку испытания.
        from core.relics import ALL_RELICS
        from core.progression import is_relic_unlocked, relic_id_for, is_challenge_relic
        meta  = getattr(gm, "meta", None)
        owned = {type(r).__name__ for r in gm.relics}
        elig  = [c for c in ALL_RELICS if not is_challenge_relic(relic_id_for(c))]
        pool  = [c for c in elig
                 if is_relic_unlocked(meta, relic_id_for(c)) and c.__name__ not in owned]
        if not pool:                      # всё уже есть/залочено → не падаем
            pool = [c for c in elig if c.__name__ not in owned] or elig
        r = random.choice(pool)()
        gm.relics.append(r)
        gm.event_result = f"Получена реликвия: {r.name}"

    elif key == "gain_forge":
        # +N очков ковки (CR-ось, economy-axis-trinity): событий-источников CR не было.
        amount = int(value)
        gm.player.forge_points = getattr(gm.player, "forge_points", 0) + amount
        gm.event_result = f"+{amount} CR"

    elif key == "accrue_bug":
        # +N Багов в колоду забега: тематическая ЦЕНА техдолга (мост к bug-слою).
        # Баг = несыгрываемая карта, дилютит добор; чистится Код-ревью/DEBUG.
        from core.cards.bug import create_bug
        amount = int(value)
        for _ in range(amount):
            gm.add_card(create_bug())
        gm.event_result = f"+{amount} Баг(ов) в колоду"

    elif key == "set_flag":
        # Ставит флаг-веху забега (мост многошаговых ИСПЫТАНИЙ, С72): завязка ставит
        # флаг → развязка-событие читает его через condition (зеркало remove_flag).
        # СКРЫТЫЙ ПЕЙОФФ (решение юзера): не спойлерит награду — даём нейтральный
        # event_result, который перетрётся ценой (lose_hp_pct идёт в опции ПОСЛЕ).
        setattr(gm, value, True)
        gm.event_result = "Ты ввязался."

    elif key == "remove_flag":
        if hasattr(gm, value):
            setattr(gm, value, False)
        gm.event_result = "Флаг снят."

    elif key == "skip":
        gm.event_result = "Вы прошли мимо."


def apply_option(option: dict, gm) -> None:
    for effect_str in option["effects"]:
        apply_effect(effect_str, gm)