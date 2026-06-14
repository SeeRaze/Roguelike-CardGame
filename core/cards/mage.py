# core/cards/mage.py
# Классовые карты Мага. Идентичность класса — «стихии и комбо»: Маг вешает
# стихийные статусы и детонирует их через комбо-реестр (core/ComboRegistry.py).
# «Залить в прод» — энейблер ПАР: вешает Разлитый кофе и Legacy-код разом, чтобы
# следующая атака сработала с ×2.0 урона (комбо ХОТФИКС).
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
                f" -> Автопилот: −{lost} HP ({int(self.hp_pct * 100)}% max) → "
                f"+{gain} Мастерства (всего {player.mastery})."
            )


class MasteryScalingDamageEffect:
    """Грань «выжать глубину» («Сгенерить фичу»): урон = base × (1 + mult×Мастерство)
    — МУЛЬТИПЛИКАТИВНО (С57, единый формат с Воином: флат per×mastery тонул в эндгейме).
    Читает Мастерство, НЕ тратит (компаунд держится — контраст спендеру Воина). payoff
    поверх пассива: шаг 2c добавит свой +Мастерство, перегруз 4c домножит → выпуск =
    лучший слив глубины. Множитель масштаб-инвариантен. Числа = ЗАГЛУШКИ под капстоун."""

    def __init__(self, base_val, upgrade_val, mult_per, upgrade_mult_per):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.mult_per = mult_per                 # доля множителя за стак Мастерства
        self.upgrade_mult_per = upgrade_mult_per

    def projected_damage(self, player, is_upgraded):
        """База урона ДО общих модификаторов (для проекции на карте) = base × текущий
        множитель Мастерства. Совпадает с amount в execute → preview == фактический удар."""
        base = self.upgrade_val if is_upgraded else self.base_val
        mult_per = self.upgrade_mult_per if is_upgraded else self.mult_per
        mastery = max(0, getattr(player, "mastery", 0)) if player else 0
        return int(base * (1.0 + mult_per * mastery))

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
                f" -> Сгенерить фичу: {final} урона "
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


class MasterySpenderDamageEffect:
    """Грань «слей глубину» («Релиз в пятницу»): СЖИГАЕТ ВСЁ Мастерство и наносит урон
    = base × (1 + mult×сожжено) — МУЛЬТИПЛИКАТИВНО (единый формат со спендером Воина
    «Критический баг»). Спендер-противовес компаунду «Сгенерить фичу» (та ЧИТАЕТ, не жжёт):
    выбор «копи (Сгенерить фичу) vs слей (Релиз в пятницу)». Трата ОБНУЛЯЕТ Мастерство ДО
    EffectCalculator → шаг 2c (+N урона за стак) И шаг 4b (перегруз-множитель) не задваивают
    и не доплачивают этому удару: своя ×-формула карты = весь payoff. ПОБОЧКА (фича-противовес,
    апрув Жеки): слив роняет Мастерство ниже порога → гасит HP-искру следующего хода
    («обналичь + остынь»). Вне Мастерства → просто base. Числа = ЗАГЛУШКИ под капстоун."""

    def __init__(self, base_val, upgrade_val, mult_per, upgrade_mult_per):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.mult_per = mult_per                 # доля множителя за каждый сожжённый стак
        self.upgrade_mult_per = upgrade_mult_per

    def projected_damage(self, player, is_upgraded):
        """База урона ДО общих модификаторов (для проекции на карте) = base × текущий
        множитель Мастерства. Совпадает с amount в execute → preview == фактический удар."""
        base = self.upgrade_val if is_upgraded else self.base_val
        mult_per = self.upgrade_mult_per if is_upgraded else self.mult_per
        spent = max(0, getattr(player, "mastery", 0)) if player else 0
        return int(base * (1.0 + mult_per * spent))

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        mult_per = self.upgrade_mult_per if is_upgraded else self.mult_per
        spent = max(0, getattr(player, "mastery", 0))
        player.set_status("mastery", 0)          # сжечь стак ДО расчёта (без задвоя 2c/4b)
        mult = 1.0 + mult_per * spent
        amount = int(base * mult)
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final = EffectCalculator.calculate_damage(
            player, enemy, amount, gm_ref, combat_manager
        )
        enemy.take_damage(final, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Релиз в пятницу: {final} урона "
                f"(сожжено {spent} Мастерства → ×{mult:.2f}; перегруз сброшен)."
            )


class MasteryScaledHealEffect:
    """Грань «сустейн» («Дебаг-сессия»): хил = base + per×(текущее Мастерство), Мастерство
    НЕ тратит. Зеркало Тестировщикова «Чеклиста» (DisciplineScaledShieldEffect), но по оси
    HP — ресурсу Мага, а не щита: компенсирует HP-churn/искру перегруза. Чем глубже понимание
    (Мастерство), тем быстрее чинишь баг. ⚠️ Баланс: per-за-стак держать скромным, иначе
    хрупкий HP-churn превращается в неубиваемость. Числа = ЗАГЛУШКИ под капстоун."""

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
        healed = player.heal(amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Дебаг-сессия: +{healed} HP "
                f"(база {base} + {per}×{mastery} Мастерства)."
            )


