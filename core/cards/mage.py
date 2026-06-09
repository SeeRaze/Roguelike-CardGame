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
    """Грань «выжать глубину» («Резонансный разряд»): урон = base × (1 + mult×Мастерство)
    — МУЛЬТИПЛИКАТИВНО (С57, единый формат с Воином: флат per×mastery тонул в эндгейме).
    Читает Мастерство, НЕ тратит (компаунд держится — контраст спендеру Воина). payoff
    поверх пассива: шаг 2c добавит свой +Мастерство, перегруз 4c домножит → разряд =
    лучший слив глубины. Множитель масштаб-инвариантен. Числа = ЗАГЛУШКИ под капстоун."""

    def __init__(self, base_val, upgrade_val, mult_per, upgrade_mult_per):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.mult_per = mult_per                 # доля множителя за стак Мастерства
        self.upgrade_mult_per = upgrade_mult_per

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        mult_per = self.upgrade_mult_per if is_upgraded else self.mult_per
        mastery = max(0, getattr(player, "mastery", 0))
        mult = 1.0 + mult_per * mastery
        amount = int(base * mult)
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final = EffectCalculator.calculate_damage(
            player, enemy, amount, gm_ref, combat_manager
        )
        enemy.take_damage(final, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Резонансный разряд: {final} урона "
                f"(Мастерство {mastery} → ×{mult:.2f} базы)."
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


def create_overclock():
    """«Разгон» — заплати 10% max HP → +3(4) Мастерства разом. Грань гамбл/Нестабильность:
    активная ручка «Гни» — игрок САМ перешагивает порог перегруза (≥5 → ×1.5 + эскалир.
    %-цена/ход). Ось HP-казино. Не закрывает билд: Мастерство копится и от комбо. UNCOMMON."""
    return Card(
        name="Разгон",
        cost=1,
        card_type="skill",
        description="Заплатите 10% max HP. +3(4) Мастерства.",
        effects=[OverclockEffect(0.10, 3, 4)],
        rarity=Rarity.UNCOMMON,
    )


def create_resonant_discharge():
    """«Резонансный разряд» — урон 6(9) ×(1 + 25%(35%) за стак Мастерства). Грань «выжать
    глубину»: payoff накопленного Мастерства, НЕ тратит его (компаунд цел). Мультипликатив
    (С57): пик растёт со стаком и домножается перегрузом/ковкой, не тонет. UNCOMMON."""
    return Card(
        name="Резонансный разряд",
        cost=2,
        card_type="attack",
        description="Урон 6(9) ×(1 + 25%(35%) за каждый стак Мастерства). Мастерство не тратится.",
        effects=[MasteryScalingDamageEffect(6, 9, 0.25, 0.35)],
        rarity=Rarity.UNCOMMON,
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
