# core/fusion.py
# CARD FUSION — чистый МЕХАНИЗМ слияния двух карт в «Глитч-карту» (§2, фундамент Химика).
#
# ПРИНЦИП (С49): механизм УНИВЕРСАЛЕН и ИНЕРТЕН — существует всегда, но никто его не зовёт,
# пока класс (Химик) / реликвия не активирует ДОСТУП (как `positioning_enabled` у позиционки).
# Для 95% игры и кода фьюжна как будто нет → баланс контейнеризован одним классом.
#
# Это ЧИСТЫЙ модуль: только данные + пьюр-функции. Без pygame, без player/combat, без
# побочек → тестируется без SDL. Источники НЕ мутируются — возвращается новый Card.
#
# Развилки закрыты с юзером (см. _card_fusion_design.md «✅ Решения»):
# • стоимость = max(a,b) с полом 1 — ТОРМОЗ фьюжна в РЕСУРСЕ класса (Реагент), а не в цене
#   розыгрыша (max+1 при энергобюджете ~3 давал неиграбельные кирпичи; max-пол-1 всегда
#   играбелен + дофамин эффективности + пол убивает 0-cost абуз);
# • эффекты — КОНКАТЕНАЦИЯ (ноль спец-кода на тип → эмерджентные комбо);
# • прокачка СБРОШЕНА (upgraded=False) — наследование уровней/тегов ковки делает слой
#   триггера (этап 2), не этот чистый механизм.
from core.cards.base import Card
from core.rarity import Rarity

# Пол стоимости Глитч-карты (анти-абуз 0-cost). Ручка баланса — _balance_knobs.md.
FUSED_COST_FLOOR = 1

# Кап числа эффектов на Глитч-карте — ГАРД-РЕЙЛ против ЦЕПНОГО фьюжна (Глитч + ещё карта
# + ещё…), который иначе растил бы стопку эффектов без предела → переполнение чисел/UI.
# Ручка — _balance_knobs.md.
MAX_FUSED_EFFECTS = 6

# Явный порядок тиров редкости: Rarity — это Enum СТРОК (не упорядочен), поэтому
# max(rarity_a, rarity_b) НЕ работает напрямую. Индекс в этом кортеже = «высота» тира.
_RARITY_ORDER = (
    Rarity.COMMON, Rarity.UNCOMMON, Rarity.RARE, Rarity.EPIC, Rarity.LEGENDARY,
)


def can_fuse(card_a, card_b) -> bool:
    """Можно ли слить две карты: суммарное число эффектов не превышает MAX_FUSED_EFFECTS.
    Предикат для ВЫЗЫВАТЕЛЯ (отказать в слиянии / погасить кнопку UI) — enforcement
    делает слой триггера; `fuse_cards` защитно поднимает ошибку как страховку."""
    return len(card_a.effects) + len(card_b.effects) <= MAX_FUSED_EFFECTS


def fused_cost(card_a, card_b) -> int:
    """Стоимость Глитч-карты: max(стоимостей) с полом FUSED_COST_FLOOR.
    Не превышает дороже из источников → Глитч всегда играбелен в пределах энергобюджета.
    Мощность фьюжна тормозит РЕСУРС класса (Реагент), а не эта цена."""
    return max(card_a.cost, card_b.cost, FUSED_COST_FLOOR)


def higher_rarity(rarity_a, rarity_b):
    """Более высокий из двух тиров редкости (по явному порядку _RARITY_ORDER).
    Неизвестный тир считается нижайшим (индекс −1) → безопасный фолбэк."""
    ia = _RARITY_ORDER.index(rarity_a) if rarity_a in _RARITY_ORDER else -1
    ib = _RARITY_ORDER.index(rarity_b) if rarity_b in _RARITY_ORDER else -1
    return rarity_a if ia >= ib else rarity_b


def _fused_name(card_a, card_b) -> str:
    """Имя Глитча из БАЗОВЫХ имён источников (без апгрейд-суффикса «+», т.к. прокачка
    Глитча сброшена)."""
    a = card_a.name.rstrip("+")
    b = card_b.name.rstrip("+")
    return f"{a}+{b}"


def _fused_type(card_a, card_b) -> str:
    """Тип Глитча: общий, если совпадает; иначе «attack» (большинство гибридов бьют —
    нужно для реликвий, ловящих первую атаку)."""
    if card_a.card_type == card_b.card_type:
        return card_a.card_type
    return "attack"


def _fused_description(card_a, card_b) -> str:
    """Описание Глитча — склейка описаний источников (UI-косметика)."""
    return f"{card_a.description} {card_b.description}".strip()


def fuse_cards(card_a, card_b) -> Card:
    """Слить две карты в «Глитч-карту». ЧИСТО: возвращает НОВЫЙ Card; источники не
    мутирует, player/combat не трогает.

    Состав (развилки закрыты С49):
    - эффекты — КОНКАТЕНАЦИЯ списков (порядок: сначала a, затем b);
    - стоимость — fused_cost (max, пол 1); редкость — выше из двух; тип — общий/«attack»;
    - изгнание — a или b; прокачка СБРОШЕНА (upgraded=False, базовые значения эффектов).

    Метит результат: `is_fused=True` (UI/гард-рейлы) + `fused_from=(имя_a, имя_b)`.
    Эффекты переиспользуются по ссылке — кирпичи неизменяемая конфигурация (base_val/
    upgrade_val), общее владение безопасно.

    Защитно поднимает ValueError при превышении MAX_FUSED_EFFECTS (гард-рейл цепного
    фьюжна) — вызыватель обязан заранее проверить `can_fuse`; это страховка контракта."""
    if not can_fuse(card_a, card_b):
        raise ValueError(
            f"Слияние превысит кап эффектов ({MAX_FUSED_EFFECTS}): "
            f"{len(card_a.effects)} + {len(card_b.effects)}"
        )
    fused = Card(
        name=_fused_name(card_a, card_b),
        cost=fused_cost(card_a, card_b),
        card_type=_fused_type(card_a, card_b),
        description=_fused_description(card_a, card_b),
        effects=list(card_a.effects) + list(card_b.effects),
        rarity=higher_rarity(card_a.rarity, card_b.rarity),
        exile=bool(getattr(card_a, "exile", False) or getattr(card_b, "exile", False)),
    )
    fused.is_fused = True
    fused.fused_from = (card_a.name, card_b.name)
    return fused
