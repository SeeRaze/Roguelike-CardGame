# core/cards/synergy.py
# СИНЕРГИЯ ОБЩЕГО ПУЛА (Блок 2, С65) — нейтральные generic-карты, углубляющие
# взаимодействие 6 канон-стихий. Мост кросс-классовости: стихии = статусы на враге,
# класс-агностичны (одну половинку вешает класс А, другую — класс Б → комбо общее).
# Тут живут: комбо-сетапы (обе половинки новой пары в одной карте — on-ramp к
# ComboRegistry), достройка decomp (тонко поддержанной стихии) и чистое топливо драфта.
# Все карты LOCKED (награда за прогресс). Числа = ЗАГЛУШКИ (баланс-капстоун калибрует
# позже). Чистый слой — без хуков в ядро.
from core.cards.base import (
    Card, StatusEffect, DecompEffect, DrawEffect, EnergyEffect,
)
from core.EffectCalculator import EffectCalculator
from core.rarity import Rarity
import random

# 6 канон-стихий (StatusRegistry), С65 — закреплены под сеттинг, НЕ расширяем:
# legacy=DoT, coffee=уязвимость, shortcircuit=детонатор, tox=ослабление,
# leak=утечка, decomp=окно. Это НЕ ось-статусы (mastery/discipline) и не
# duration-нестихии (stunned/heal_block). Источник кросс-элемент payoff'ов ниже.
ELEMENT_KEYS = ("legacy", "coffee", "shortcircuit", "tox", "leak", "decomp")


# ─── ЭФФЕКТ-КИРПИЧИ движок-четвёрки (Блок 2, С65) ────────────────────────────
def _deal(player, enemy, raw, combat_manager):
    """Нанести raw урона через единый EffectCalculator (комбо/уязвимость/ковка
    применяются как у обычной атаки). Зеркало base.DamageEffect."""
    gm_ref = combat_manager.gm if combat_manager is not None else None
    final = EffectCalculator.calculate_damage(player, enemy, raw, gm_ref, combat_manager)
    enemy.take_damage(final, attacker=player, combat_manager=combat_manager)
    if combat_manager:
        combat_manager.add_log_message(f" -> {enemy.name} получает {final} урона.")
    return final


class DecompPayoffDamageEffect:
    """«Дамп памяти»: payoff окна decomp. Базовый урон + бонус, если на цели висит
    Декомпиляция (вскрытое окно). Бонус вшит ДО EffectCalculator → комбо/уязвимость
    множат всю атаку целиком (большое видимое число)."""
    def __init__(self, base_val, upgrade_val, bonus_base, bonus_upgrade):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.bonus_base = bonus_base
        self.bonus_upgrade = bonus_upgrade

    def execute(self, player, enemy, combat_manager, is_upgraded):
        raw = self.upgrade_val if is_upgraded else self.base_val
        if enemy.get_status("decomp") > 0:
            raw += self.bonus_upgrade if is_upgraded else self.bonus_base
            if combat_manager:
                combat_manager.add_log_message(
                    " -> Дамп памяти: окно decomp вскрыто (+урон)."
                )
        _deal(player, enemy, raw, combat_manager)


class SpreadScalingDamageEffect:
    """«Технический регресс»: урон растёт за каждую РАЗНУЮ стихию на цели (награда за
    «размазывание» — разные классы вешают разные стихии = кросс-классовость). Бонус
    вшит ДО EffectCalculator."""
    def __init__(self, base_val, upgrade_val, per_base, per_upgrade):
        self.base_val = base_val
        self.upgrade_val = upgrade_val
        self.per_base = per_base
        self.per_upgrade = per_upgrade

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        per = self.per_upgrade if is_upgraded else self.per_base
        count = sum(1 for k in ELEMENT_KEYS if enemy.get_status(k) > 0)
        raw = base + per * count
        if combat_manager and count:
            combat_manager.add_log_message(
                f" -> Технический регресс: {count} стихи(й) на цели (+{per*count})."
            )
        _deal(player, enemy, raw, combat_manager)


class DoubleElementStacksEffect:
    """«Контроль версий»: удваивает ВСЕ стихийные стаки на цели (включая shortcircuit —
    может протолкнуть детонатор за порог → авто-детонация в фазе врага). Большой
    видимый свинг (north-star), окупает RARE+locked. Duration-стихия decomp тоже
    удваивается по длительности."""
    def __init__(self, *_):
        pass

    def execute(self, player, enemy, combat_manager, is_upgraded):
        doubled = []
        for k in ELEMENT_KEYS:
            cur = enemy.get_status(k)
            if cur > 0:
                enemy.set_status(k, cur * 2)
                doubled.append(k)
        if combat_manager and doubled:
            combat_manager.add_log_message(
                f" -> Контроль версий: удвоены стихии ({', '.join(doubled)})."
            )


