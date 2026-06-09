from core.players.base import Player
from core.players.abilities import BerserkerAbility
from core.players.abilities.berserker import MADNESS_HP_PCT_PER_COST
from core.cards import (
    create_strike, create_heavy_blade,
    create_flex, create_battle_cry,
    create_blood_rage, create_blood_thirst, create_crunch,
)


def get_berserker_deck():
    # Стартер РАСКРЫВАЕТ пассив, не запирает билд ([[starter-deck-reveals-passive]]):
    # 3 сигнатурки-«учителя» граней долга (Кровавая ярость = долг→урон, Жажда крови =
    # долг→FP, Кранч = добил-в-долге→второе дыхание/сустейн) + generic-основа = открытый
    # холст. 4-я сигнатурка (Безрассудный удар) — в драфт-пул, не в стартер. Один strike
    # уступил место Кранчу: цепочка «нырнул→добил→откачался» видна с 1-го боя (закрывает
    # дыру аутопсии «нырок не окупается в бою»). Замкнутого комбо-лупа нет.
    return [
        create_strike(), create_strike(),
        create_heavy_blade(), create_heavy_blade(),
        create_flex(),
        create_battle_cry(),
        create_blood_rage(),
        create_blood_thirst(),
        create_crunch(),
    ]


class Berserker(Player):
    """«Отрицание Смерти» — класс на ДОЛГЕ HP (§4, [[class-concepts-ideas]]).

    Пассив-движок: `hp_overdraft=True` → уходит в МИНУС HP (не умирает на 0), глубина
    минуса даёт множитель урона (EffectCalculator, шаг 8-ter). СТРОГАЯ расплата
    (`on_hp_debt_settle`): конец СВОЕГО хода в минусе и без победы → падает замертво
    (обязан выйти в плюс или добить за ход). ПИК (`on_combat_won`): победа «в коме» →
    |минус HP| → Forge Points колоде (death-spiral кормит ковку); выживает (hp=1)."""

    def __init__(self):
        super().__init__(
            name="Берсерк",
            max_hp=60,
            max_energy=3,
            gold=80,
            starter_deck_factory=get_berserker_deck,
        )
        self.active_ability = BerserkerAbility()
        # Класс ВКЛЮЧАЕТ долг HP всегда — это его движок (не Ставка/опт-ин).
        self.hp_overdraft = True
        # Ставка «Безумия»: HP за единицу стоимости карты = % max HP (карты за 0 энергии
        # ценой крови; С57 — процент, масштаб-инвариантно к росту max HP).
        self.madness_hp_pct_per_cost = MADNESS_HP_PCT_PER_COST

    def on_hp_debt_settle(self, combat_manager) -> None:
        """СТРОГАЯ расплата (вызывается в конце хода ядром, когда hp<0): если бой НЕ
        выигран (есть живые враги) — Берсерк падает замертво. Форсируем пол-смерть;
        end_turn_phase прервётся через check_player_defeat ДО действий врагов. Победа «в
        коме» сюда НЕ доходит: _check_victory срабатывает в момент килла (hp уже ≥0 после
        on_combat_won)."""
        if any(e.hp > 0 for e in combat_manager.enemies):
            self.hp = self._hp_floor()

    def on_combat_won(self, combat_manager) -> None:
        """ПИК «Отрицание Смерти»: победа в минусе → |минус HP| → Forge Points (кормит
        ковку колоды), Берсерк выживает (hp=1). NO-OP при hp>=0 (победил не в коме)."""
        if self.hp < 0:
            gained = -self.hp
            self.forge_points += gained
            combat_manager.add_log_message(
                f"[БЕРСЕРК] Отрицание Смерти: {gained} HP-долга → +{gained} FP!")
            self.hp = 1