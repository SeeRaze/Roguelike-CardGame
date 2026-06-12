# ui/cards/classifier.py
# Классификация карты по составу эффектов -> ключ палитры (см. data.card_palette).
from core.cards.base import (
    StatusEffect, AoEStatusEffect, DecompEffect, RegenEffect, HealEffect,
    VampireDamageEffect, DamageEffect, ShieldEffect,
    BarrierEffect,
)
from ui.cards.data import _ELEMENTAL_CARD_KEYS
from core.cards.buff.strength import BuffEffect
from core.cards.buff.vampirism import VampireBuffEffect
from core.cards.air import FlowEffect
from core.cards.echo import EchoEffect, EchoPayoffEffect
from core.cards.mage import MasteryEffect
from core.cards.berserker import DebtScalingDamageEffect
from core.cards.warrior import DisciplineBurstDamageEffect, DisciplineToShieldEffect
from core.cards.mage import OverclockEffect, MasteryScalingDamageEffect


def _elemental_key(effects):
    """Первый стихийный ключ среди эффектов карты (порядок = как лежат в карте), или
    None. DecompEffect → 'decomp'; StatusEffect/AoEStatusEffect → его status_type,
    если он стихийный. Не-стихийные статусы игнорируются."""
    for e in effects:
        if isinstance(e, DecompEffect):
            return "decomp"
        if isinstance(e, (StatusEffect, AoEStatusEffect)) and \
                e.status_type in _ELEMENTAL_CARD_KEYS:
            return e.status_type
    return None


def classify_card(card) -> str:
    """Определяет класс карты по составу эффектов. Возвращает ключ для card_palette."""
    # Слой БАГОВ (ярус 1): несыгрываемая карта-долг — отдельный «проклятый» вид,
    # независимо от эффектов (у Бага их нет). Проверяем ПЕРВЫМ.
    if getattr(card, "unplayable", False):
        return "bug"

    effects = card.effects
    has_damage   = any(isinstance(e, (DamageEffect, VampireDamageEffect, EchoPayoffEffect, DebtScalingDamageEffect, DisciplineBurstDamageEffect, MasteryScalingDamageEffect)) for e in effects)
    has_cache_hit = any(isinstance(e, VampireBuffEffect) for e in effects)
    has_shield   = any(isinstance(e, (ShieldEffect, DisciplineToShieldEffect)) for e in effects)
    has_heal     = any(isinstance(e, HealEffect) for e in effects)
    has_healthcheck = any(isinstance(e, RegenEffect) for e in effects)
    has_buff     = any(isinstance(e, BuffEffect) for e in effects)
    has_flow     = any(isinstance(e, FlowEffect) for e in effects)
    has_echo     = any(isinstance(e, EchoEffect) for e in effects)
    has_barrier  = any(isinstance(e, BarrierEffect) for e in effects)
    has_mastery  = any(isinstance(e, (MasteryEffect, OverclockEffect)) for e in effects)

    # Стихия-PAYLOAD: первый стихийный ключ среди эффектов (StatusEffect/AoE по
    # status_type, DecompEffect → "decomp"). Рамка карты = цвет этой стихии.
    elemental = _elemental_key(effects)

    if has_cache_hit:
        return "cache_hit"
    if elemental:
        return elemental
    if has_flow:
        return "air"
    if has_echo:
        return "echo"
    if has_barrier:
        return "barrier"
    if has_mastery:
        return "mastery"
    if has_healthcheck:
        return "healthcheck"
    if has_heal:
        return "heal"
    if has_buff:
        return "buff"
    if has_shield and not has_damage:
        return "shield"
    if has_damage and not has_shield:
        return "attack_pure"
    if has_damage:
        return "attack_mixed"
    if has_shield:
        return "shield"
    return "default"
