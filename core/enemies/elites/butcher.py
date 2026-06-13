# core/enemies/elites/butcher.py
# Анти-DDoS — элита-контра БЁРСТУ (перекована после передела классов).
# Старая контра (наказание за хил) протухла: вампиризм снесён, ни один из тройки
# больше не хил-класс. Новая роль — оппонент гласс-пушке Стажёра (overdrive/HP-долг),
# у которой контры не было. Механика: отражает ДОЛЮ размера входящего удара
# (%-отлуп) — чем крупнее залп, тем больнее отдача; мелкий чип проходит почти
# даром. Бьёт по тому, кто живёт большими ударами на низком HP. Плюс мелкий
# флат-файрвол (иконка-телеграф «отражает»). Crash Reboot (leak+tox) гасит файрвол
# → весь отлуп отключается (честная контра игрока). Класс-ID ButcherTorturer сохранён.
import random
from core.enemies.elites.base import EliteBase


class ButcherTorturer(EliteBase):
    """Элита-контра бёрсту («Анти-DDoS»).

    Пассив: флат-Файрвол FLAT_FIREWALL (иконка + базовое отражение). Override
    take_damage добавляет %-отлуп: REFLECT_PCT от РАЗМЕРА удара возвращается
    атакующему сквозь щит. Чем крупнее единичный удар (бёрст Стажёра), тем больше
    отдача; при низком/долговом HP атакующего отлуп подталкивает к полу долга.
    %-часть активна, только пока жив файрвол → Crash Reboot его обнуляет и снимает
    весь отлуп (counterplay). Боевая логика — преимущественно атака.

    Мягкие обходы:
    - Дробный урон/много мелких ударов: %-отлуп на каждый мал → проходит дёшево
    - Урон сквозь щит без «удара» (legacy-DoT/Казнь): не триггерит отлуп
    - Crash Reboot (leak+tox): гасит файрвол → отлуп выключен
    """

    FLAT_FIREWALL = 2     # базовое отражение + иконка-телеграф «отражает»
    REFLECT_PCT = 0.25    # доля размера удара, возвращаемая атакующему (анти-бёрст)

    _TITLES = [
        "Анти-DDoS",
        "IDS-файрвол",
        "WAF",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        self.firewall = self.FLAT_FIREWALL

    @staticmethod
    def random_title() -> str:
        return random.choice(ButcherTorturer._TITLES)

    # ── Анти-бёрст: %-отлуп размера удара ────────────────────────────────

    def take_damage(self, amount, attacker=None, combat_manager=None):
        # Базовый расчёт + флат-файрвол (Creature.take_damage отражает self.firewall).
        super().take_damage(amount, attacker, combat_manager)
        # %-отлуп: возвращаем долю РАЗМЕРА удара (наказание за бёрст). Активен,
        # пока жив файрвол — Crash Reboot его гасит и отключает отдачу.
        if attacker is not None and amount > 0 and self.get_status("firewall") > 0:
            reflect = int(amount * self.REFLECT_PCT)
            if reflect > 0:
                attacker.hp = max(attacker.hp - reflect, attacker._hp_floor())
                if combat_manager:
                    combat_manager.add_log_message(
                        f"[АНТИ-DDoS] Отлуп {reflect} "
                        f"({int(self.REFLECT_PCT * 100)}% удара) по "
                        f"{getattr(attacker, 'name', '?')}."
                    )

    # ── Боевая логика ───────────────────────────────────────────────────

    def choose_intent(self):
        # Преимущественно атакует (отлуп — пассивная угроза).
        if self.turn_count % 3 == 2:
            self.set_intent("defend", self.base_test_shield)
        else:
            self.set_intent("attack", self.base_test_damage)