def create_overclock():
    """«Автопилот» — заплати 10% max HP → +3(4) Мастерства разом. Грань гамбл/Нестабильность:
    активная ручка «Гни» — игрок САМ перешагивает порог перегруза (≥5 → ×1.5 + эскалир.
    %-цена/ход). Ось HP-казино: гонишь не глядя, выгораешь. Не закрывает билд: Мастерство
    копится и от комбо. UNCOMMON."""
    return Card(
        name="Автопилот",
        cost=1,
        card_type="skill",
        description="Заплатите 10% max HP. +3(4) Мастерства.",
        effects=[OverclockEffect(0.10, 3, 4)],
        rarity=Rarity.UNCOMMON,
    )


def create_resonant_discharge():
    """«Сгенерить фичу» — урон 6(9) ×(1 + 25%(35%) за стак Мастерства). Грань «выжать
    глубину»: payoff накопленного Мастерства, НЕ тратит его (компаунд цел). Мультипликатив
    (С57): пик растёт со стаком и домножается перегрузом/ковкой, не тонет. UNCOMMON."""
    return Card(
        name="Сгенерить фичу",
        cost=2,
        card_type="attack",
        description="Урон 6(9) ×(1 + 25%(35%) за каждый стак Мастерства). Мастерство не тратится.",
        effects=[MasteryScalingDamageEffect(6, 9, 0.25, 0.35)],
        rarity=Rarity.UNCOMMON,
    )


def create_boil():
    """«Залить в прод» — вешает Разлитый кофе (3) и Legacy-код (3) на цель + урон 5.
    Улучшение: урон 6, статусы по 4 хода. Стоит 1 энергии: сетап стоит дёшево,
    оставляя энергию на атаку-детонатор ХОТФИКС в тот же ход. Залил не глядя — техдолг
    потом тушить."""
    return Card(
        name="Залить в прод",
        cost=1,
        card_type="attack",
        description="Урон 5(6). Вешает Разлитый кофе 3(4) и Legacy-код 3(4). "
                    "Сетап для комбо ХОТФИКС.",
        effects=[
            DamageEffect(5, 6),
            StatusEffect("coffee", 3, 4),
            StatusEffect("legacy", 3, 4),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_arcane_focus():
    """«Удачный промпт» — Мастерство 2(3). Чистый энейблер движка вайб-кодера:
    разгоняет компаунд урона без ожидания комбо."""
    return Card(
        name="Удачный промпт",
        cost=1,
        card_type="skill",
        description="Мастерство 2(3): усиливает урон всех атак до конца боя.",
        effects=[MasteryEffect(2, 3)],
        rarity=Rarity.UNCOMMON,
    )


def create_elemental_surge():
    """«Вайб-сессия» — урон 4(6) + Кофе + Legacy + Мастерство 1.
    Гибрид: сетап ХОТФИКС (вешает обе стихии) И сразу +1 мастерства. В тот же ход
    атака-детонатор → комбо → ещё +1 мастерства от пассива. Накодил на вайбе — и фича,
    и техдолг разом."""
    return Card(
        name="Вайб-сессия",
        cost=2,
        card_type="attack",
        description="Урон 4(6). Разлитый кофе 3 + Legacy-код 3 + Мастерство 1.",
        effects=[
            DamageEffect(4, 6),
            StatusEffect("coffee", 3, 3),
            StatusEffect("legacy", 3, 3),
            MasteryEffect(1, 1),
        ],
        rarity=Rarity.RARE,
    )


def create_friday_release():
    """«Релиз в пятницу» — урон 8(11) ×(1 + 40%(55%) за каждый сожжённый стак Мастерства),
    затем СЖИГАЕТ всё Мастерство → 0. Спендер-противовес компаунду «Сгенерить фичу»
    (выбор «копи vs слей»). Слив роняет ниже порога перегруза → гасит HP-искру след. хода
    (cool-down «обналичь + остыть» = противовес мощному свингу). RARE."""
    return Card(
        name="Релиз в пятницу",
        cost=2,
        card_type="attack",
        description="Урон 8(11) ×(1 + 40%(55%) за каждый стак Мастерства). "
                    "Сжигает всё Мастерство.",
        effects=[MasterySpenderDamageEffect(8, 11, 0.40, 0.55)],
        rarity=Rarity.RARE,
    )


def create_debug_session():
    """«Дебаг-сессия» — лечит 5(7) + 1(2) за каждый стак Мастерства. Мастерство не тратит.
    Классовый сустейн хрупкого HP-churn: компенсирует искру перегруза, масштабируется
    с глубиной билда. Зеркало Тестировщикова «Чеклиста» по оси HP. UNCOMMON."""
    return Card(
        name="Дебаг-сессия",
        cost=1,
        card_type="skill",
        description="Лечит 5(7) + 1(2) за каждый стак Мастерства. Мастерство не тратится.",
        effects=[MasteryScaledHealEffect(5, 7, 1, 2)],
        rarity=Rarity.UNCOMMON,
    )
