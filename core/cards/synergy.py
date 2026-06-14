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
from core.rarity import Rarity


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
