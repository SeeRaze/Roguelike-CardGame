# core/enemies/elites/plague.py
# Легаси-монолит — элита-контра обороне (ОСЛАБЛЕНА после передела Тестировщика).
# Механика: в начале своего хода вешает Legacy-код игроку; ЕСЛИ у игрока есть щит —
# дополнительно +Токс (рыхлый монолит «подтекает» в твою броню), но БЕЗ удвоения и
# без катастрофического пробития прежнего «Кислотного дождя». Турель замечена, но
# не казнена: переделанный Тестировщик весь на удержании щита, поэтому контра
# смягчена до налога-напряжения. Обход: агрессия, снятие/игнор DoT, бёрст.
# Класс-идентификатор PlaguePustule сохранён (инфра/реестр).
import random
from core.enemies.elites.base import EliteBase


class PlaguePustule(EliteBase):
    """Элита-контра обороне («Легаси-монолит», ослабленная).

    Начало хода (on_turn_start): +LEGACY_PER_TURN Legacy-кода игроку; при наличии
    щита — дополнительно +SHIELD_TOX Токс (мягкий налог на «черепаху»: токс слегка
    режет исходящий урон). БЕЗ ×2 и без полного пробития брони (прежний «Кислотный
    дождь» снят — он стал анти-классом для щит-Тестировщика). Боевая логика —
    атака/защита; основная угроза — стакающийся DoT.

    Мягкие обходы:
    - Агрессивные билды: меньше сидят под щитом → нет даже токс-налога
    - Снятие/блок стихий (Маг): гасит DoT
    - Бёрст/высокий DPS: убивают до того, как DoT накопится
    """

    LEGACY_PER_TURN = 2   # базовое наложение Legacy-кода за ход (было 3)
    SHIELD_TOX = 1        # +Токс при щите (мягкий налог; было ×2 legacy + 2 tox)

    _TITLES = [
        "Легаси-монолит",
        "Неубиваемый монолит",
        "Ком грязного кода",
    ]

    @staticmethod
    def random_title() -> str:
        return random.choice(PlaguePustule._TITLES)

    # ── Хук реакции ──────────────────────────────────────────────────────

    def on_turn_start(self, player, combat_manager) -> None:
        """Вешает Legacy-код игроку. Щит игрока добавляет мягкий Токс-налог
        (без ×2 и без полного пробития). Смягчённая контра обороне."""
        player.add_status("legacy", self.LEGACY_PER_TURN, combat_manager)
        shielded = getattr(player, "shield", 0) > 0
        if shielded:
            player.add_status("tox", self.SHIELD_TOX, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f"[ЛЕГАСИ-МОНОЛИТ] +{self.LEGACY_PER_TURN} Legacy-кода; "
                    f"щит подтекает: +{self.SHIELD_TOX} Токс."
                )
        elif combat_manager:
            combat_manager.add_log_message(
                f"[ЛЕГАСИ-МОНОЛИТ] +{self.LEGACY_PER_TURN} Legacy-кода."
            )

    # ── Боевая логика ───────────────────────────────────────────────────

    def choose_intent(self):
        # Чередует защиту и атаку; основной урон наносит DoT из on_turn_start.
        if self.turn_count % 2 == 0:
            self.set_intent("attack", self.base_test_damage)
        else:
            self.set_intent("defend", self.base_test_shield)
