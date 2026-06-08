# core/cards/mage.py
# Классовые карты Мага. Идентичность класса — «стихии и комбо»: Маг вешает
# стихийные статусы и детонирует их через комбо-реестр (core/ComboRegistry.py).
# «Закипание» — энейблер ПАР: вешает Мокрый и Горение разом, чтобы следующая
# атака сработала с ×2.0 урона.
#
# Мастерство стихий (кат.4 движок): каждое сработавшее комбо даёт +1 к урону всех
# атак до конца боя (пассив Мага). MasteryEffect — карта-катализатор, дающая
# мастерство напрямую (стартовый разгон движка).
from core.cards.base import Card, DamageEffect, StatusEffect
from core.EffectCalculator import EffectCalculator
from core.rarity import Rarity


# ─── Кирпичи движка Мастерства/Нестабильности (С56, передел Мага) ──────────────
class OverclockEffect:
    """Грань «гамбл/Нестабильность» («Разгон»): заплати % ОТ MAX HP (сквозь щит) →
    +N Мастерства разом. Активная ручка «Гни»: игрок САМ перешагивает порог перегруза
    (mastery≥5 → ×1.5 + эскалирующая %-цена в начале хода). Цена в % → масштаб-инвариантна
    (актуальна на этаже 1 и 100). Ось класса = HP-казино: гэмблишь HP за компаунд."""

    def __init__(self, hp_pct, gain, upgrade_gain):
        self.hp_pct = hp_pct
        self.gain = gain
        self.upgrade_gain = upgrade_gain

    def execute(self, player, enemy, combat_manager, is_upgraded):
        gain = self.upgrade_gain if is_upgraded else self.gain
        cost = int(getattr(player, "max_hp", 0) * self.hp_pct)
        lost = player.lose_hp(cost) if cost > 0 else 0
        player.add_status("mastery", gain, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Разгон: −{lost} HP ({int(self.hp_pct * 100)}% max) → "
                f"+{gain} Мастерства (всего {player.mastery})."
            )


class MasteryScalingDamageEffect:
    """Грань «выжать глубину» («Резонансный разряд»): урон = base + per×Мастерство.
    Читает Мастерство, НЕ тратит (компаунд держится — контраст спендеру Воина). Это
    payoff-карта накопленного Мастерства: масштабируется С НИМ СВЕРХ обычного бонуса
    Мастерства (шаг 2c добавляет свой +Мастерство к ЛЮБОЙ атаке) → разряд = лучший слив
    глубины. Урон через EffectCalculator (перегруз ×1.5/уязвимость учтены)."""

    def __init__(self, base_val, upgrade_val, per_mastery, upgrade_per_mastery):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.per_mastery = per_mastery
        self.upgrade_per_mastery = upgrade_per_mastery

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        per = self.upgrade_per_mastery if is_upgraded else self.per_mastery
        mastery = max(0, getattr(player, "mastery", 0))
        amount = base + per * mastery
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final = EffectCalculator.calculate_damage(
            player, enemy, amount, gm_ref, combat_manager
        )
        enemy.take_damage(final, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Резонансный разряд: {final} урона "
                f"(Мастерство {mastery} → +{per * mastery} базы)."
            )


class MasteryEffect:
    """Накладывает Мастерство стихий на игрока — +N к урону всех атак до конца боя.
    Прямой бустер движка Мага (обычно мастерство копится от комбо-пассива)."""

    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.add_status("mastery", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Мастерство +{amount} (всего: {player.mastery})."
            )


def create_boil():
    """«Закипание» — вешает Мокрый (3) и Горение (3) на цель + урон 5.
    Улучшение: урон 6, статусы по 4 хода. Стоит 1 энергии: сетап стоит дёшево,
    оставляя энергию на атаку-детонатор ПАР в тот же ход."""
    return Card(
        name="Закипание",
        cost=1,
        card_type="attack",
        description="Урон 5(6). Вешает Мокрый 3(4) и Горение 3(4). "
                    "Сетап для комбо ПАР.",
        effects=[
            DamageEffect(5, 6),
            StatusEffect("wet", 3, 4),
            StatusEffect("ignited", 3, 4),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_arcane_focus():
    """«Тайное сосредоточение» — Мастерство 2(3). Чистый энейблер движка Мага:
    разгоняет компаунд урона без ожидания комбо."""
    return Card(
        name="Тайное сосредоточение",
        cost=1,
        card_type="skill",
        description="Мастерство 2(3): усиливает урон всех атак до конца боя.",
        effects=[MasteryEffect(2, 3)],
        rarity=Rarity.UNCOMMON,
    )


def create_elemental_surge():
    """«Стихийный всплеск» — урон 4(6) + Мокрый + Горение + Мастерство 1.
    Гибрид: сетап ПАР (вешает обе стихии) И сразу +1 мастерства. В тот же ход
    атака-детонатор → комбо → ещё +1 мастерства от пассива."""
    return Card(
        name="Стихийный всплеск",
        cost=2,
        card_type="attack",
        description="Урон 4(6). Мокрый 3 + Горение 3 + Мастерство 1.",
        effects=[
            DamageEffect(4, 6),
            StatusEffect("wet", 3, 3),
            StatusEffect("ignited", 3, 3),
            MasteryEffect(1, 1),
        ],
        rarity=Rarity.RARE,
    )
