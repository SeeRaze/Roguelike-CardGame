from core.players.base import Player
from core.players.abilities import MageAbility
from core.EffectCalculator import EffectCalculator
from core.cards import (
    create_commit, create_code_review, create_coffee_spill, create_legacy_patch,
    create_overclock, create_resonant_discharge,
)

# НЕСТАБИЛЬНОСТЬ (ступень «Гни») — цена в % от MAX HP (масштаб-инвариантна: актуальна
# на этаже 1 и 100, [[economy-axis-trinity]]). ЭСКАЛИРУЕТ с глубиной Мастерства за порогом:
# чем дальше «гнёшь» — тем больнее глитчит (прото-Контекстное Окно Демиурга). Награда
# (×1.5, шаг 2c) растёт сама от большего Мастерства. Числа = ЗАГЛУШКИ под капстоун.
INSTABILITY_BASE_PCT      = 0.04   # базовая цена на пороге (% max HP/ход)
INSTABILITY_PCT_PER_STACK = 0.01   # +% за каждый стак Мастерства СВЕРХ порога
# Комбо-хил (Стихийный резонанс) — тоже % от MAX HP (иначе плоский +7 протух бы к эт.100).
# Маг = HP-churn: %-искрит / %-лечится → самодостаточен на любом масштабе.
COMBO_HEAL_PCT            = 0.08


def instability_cost(max_hp: int, mastery: int) -> int:
    """Цена Нестабильности за ход (HP сквозь щит) при данных max_hp и Мастерстве.
    0 ниже порога перегруза; на пороге = base%, далее +per_stack% за каждый стак сверх.
    Чистая функция — зовут пассив Мага И бот-политика (оценка риска гамбла)."""
    threshold = EffectCalculator.MASTERY_INSTABILITY_THRESHOLD
    if mastery < threshold:
        return 0
    over = mastery - threshold
    pct = INSTABILITY_BASE_PCT + INSTABILITY_PCT_PER_STACK * over
    return int(max_hp * pct)


def get_mage_deck():
    # Де-рельсенный стартер (С56→С58): ХОТФИКС НЕ пред-собран. Кофе+Legacy раздельно →
    # игрок СОБИРАЕТ комбо сам → комбо растит Мастерство (пассив). 2 сигнатурки-учителя:
    # Разгон (гамбл HP→Мастерство) + Резонансный разряд (выжать глубину). Закипание/
    # Стихийный всплеск/Тайное сосредоточение — в драфт-пуле (catalog).
    # С60 (задача 4): флат → пол 1:1 (Удар→Коммит, Защита→Код-ревью). Костыль копит
    # долг (ACCRUE) — Код-ревью×3 даёт counterplay из коробки.
    return [
        create_commit(), create_commit(),
        create_code_review(), create_code_review(), create_code_review(),
        create_coffee_spill(),          # Разлитый кофе (половина ХОТФИКС)
        create_legacy_patch(),          # Legacy-код (половина ХОТФИКС) — собери сам
        create_overclock(),             # Разгон: гамбл HP → Мастерство
        create_resonant_discharge(),    # Резонансный разряд: урон от глубины Мастерства
    ]


class Mage(Player):
    def __init__(self):
        super().__init__(
            name="Маг",
            max_hp=70,
            max_energy=3,
            gold=90,
            starter_deck_factory=get_mage_deck,
        )
        self.active_ability = MageAbility()

    def on_turn_start_passive(self, combat_manager) -> None:
        """НЕСТАБИЛЬНОСТЬ (ступень «Гни»): при перегрузе Мастерства (≥ порога) «интерфейс
        искрит» — Маг теряет HP сквозь щит в начале хода. Цена в % max HP, ЭСКАЛИРУЕТ с
        глубиной Мастерства (чем дальше гнёшь — тем больнее). Цена за усиленный бонус
        Мастерства (EffectCalculator шаг 2c). Сеет Контекстное Окно Демиурга. NO-OP ниже
        порога."""
        cost = instability_cost(self.max_hp, self.mastery)
        if cost > 0:
            lost = self.lose_hp(cost)
            if lost > 0 and combat_manager:
                combat_manager.add_log_message(
                    f" [ВАЙБ-КОДЕР] Нестабильность: интерфейс искрит, -{lost} HP "
                    f"(Мастерство {self.mastery})."
                )

    def on_card_played_passive(self, card, combat_manager) -> None:
        if not combat_manager:
            return
        if getattr(combat_manager, '_combo_triggered', False):
            combat_manager._combo_triggered = False
            # Мастерство стихий: каждое комбо усиливает ВСЕ будущие атаки (кат.4).
            self.add_status("mastery", 1, combat_manager)
            drawn = combat_manager.deck_manager.draw_cards(1)
            if drawn > 0:
                combat_manager.add_log_message(
                    " [ВАЙБ-КОДЕР] Стихийный резонанс: +1 карта из колоды!"
                )
            healed = self.heal(int(self.max_hp * COMBO_HEAL_PCT), combat_manager)
            if healed > 0:
                combat_manager.add_log_message(
                    f" [ВАЙБ-КОДЕР] Стихийный резонанс: +{healed} HP, "
                    f"Мастерство {self.mastery}!"
                )