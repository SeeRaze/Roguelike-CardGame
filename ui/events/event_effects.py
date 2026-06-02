import random
from ui.events.event_data import CARD_FACTORIES

# ─── Реликвии по имени ───────────────────────────────────────────────────────
def _get_relic_class(name: str):
    from core.relics.starter   import LuckyClover, SpikedBracelet, ТочильныйКамень
    from core.relics.elemental import ДревнееОгниво, НамокшаяРукавица
    registry = {
        "LuckyClover":       LuckyClover,
        "SpikedBracelet":    SpikedBracelet,
        "ТочильныйКамень":   ТочильныйКамень,
        "ДревнееОгниво":     ДревнееОгниво,
        "НамокшаяРукавица":  НамокшаяРукавица,
    }
    return registry[name]


# ─── Карты по имени ──────────────────────────────────────────────────────────
def _get_card_factory(name: str):
    from core.cards.basic  import create_strike, create_defend, create_heavy_blade, create_iron_wall
    from core.cards.fire   import create_ignite, create_fire_breath
    from core.cards.poison import create_poison_stab, create_toxic_cloud
    from core.cards.water  import create_splash, create_rain_cloud
    registry = {
        "create_strike":      create_strike,
        "create_defend":      create_defend,
        "create_heavy_blade": create_heavy_blade,
        "create_iron_wall":   create_iron_wall,
        "create_ignite":      create_ignite,
        "create_fire_breath": create_fire_breath,
        "create_poison_stab": create_poison_stab,
        "create_toxic_cloud": create_toxic_cloud,
        "create_splash":      create_splash,
        "create_rain_cloud":  create_rain_cloud,
    }
    return registry[name]


# ─── Применение одного эффекта ───────────────────────────────────────────────
def apply_effect(effect_str: str, gm) -> None:
    """Разбирает строку вида 'heal:20' и применяет эффект к gm."""
    if ":" in effect_str:
        key, value = effect_str.split(":", 1)
    else:
        key, value = effect_str, None

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
        gm.event_result = f"Получена карта: {card.name}"

    elif key == "gain_random_card":
        card = random.choice(CARD_FACTORIES)()
        gm.add_card(card)
        gm.event_result = f"Получена карта: {card.name}"

    elif key == "gain_relic":
        relic_cls = _get_relic_class(value)
        r = relic_cls()
        gm.relics.append(r)
        gm.event_result = f"Получена реликвия: {r.name}"

    elif key == "skip":
        gm.event_result = "Вы прошли мимо."


# ─── Применение всех эффектов варианта ──────────────────────────────────────
def apply_option(option: dict, gm) -> None:
    """Принимает dict варианта из event_data и применяет все его эффекты."""
    for effect_str in option["effects"]:
        apply_effect(effect_str, gm)