# core/cards/cleave.py
# ПОЗИЦИОННЫЕ AoE-КИРПИЧИ — потребители 2D-субстрата позиционки (§1 после С47/С48).
#
# Субстрат дал пьюр-ридеры (core/positioning.py: neighbors/column/same_rank), но до §1
# их никто не дёргал — ридеры были инертны. Эти кирпичи их оживляют: урон по геометрии
# сетки (соседи / колонка / ряд). Class-agnostic; позиция цели начинает РЕШАТЬ.
#
# Все кирпичи НАСЛЕДУЮТ DamageEffect (через _PositionalAoEEffect) → isinstance-проверки
# (синергийный слой бота, снимок hand_attack, классификатор карт) видят атаку без правок.
# Вторичные цели — поверх первичного удара. Позиционка off / нет позиции у цели →
# вторичных целей нет → ведёт себя как обычный DamageEffect (single-target fallback,
# baseline зелёный).
from core.cards.base import Card, DamageEffect
from core.EffectCalculator import EffectCalculator
from core.rarity import Rarity


class _PositionalAoEEffect(DamageEffect):
    """База позиционных AoE: цель — ПОЛНЫЙ урон (наследует DamageEffect), вторичные
    цели (по геометрии сетки) — `splash_ratio` от базового, через EffectCalculator
    (уязвимость/слабость/шок вторичной цели учитываются).

    Подкласс задаёт `LABEL` (тег в логе) + `_secondary_targets(enemy, cm)` (геометрия).
    Вторичные цели ПУСТЫ без позиции → single-target fallback (регресс-нейтрально)."""

    LABEL = "AoE"
    SPLASH_RATIO = 0.5

    def __init__(self, base_val, upgrade_val, splash_ratio=None):
        super().__init__(base_val, upgrade_val)
        self.splash_ratio = self.SPLASH_RATIO if splash_ratio is None else splash_ratio

    def _secondary_targets(self, enemy, combat_manager) -> list:
        """Список вторичных целей по геометрии сетки. База — пусто (переопределяется)."""
        return []

    def execute(self, player, enemy, combat_manager, is_upgraded):
        # Первичный удар по цели — полный урон + лог (наследованная логика).
        super().execute(player, enemy, combat_manager, is_upgraded)
        if combat_manager is None:
            return
        targets = self._secondary_targets(enemy, combat_manager)
        if not targets:
            return
        base = self.upgrade_val if is_upgraded else self.base_val
        dmg = int(base * self.splash_ratio)
        if dmg <= 0:
            return
        gm_ref = combat_manager.gm
        for tgt in targets:
            final = EffectCalculator.calculate_damage(
                player, tgt, dmg, gm_ref, combat_manager
            )
            tgt.take_damage(final, attacker=player, combat_manager=combat_manager)
            combat_manager.add_log_message(
                f" -> {self.LABEL}: {tgt.name} получает {final} урона."
            )


class SplashDamageEffect(_PositionalAoEEffect):
    """Цель + сплеш по ОРТОГОНАЛЬНО соседним клеткам (манхэттен-1, диагональ — не
    сосед). Дёргает `neighbors`. Позиция цели решает: центр строя задевает больше."""

    LABEL = "Мердж-конфликт"

    def _secondary_targets(self, enemy, combat_manager):
        from core.positioning import neighbors
        return neighbors(enemy, combat_manager.enemies)


class ColumnStrikeEffect(_PositionalAoEEffect):
    """Цель + вся её КОЛОНКА (вертикальный ряд линии: фронт+тыл). Дёргает `column`.
    ПРОБИВАЕТ перехват: достаёт прикрытый тыл через фронт той же линии (анти-черепаха).
    Полным уроном (splash_ratio=1.0): колонка узкая (≤1 вторичная цель в Т-раскладке)."""

    LABEL = "SQL-инъекция"
    SPLASH_RATIO = 1.0

    def _secondary_targets(self, enemy, combat_manager):
        from core.positioning import cell, column
        if cell(enemy) is None:          # нет полной позиции → fallback одиночная цель
            return []
        line = getattr(enemy, "line", None)
        return [c for c in column(line, combat_manager.enemies)
                if c is not enemy and c.hp > 0]


class RankStrikeEffect(_PositionalAoEEffect):
    """Цель + весь её РЯД (горизонталь: весь ФРОНТ или весь ТЫЛ). Дёргает `same_rank`.
    Классический sweep по шеренге; вторичные — `splash_ratio`(0.5)."""

    LABEL = "Ответить всем"

    def _secondary_targets(self, enemy, combat_manager):
        from core.positioning import same_rank
        rank = getattr(enemy, "rank", None)
        if rank is None:                 # нет ранга → fallback одиночная цель
            return []
        return [c for c in same_rank(rank, combat_manager.enemies)
                if c is not enemy and c.hp > 0]


def create_cleaving_strike():
    """«Мердж-конфликт» — урон 6(8) цели + половина по СОСЕДНИМ врагам на сетке.
    Демонстрационный носитель сплеша (generic). Награда за позиционирование: бей по
    центру вражеского строя — заденешь больше."""
    return Card(
        name="Мердж-конфликт",
        cost=1,
        card_type="attack",
        description="Урон 6(8) цели + половина по соседним врагам (по сетке).",
        effects=[SplashDamageEffect(6, 8)],
        rarity=Rarity.COMMON,
    )


def create_piercing_thrust():
    """«SQL-инъекция» — урон 6(8) цели + полный по ВСЕЙ её колонке (фронт+тыл линии).
    Пробивает перехват: проходит сквозь фронт(енд) и достаёт бэк. Анти-черепаха (generic)."""
    return Card(
        name="SQL-инъекция",
        cost=2,
        card_type="attack",
        description="Урон 6(8) цели и всем врагам в её колонке (фронт+тыл линии).",
        effects=[ColumnStrikeEffect(6, 8)],
        rarity=Rarity.UNCOMMON,
    )


def create_wide_swing():
    """«Ответить всем» — урон 7(9) цели + половина по всему её РЯДУ (вся шеренга
    фронта/тыла). Каждый, кто был в копии, получил (generic)."""
    return Card(
        name="Ответить всем",
        cost=2,
        card_type="attack",
        description="Урон 7(9) цели + половина по всему её ряду (шеренге).",
        effects=[RankStrikeEffect(7, 9)],
        rarity=Rarity.UNCOMMON,
    )
