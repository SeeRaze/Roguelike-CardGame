# ui/cards/classifier.py
# Классификация карты по составу эффектов -> ключ палитры (см. data._C).
from core.cards.base import (
    StatusEffect, PoisonEffect, RegenEffect, HealEffect,
    VampireDamageEffect, DamageEffect, ShieldEffect,
)
from core.cards.debuff.bleed import BleedEffect
from core.cards.buff.strength import BuffEffect
from core.cards.buff.vampirism import VampireBuffEffect


def classify_card(card) -> str:
    """Определяет класс карты по составу эффектов. Возвращает ключ из data._C."""
    effects = card.effects
    has_damage   = any(isinstance(e, (DamageEffect, VampireDamageEffect)) for e in effects)
    has_vampire  = any(isinstance(e, VampireBuffEffect) for e in effects)
    has_bleed    = any(isinstance(e, BleedEffect) for e in effects)
    has_poison   = any(isinstance(e, PoisonEffect) for e in effects)
    has_shield   = any(isinstance(e, ShieldEffect) for e in effects)
    has_heal     = any(isinstance(e, HealEffect) for e in effects)
    has_regen    = any(isinstance(e, RegenEffect) for e in effects)
    has_buff     = any(isinstance(e, BuffEffect) for e in effects)

    has_ignited  = any(isinstance(e, StatusEffect) and e.status_type == "ignited" for e in effects)
    has_wet      = any(isinstance(e, StatusEffect) and e.status_type == "wet"     for e in effects)
    has_shock    = any(isinstance(e, StatusEffect) and e.status_type == "shock"   for e in effects)
    has_shatter  = any(isinstance(e, StatusEffect) and e.status_type == "shatter" for e in effects)
    has_debuff   = any(
        isinstance(e, StatusEffect) and e.status_type in ("vulnerable", "weak")
        for e in effects
    )

    if has_vampire:
        return "vampire"
    if has_bleed:
        return "bleed"
    if has_poison:
        return "poison"
    if has_ignited:
        return "fire"
    if has_wet:
        return "water"
    if has_shock:
        return "shock"
    if has_shatter:
        return "earth"
    if has_regen:
        return "regen"
    if has_heal:
        return "heal"
    if has_buff:
        return "buff"
    if has_debuff:
        return "debuff"
    if has_shield and not has_damage:
        return "shield"
    if has_damage and not has_shield and not has_debuff:
        return "attack_pure"
    if has_damage:
        return "attack_mixed"
    if has_shield:
        return "shield"
    return "default"
