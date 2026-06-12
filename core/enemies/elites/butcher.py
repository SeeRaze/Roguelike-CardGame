# core/enemies/elites/butcher.py
# Мясник-Истязатель — элита-контра сустейну/хилу.
# Механика: постоянный Файрвол (отражает урон атакующему) + наказание за лечение —
# если HP игрока ВЫРОС между ходами Мясника (хил/хелсчек перекрыли урон),
# игрок получает Токсичность. Контра билдам, чей сустейн превышает входящий урон.
# Обход: не полагаться на хил (щит/бёрст), убить до накопления Токсичности.
import random
from core.enemies.elites.base import EliteBase


class ButcherTorturer(EliteBase):
    """Элита-контра сустейну/хилу.

    Пассив: Файрвол BUTCHER_FIREWALL (Creature.take_damage отражает их атакующему).
    Начало хода (on_turn_start): если HP игрока стал ВЫШЕ, чем на прошлом ходу
    Мясника (нетто-лечение перекрыло урон) — +1 Токсичность. Первое наблюдение
    лишь фиксирует снимок (без штрафа).

    Мягкие обходы:
    - Щитовики (Воин): защита вместо хила → HP не растёт, Токсичности нет
    - Бёрст/высокий DPS: убивают до накопления Токсичности
    - Файрвол мал относительно поздних HP — не «глухая стена», а налог на сустейн
    """

    BUTCHER_FIREWALL = 3   # постоянное отражение урона (Creature.take_damage)

    _TITLES = [
        "Мясник-Истязатель",
        "Палач Плоти",
        "Свежеватель",
    ]

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        self.firewall = self.BUTCHER_FIREWALL
        # Снимок HP игрока с прошлого хода Мясника. None → первое наблюдение.
        self._last_player_hp = None

    @staticmethod
    def random_title() -> str:
        return random.choice(ButcherTorturer._TITLES)

    # ── Хук реакции ──────────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Налог на сустейн: рост HP игрока между ходами Мясника → +1 Токсичность."""
        # Поддерживаем Файрвол (на случай, если что-то его обнулит в будущем).
        if self.firewall < self.BUTCHER_FIREWALL:
            self.firewall = self.BUTCHER_FIREWALL

        cur = player.hp
        if self._last_player_hp is not None and cur > self._last_player_hp:
            player.tox += 1
            if combat_manager:
                combat_manager.add_log_message(
                    f"[МЯСНИК] Ваше исцеление ({self._last_player_hp}→{cur} HP) "
                    f"бесит его: +1 Токсичность."
                )
        self._last_player_hp = cur

    # ── Боевая логика ───────────────────────────────────────────────────

    def choose_intent(self):
        # Преимущественно атакует (Файрвол и Токсичность — пассивная угроза).
        if self.turn_count % 3 == 2:
            self.set_intent("defend", self.base_test_shield)
        else:
            self.set_intent("attack", self.base_test_damage)