class RandomElementAoEEffect:
    """«Веерная рассылка»: каждому живому врагу — N стак(ов) СЛУЧАЙНОЙ стихии (из 6).
    Хаос-AoE: непредсказуемый посев под комбо/детонации (дофамин/иллюзия авторства,
    north-star). Рандом per-enemy (максимум хаоса)."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        n = self.upgrade_val if is_upgraded else self.base_val
        if combat_manager is not None:
            targets = [e for e in getattr(combat_manager, "enemies", [enemy])
                       if e.hp > 0]
        else:
            targets = [enemy]
        for t in targets:
            elem = random.choice(ELEMENT_KEYS)
            t.add_status(elem, n, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f" -> Веерная рассылка: {elem} {n} на {t.name}."
                )



def create_code_archaeology():
    """«Археология кода» — комбо-сетап ВСКРЫТЫЙ LEGACY (decomp+legacy) в одной карте.
    Вскрыл старый модуль → его техдолг готов детонировать под следующей атакой."""
    return Card(
        name="Археология кода",
        cost=1,
        card_type="skill",
        description="Декомпиляция 1(2) х. Накладывает Legacy-код 4(6).",
        effects=[
            DecompEffect(1, 2),
            StatusEffect("legacy", 4, 6),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_bottleneck():
    """«Бутылочное горлышко» — комбо-сетап ДЕГРАДАЦИЯ (tox+leak). Процесс заткнулся:
    токсичный менеджмент + утечка памяти = система гниёт под следующей атакой."""
    return Card(
        name="Бутылочное горлышко",
        cost=1,
        card_type="skill",
        description="Накладывает Токсичный менеджмент 2(3) и Утечку памяти 2(3).",
        effects=[
            StatusEffect("tox", 2, 3),
            StatusEffect("leak", 2, 3),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_spilled_espresso():
    """«Пролитый эспрессо» — комбо-сетап ХРУПКОСТЬ (coffee+decomp). Залил кофе на
    вскрытый код: уязвимость + заглушенный щит = максимальная хрупкость цели."""
    return Card(
        name="Пролитый эспрессо",
        cost=1,
        card_type="skill",
        description="Накладывает Разлитый кофе 2(3). Декомпиляция 1(2) х.",
        effects=[
            StatusEffect("coffee", 2, 3),
            DecompEffect(1, 2),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_breakpoint():
    """«Точка останова» — дешёвый опенер окна эксплойта + картдвижение. Достройка
    decomp: ставит окно (−щит/глушит генерацию) и сразу подаёт топливо в руку."""
    return Card(
        name="Точка останова",
        cost=1,
        card_type="skill",
        description="Декомпиляция 2(3) х. Добор 1(2).",
        effects=[
            DecompEffect(2, 3),
            DrawEffect(1, 2),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_planning():
    """«Планёрка» — чистое топливо драфта (картдвижение + рамп). Без стихий: смазка
    движка, разгоняет любую сборку. (Имя «Стендап» занято баффом Оптимизации.)"""
    return Card(
        name="Планёрка",
        cost=1,
        card_type="skill",
        description="Добор 2. +1(2) энергии в этот ход.",
        effects=[
            DrawEffect(2, 2),
            EnergyEffect(1, 2),
        ],
        rarity=Rarity.UNCOMMON,
    )


def create_monitoring():
    """«Мониторинг» — leak-движок в одной карте: вешает Утечку и тут же прокручивает
    руку. Добор триггерит свежую Утечку (N × размер руки урона) → самодостаточный
    payoff стихии Утечки. Порядок эффектов важен: сперва Утечка, затем добор."""
    return Card(
        name="Мониторинг",
        cost=1,
        card_type="skill",
        description="Накладывает Утечку памяти 2(3). Добор 2.",
        effects=[
            StatusEffect("leak", 2, 3),
            DrawEffect(2, 2),
        ],
        rarity=Rarity.RARE,
    )


# ─── ДВИЖОК-ЧЕТВЁРКА (Блок 2, С65): карты на эффект-кирпичах выше ─────────────
def create_memory_dump():
    """«Дамп памяти» (RARE/attack): payoff окна decomp — тяжёлый удар, ещё тяжелее
    по вскрытой (декомпилированной) цели."""
    return Card(
        name="Дамп памяти",
        cost=2,
        card_type="attack",
        description="Урон 6(8). Если на цели Декомпиляция — ещё +6(8).",
        effects=[DecompPayoffDamageEffect(6, 8, 6, 8)],
        rarity=Rarity.RARE,
    )


def create_tech_regression():
    """«Технический регресс» (RARE/attack): кросс-элемент payoff — урон за каждую
    разную стихию на цели (награда за размазывание = кросс-классовость)."""
    return Card(
        name="Технический регресс",
        cost=2,
        card_type="attack",
        description="Урон 5(7), +3(4) за каждую разную стихию на цели.",
        effects=[SpreadScalingDamageEffect(5, 7, 3, 4)],
        rarity=Rarity.RARE,
    )


def create_version_control():
    """«Контроль версий» (RARE/skill): удваивает все стихийные стаки на цели —
    большой видимый множитель под выстроенную сборку (вкл. детонатор shortcircuit)."""
    return Card(
        name="Контроль версий",
        cost=1,
        card_type="skill",
        description="Удваивает все стихийные стаки на цели.",
        effects=[DoubleElementStacksEffect()],
        rarity=Rarity.RARE,
    )


def create_fan_out():
    """«Веерная рассылка» (UNC/skill): 1(2) стак случайной стихии каждому врагу —
    хаос-AoE, сеет почву под комбо/детонации непредсказуемо."""
    return Card(
        name="Веерная рассылка",
        cost=1,
        card_type="skill",
        description="Накладывает 1(2) стак случайной стихии каждому врагу.",
        effects=[RandomElementAoEEffect(1, 2)],
        rarity=Rarity.UNCOMMON,
    )
