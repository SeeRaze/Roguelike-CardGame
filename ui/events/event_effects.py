import random
from ui.events.event_data import CARD_FACTORIES


def _get_relic_class(name: str):
    from core.relics.starter  import LuckyClover, SpikedBracelet, ТочильныйКамень
    from core.relics.elemental import ДревнееОгниво, НамокшаяРукавица
    from core.relics.advanced import (
        ОкровавленныйШприц, СердцеТитана, ГнилойКлык,
        ПроклятаяКорона, ФлаконСЖелчью, СвинцовыйНабалдашник,
        СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер,
        Заплатка, ЗаточенныйОсколок,
    )
    registry = {
        "LuckyClover":        LuckyClover,
        "SpikedBracelet":     SpikedBracelet,
        "ТочильныйКамень":    ТочильныйКамень,
        "ДревнееОгниво":      ДревнееОгниво,
        "НамокшаяРукавица":   НамокшаяРукавица,
        "ОкровавленныйШприц": ОкровавленныйШприц,
        "СердцеТитана":       СердцеТитана,
        "ГнилойКлык":         ГнилойКлык,
        "ПроклятаяКорона":    ПроклятаяКорона,
        "ФлаконСЖелчью":      ФлаконСЖелчью,
        "СвинцовыйНабалдашник": СвинцовыйНабалдашник,
        "СтараяПиявка":       СтараяПиявка,
        "СчастливаяМонетка":  СчастливаяМонетка,
        "ЗасохшийКлевер":     ЗасохшийКлевер,
        "Заплатка":           Заплатка,
        "ЗаточенныйОсколок":  ЗаточенныйОсколок,
    }
    return registry[name]


def _get_card_factory(name: str):
    from core.cards.basic  import create_strike, create_defend, create_heavy_blade, create_iron_wall
    from core.cards.fire   import create_ignite, create_fire_breath
    from core.cards.poison import create_poison_stab, create_toxic_cloud
    from core.cards.water  import create_splash, create_rain_cloud
    from core.cards.heal   import create_bandage, create_second_wind, create_elixir
    from core.cards.buff.regen     import create_regenerate, create_vitality, create_triage
    from core.cards.buff.vampirism import create_drain, create_blood_feast, create_life_tap
    from core.cards.debuff.bleed   import create_lacerate, create_hemorrhage, create_open_wound
    registry = {
        "create_strike":       create_strike,
        "create_defend":       create_defend,
        "create_heavy_blade":  create_heavy_blade,
        "create_iron_wall":    create_iron_wall,
        "create_ignite":       create_ignite,
        "create_fire_breath":  create_fire_breath,
        "create_poison_stab":  create_poison_stab,
        "create_toxic_cloud":  create_toxic_cloud,
        "create_splash":       create_splash,
        "create_rain_cloud":   create_rain_cloud,
        "create_bandage":      create_bandage,
        "create_second_wind":  create_second_wind,
        "create_elixir":       create_elixir,
        "create_regenerate":   create_regenerate,
        "create_vitality":     create_vitality,
        "create_triage":       create_triage,
        "create_drain":        create_drain,
        "create_blood_feast":  create_blood_feast,
        "create_life_tap":     create_life_tap,
        "create_lacerate":     create_lacerate,
        "create_hemorrhage":   create_hemorrhage,
        "create_open_wound":   create_open_wound,
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

    elif key == "gain_card":
        factory = _get_card_factory(value)
        card = factory()
        gm.add_card(card)
        gm.event_result      = "Получена карта:"
        gm.event_result_card = card

    elif key == "gain_random_card":
        card = random.choice(CARD_FACTORIES)()
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