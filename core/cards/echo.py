# core/cards/echo.py
# Карты механики «Эхо» (ретриггер). Эхо — статус ИГРОКА (is_stack): каждая
# разыгранная карта срабатывает повторно за каждый заряд Эха, после чего заряд
# тратится. Это чистый множитель кат.4: Эхо × сильная карта = взрывной ход.
#
# Ретриггер-хук — в CombatManager.play_card_by_index (проверяет player.echo).
#
# Трио:
#   «Резонанс»   — чистый энейблер: Эхо 2(3).
#   «Отзвук»     — гибрид: урон + Эхо 1.
#   «Каскад»     — пейофф: крупный урон, если есть Эхо — не тратит заряд (RARE).
from core.cards.base import Card, DamageEffect
from core.rarity import Rarity


class EchoEffect:
    """Накладывает Эхо (статус игрока) — каждая следующая разыгранная карта
    срабатывает повторно за каждый заряд. Не в _ELEMENTAL_KEYS — не блокируется
    барьером Мага (эхо не стихия, а мета-механика)."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.add_status("echo", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Эхо +{amount} (всего: {player.echo})."
            )


class EchoPayoffEffect:
    """Урон ×2 если у игрока есть Эхо. Эхо НЕ тратится — это payoff карта,
    а не потребитель. Даёт бонус за НАЛИЧИЕ эха, не снимая его."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        from core.EffectCalculator import EffectCalculator
        base = self.upgrade_val if is_upgraded else self.base_val
        if player.echo > 0:
            base *= 2
            if combat_manager:
                combat_manager.add_log_message(
                    f"[ЭХО] Каскад усилен: урон ×2 (={base})!"
                )
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final_dmg = EffectCalculator.calculate_damage(
            player, enemy, base, gm_ref, combat_manager
        )
        enemy.take_damage(final_dmg, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> {enemy.name} получает {final_dmg} урона."
            )


def create_echo_resonance():
    """«Резонанс» — чистый энейблер: Эхо 2(3) за 1 энергию. Готовит следующий
    ход под двойной/тройной удар."""
    return Card(
        name="Резонанс",
        cost=1,
        card_type="skill",
        description="Эхо 2(3): следующая карта срабатывает повторно ×2(×3).",
        effects=[EchoEffect(2, 3)],
        rarity=Rarity.UNCOMMON,
    )


def create_echo_strike():
    """«Отзвук» — урон 4(6) + Эхо 1. Гибрид: бьёт сейчас и заряжает ретриггер
    под следующую карту."""
    return Card(
        name="Отзвук",
        cost=1,
        card_type="attack",
        description="Урон 4(6). Эхо 1: следующая карта срабатывает дважды.",
        effects=[DamageEffect(4, 6), EchoEffect(1, 1)],
    )


def create_echo_cascade():
    """«Каскад» — урон 8(12), ×2 если игрок под Эхом (не тратит заряд).
    Payoff: бонус за НАЛИЧИЕ эха, сам эхо остаётся для ретриггера."""
    return Card(
        name="Каскад",
        cost=2,
        card_type="attack",
        description="Урон 8(12). Если есть Эхо — урон ×2 (эхо не тратится).",
        effects=[EchoPayoffEffect(8, 12)],
        rarity=Rarity.RARE,
    )
