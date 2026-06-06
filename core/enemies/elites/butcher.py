# core/enemies/elites/butcher.py
# Мясник-Истязатель — элита-контра вампиризму/хилу.
# Механика: постоянные Шипы (отражают урон атакующему) + наказание за лечение —
# если HP игрока ВЫРОС между ходами Мясника (хил/вампир/реген перекрыли урон),
# игрок получает Слабость. Контра билдам, чей сустейн превышает входящий урон.
# Обход: не полагаться на хил (щит/бёрст), убить до накопления Слабости.
import random
from core.enemies.elites.base import EliteBase


class ButcherTorturer(EliteBase):
    """Элита-контра вампиризму/хилу.

    Пассив: Шипы BUTCHER_THORNS (Creature.take_damage отражает их атакующему).
    Начало хода (on_turn_start): если HP игрока стал ВЫШЕ, чем на прошлом ходу
    Мясника (нетто-лечение перекрыло урон) — +1 Слабость. Первое наблюдение
    лишь фиксирует снимок (без штрафа).

    Мягкие обходы:
    - Щитовики (Воин): защита вместо хила → HP не растёт, Слабости нет
    - Бёрст/высокий DPS: убивают до накопления Слабости
    - Шипы малы относительно поздних HP — не «глухая стена», а налог на сустейн
    """

    BUTCHER_THORNS = 3   # постоянное отражение урона (Creature.take_damage)

    _TITLES = [
        "Мясник-Истязатель",
        "Палач Плоти",
        "Свежеватель",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        self.thorns = self.BUTCHER_THORNS
        # Снимок HP игрока с прошлого хода Мясника. None → первое наблюдение.
        self._last_player_hp = None

    @staticmethod
    def random_title() -> str:
        return random.choice(ButcherTorturer._TITLES)

    # ── Хук реакции ──────────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Налог на сустейн: рост HP игрока между ходами Мясника → +1 Слабость."""
        # Поддерживаем Шипы (на случай, если что-то их обнулит в будущем).
        if self.thorns < self.BUTCHER_THORNS:
            self.thorns = self.BUTCHER_THORNS

        cur = player.hp
        if self._last_player_hp is not None and cur > self._last_player_hp:
            player.weak += 1
            if combat_manager:
                combat_manager.add_log_message(
                    f"[МЯСНИК] Ваше исцеление ({self._last_player_hp}→{cur} HP) "
                    f"бесит его: +1 Слабость."
                )
        self._last_player_hp = cur

    # ── Боевая логика ───────────────────────────────────────────────────

    def choose_intent(self):
        # Преимущественно атакует (Шипы и Слабость — пассивная угроза).
        if self.turn_count % 3 == 2:
            self.set_intent("defend", self.base_test_shield)
        else:
            self.set_intent("attack", self.base_test_damage)
