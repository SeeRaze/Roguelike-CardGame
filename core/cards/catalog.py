# core/cards/catalog.py
# Единый каталог карт — ЕДИНСТВЕННЫЙ источник правды о том, какие карты
# существуют и кому они доступны. Без pygame, чистые данные + хелперы.
#
# Деление:
#   GENERIC_FACTORIES  — нейтральные карты, доступны всем классам (общий пул).
#   CLASS_FACTORIES    — классовые карты, выдаются в забеге ТОЛЬКО своему классу.
#
# Добавить классовую карту = одна строка в CLASS_FACTORIES.
from core.cards import (
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_catalyst,
    create_steel_barricade, create_bastion,
    create_ignite, create_fire_breath,
    create_splash, create_rain_cloud,
    create_shock_bolt, create_chain_lightning, create_thunder_strike, create_overload,
    create_rockfall, create_crush, create_tectonic_strike,
    create_gust, create_updraft, create_whirlwind, create_sirocco,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
    create_bash, create_neutralize, create_intimidate,
    create_flex, create_battle_cry, create_thorn_armor,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_drain, create_blood_feast, create_life_tap,
    create_lacerate, create_hemorrhage, create_open_wound,
    create_summon_wolf, create_summon_golem,
    create_retribution,
    create_boil, create_arcane_focus, create_elemental_surge,
    create_echo_resonance, create_echo_strike, create_echo_cascade,
    create_bloodlust, create_serrated_edge,
    create_cleaving_strike, create_piercing_thrust, create_wide_swing,
)

# ─── Нейтральные карты (generic) — общий пул для всех классов ────────────────
GENERIC_FACTORIES = [
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_catalyst,
    create_ignite, create_fire_breath,
    create_splash, create_rain_cloud,
    create_shock_bolt, create_chain_lightning, create_thunder_strike, create_overload,
    create_rockfall, create_crush, create_tectonic_strike,
    create_gust, create_updraft, create_whirlwind, create_sirocco,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
    create_bash, create_neutralize, create_intimidate,
    create_flex, create_battle_cry, create_thorn_armor,
    create_bandage, create_second_wind, create_elixir,
    create_regenerate, create_vitality, create_triage,
    create_drain, create_blood_feast, create_life_tap,
    create_lacerate, create_hemorrhage, create_open_wound,
    create_echo_resonance, create_echo_strike, create_echo_cascade,
    create_cleaving_strike, create_piercing_thrust, create_wide_swing,
]

# ─── Классовые карты — выдаются только своему классу ─────────────────────────
CLASS_FACTORIES = {
    "Summoner": [create_summon_wolf, create_summon_golem],
    "Warrior":  [create_retribution, create_steel_barricade, create_bastion],
    "Mage":     [create_boil, create_arcane_focus, create_elemental_surge],
    "Rogue":    [create_bloodlust, create_serrated_edge],
}


def _tagged(factory, class_name):
    """Обёртка фабрики: помечает созданную карту принадлежностью классу.
    Фабрики остаются чистыми — тег проставляется централизованно здесь."""
    def make():
        card = factory()
        card.card_class = class_name
        return card
    # Сохраняем имя оригинальной фабрики (нужно для дедупликации в библиотеке).
    make.__name__ = factory.__name__
    return make


# Каталог классовых фабрик с проставленным тегом card_class.
_TAGGED_CLASS_FACTORIES = {
    cls: [_tagged(f, cls) for f in factories]
    for cls, factories in CLASS_FACTORIES.items()
}


def get_pool_for_class(class_name) -> list:
    """Пул выдачи карт для класса: generic + классовые этого класса.
    Используется магазином / сундуком / событиями в забеге."""
    return GENERIC_FACTORIES + _TAGGED_CLASS_FACTORIES.get(class_name, [])


def get_class_cards(class_name) -> list:
    """Только классовые карты класса (для вкладки библиотеки)."""
    return _TAGGED_CLASS_FACTORIES.get(class_name, [])
