# core/cards/cleave.py
# ПЕРВЫЙ ПОТРЕБИТЕЛЬ 2D-субстрата позиционки (§1 после кейстоуна С47/С48).
#
# Субстрат дал пьюр-ридеры (core/positioning.py: neighbors/column/same_rank), но до
# сих пор их никто не дёргал — ридеры были инертны. Сплеш-урон по СОСЕДНИМ клеткам
# (манхэттен-1) — class-agnostic боевой примитив, который оживляет `neighbors`:
# позиция цели начинает решать (удар по центру задевает больше соседей, чем по углу).
#
# Кирпич НАСЛЕДУЕТ DamageEffect → isinstance-проверки (синергийный слой бота,
# снимок hand_attack, классификатор карт) видят атаку без правок. Сплеш — поверх
# первичного удара. Позиционка off / нет соседей → neighbors пуст → ведёт себя как
# обычный DamageEffect (single-target fallback, baseline зелёный).
from core.cards.base import Card, DamageEffect
from core.EffectCalculator import EffectCalculator
from core.rarity import Rarity


class SplashDamageEffect(DamageEffect):
    """Урон цели (полный, наследует DamageEffect) + СПЛЕШ по ортогонально соседним
    клеткам врага. Сосед получает `splash_ratio` от базового урона, проведённого
    через EffectCalculator (уязвимость/слабость/шок соседа учитываются).

    Соседство — `core.positioning.neighbors` (манхэттен-1 по сетке line×rank, диагональ
    не сосед). Без полной позиции у цели (позиционка off / нет рангов у врагов) →
    соседей нет → бьётся только цель = обычный DamageEffect (регресс-нейтрально)."""

    SPLASH_RATIO = 0.5

    def __init__(self, base_val, upgrade_val, splash_ratio=SPLASH_RATIO):
        super().__init__(base_val, upgrade_val)
        self.splash_ratio = splash_ratio

    def execute(self, player, enemy, combat_manager, is_upgraded):
        # Первичный удар по цели — полный урон + лог (наследованная логика).
        super().execute(player, enemy, combat_manager, is_upgraded)
        if combat_manager is None:
            return
        base = self.upgrade_val if is_upgraded else self.base_val
        splash_base = int(base * self.splash_ratio)
        if splash_base <= 0:
            return
        from core.positioning import neighbors
        adjacent = neighbors(enemy, combat_manager.enemies)
        if not adjacent:
            return
        gm_ref = combat_manager.gm
        for nb in adjacent:
            final = EffectCalculator.calculate_damage(
                player, nb, splash_base, gm_ref, combat_manager
            )
            nb.take_damage(final, attacker=player, combat_manager=combat_manager)
            combat_manager.add_log_message(
                f" -> Рассечение: {nb.name} получает {final} урона (сплеш)."
            )


def create_cleaving_strike():
    """«Рассекающий удар» — урон 6(8) цели + половина по СОСЕДНИМ врагам на сетке.
    Демонстрационный носитель сплеш-механики (generic, доступен всем классам).
    Награда за позиционирование: бей по центру вражеского строя — заденешь больше."""
    return Card(
        name="Рассекающий удар",
        cost=1,
        card_type="attack",
        description="Урон 6(8) цели + половина по соседним врагам (по сетке).",
        effects=[SplashDamageEffect(6, 8)],
        rarity=Rarity.COMMON,
    )
