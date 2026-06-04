# core/Summon.py
# Союзники (призывные существа): базовая логика.
# Summon — наследник Creature с авто-атакой в конце хода игрока.
import random
from core.Creature import Creature


class Summon(Creature):
    """Призывное существо-союзник. Живёт в combat_manager.allies.
    Каждый ход выбирает случайного живого врага и атакует его."""

    def __init__(self, name, hp, attack_power, owner=None):
        super().__init__(name=name, hp=hp, max_hp=hp)
        self.attack_power = attack_power
        self.owner = owner          # ссылка на игрока (если нужно)

    def choose_action(self, combat_manager):
        """Выбрать случайного живого врага. Возвращает врага или None."""
        living = [e for e in combat_manager.enemies if e.hp > 0]
        if not living:
            return None
        return random.choice(living)

    def execute_action(self, target, combat_manager):
        """Атаковать выбранного врага."""
        if target is None or target.hp <= 0:
            return
        dmg = self.attack_power
        target.take_damage(dmg, attacker=self, combat_manager=combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f"[СОЮЗНИК] {self.name} атакует {target.name} на {dmg} урона."
            )
