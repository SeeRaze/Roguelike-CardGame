# core/Summon.py
# Союзники (призывные существа): базовая логика.
# Summon — наследник Creature с авто-атакой в конце хода игрока.
import random
from core.Creature import Creature


class Summon(Creature):
    """Призывное существо-союзник. Живёт в combat_manager.allies.
    Каждый ход выбирает случайного живого врага и атакует его."""

    # Пассив Призывателя «Свора»: каждый союзник бьёт сильнее за КАЖДОГО
    # другого живого союзника на поле. Урон стаи растёт нелинейно
    # (N союзников × бонус (N-1)) — даёт призывам масштаб на поздних этажах.
    PACK_DAMAGE_PER_ALLY = 5

    def __init__(self, name, hp, attack_power, owner=None):
        super().__init__(name=name, hp=hp, max_hp=hp)
        self.attack_power = attack_power
        self.owner = owner          # ссылка на игрока (если нужно)

    def _pack_bonus(self, combat_manager) -> int:
        """Бонус «Своры»: +PACK_DAMAGE_PER_ALLY за каждого ДРУГОГО живого союзника."""
        allies = getattr(combat_manager, 'allies', None)
        if not allies:
            return 0
        others = sum(1 for a in allies if a is not self and a.hp > 0)
        return others * self.PACK_DAMAGE_PER_ALLY

    def choose_action(self, combat_manager):
        """Выбрать случайного живого врага. Возвращает врага или None."""
        living = [e for e in combat_manager.enemies if e.hp > 0]
        if not living:
            return None
        return random.choice(living)

    def execute_action(self, target, combat_manager):
        """Атаковать выбранного врага. Урон усилен «Сворой» (см. _pack_bonus)."""
        if target is None or target.hp <= 0:
            return
        bonus = self._pack_bonus(combat_manager)
        dmg = self.attack_power + bonus
        target.take_damage(dmg, attacker=self, combat_manager=combat_manager)
        if combat_manager:
            extra = f" (+{bonus} Свора)" if bonus else ""
            combat_manager.add_log_message(
                f"[СОЮЗНИК] {self.name} атакует {target.name} на {dmg} урона{extra}."
            )
