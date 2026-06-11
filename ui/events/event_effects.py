import random
from core.cards.catalog import get_pool_for_class


def _get_relic_class(name: str):
    from core.relics.starter  import Автодополнение, РеверсПрокси, Линтер
    from core.relics.elemental import Дебаггер, ПассивнаяАгрессия
    from core.relics.advanced import (
        СборщикМусора, ОткатКБэкапу, ЗомбиПроцесс,
        МаршСмерти, GitBlame, Дедлайн,
        СнекБар, Кэшбэк, ФоновоеИндексирование,
        ДМСБазовый, УтреннийСозвон,
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
        "МаршСмерти":    МаршСмерти,
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
    from core.cards.poison import create_poison_stab, create_toxic_cloud
    from core.cards.legacy import create_legacy_patch, create_tech_debt
    from core.cards.heal   import create_bandage, create_second_wind, create_elixir
    from core.cards.buff.regen     import create_regenerate, create_vitality, create_triage
    from core.cards.buff.vampirism import create_drain, create_blood_feast, create_life_tap
    registry = {
        "create_strike":       create_strike,
        "create_defend":       create_defend,
        "create_heavy_blade":  create_heavy_blade,
        "create_iron_wall":    create_iron_wall,
        "create_coffee_spill": create_coffee_spill,
        "create_coffee_flood": create_coffee_flood,
        "create_poison_stab":  create_poison_stab,
        "create_toxic_cloud":  create_toxic_cloud,
        "create_legacy_patch": create_legacy_patch,
        "create_tech_debt":    create_tech_debt,
        "create_bandage":      create_bandage,
        "create_second_wind":  create_second_wind,
        "create_elixir":       create_elixir,
        "create_regenerate":   create_regenerate,
        "create_vitality":     create_vitality,
        "create_triage":       create_triage,
        "create_drain":        create_drain,
        "create_blood_feast":  create_blood_feast,
        "create_life_tap":     create_life_tap,
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

    elif key == "remove_flag":
        if hasattr(gm, value):
            setattr(gm, value, False)
        gm.event_result = "Флаг снят."

    elif key == "skip":
        gm.event_result = "Вы прошли мимо."


def apply_option(option: dict, gm) -> None:
    for effect_str in option["effects"]:
        apply_effect(effect_str, gm)