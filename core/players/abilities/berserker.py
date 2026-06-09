# core/players/abilities/berserker.py
from core.players.ability import ClassAbility

# Безумие: карта стоит 0 энергии, но HP = стоимость × (этот % от MAX HP), сквозь щит.
# Для Берсерка (hp_overdraft) уводит в МИНУС → HP-долг множитель урона. Ручка калибровки.
# С57: ПРОЦЕНТ, не флат — самоурон растёт с max HP (масштаб-инвариантно к экспоненте,
# [[balance-curve-framework]]). На 60 HP ≡ прежнему cost×4 (0.07·60≈4). Иначе на больших
# max HP Безумие становилось бы «free cards» (cost×4 — копейки), и нырок не работал бы.
MADNESS_HP_PCT_PER_COST = 0.07


class BerserkerAbility(ClassAbility):
    """«Безумие»
    Берсерк входит в БЕЗУМИЕ на этот ход: карты стоят 0 энергии, но каждая берёт HP
    (стоимость × MADNESS_HP_PCT_PER_COST × max HP, сквозь щит). Это «педаль газа» —
    проактивный НЫРОК в красную зону: больше карт за ход (темпо) + уход в МИНУС →
    множитель урона. Цена — приближение к смерти (строгая расплата). Повторяема КАЖДЫЙ
    ход (лимит = сам HP)."""

    def __init__(self):
        super().__init__(
            name="Дедлайн",
            description="Горящий дедлайн: в этот ход карты стоят 0 энергии, "
                        f"но берут HP (стоимость × {int(MADNESS_HP_PCT_PER_COST * 100)}% "
                        "макс. HP, сквозь щит).\n"
                        "Нырок в красную зону: множитель урона от минуса HP.\n"
                        "Можно использовать каждый ход.",
        )

    def on_combat_start(self, combat_manager) -> None:
        super().on_combat_start(combat_manager)
        combat_manager.player.madness_active = False

    def on_turn_start(self, combat_manager) -> None:
        # Безумие повторяемо КАЖДЫЙ ход (один раз за ход). Снимаем пометку
        # «использовано в этот ход» → кнопка честно загорается снова на новом ходу.
        # Единый _used-цикл с Воином/Магом: статус слота не врёт после активации.
        self._used = False

    def activate(self, combat_manager) -> bool:
        player = combat_manager.player
        if getattr(player, "madness_active", False):
            return False                         # уже в безумии в этот ход
        player.madness_active = True
        self._used = True                        # кнопка гаснет до след. хода (как Воин/Маг)
        combat_manager.add_log_message(
            "[СТАЖЁР] ДЕДЛАЙН! Карты за 0 энергии — ценой HP.")
        return True
