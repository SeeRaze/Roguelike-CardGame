from core.cards.base import Card

class BuffEffect:
    """Эффект наложения пассивного баффа на игрока."""
    def __init__(self, buff_type, base_val, upgrade_val):
        self.buff_type = buff_type
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        val = self.upgrade_val if is_upgraded else self.base_val
        setattr(player, self.buff_type, getattr(player, self.buff_type) + val)
        if combat_manager:
            combat_manager.add_log_message(f" -> +{val} к {self.buff_type} на игрока.")


def create_flex():
    return Card("Стендап", 1, "skill", "Утренняя синхронизация: +2(3) Оптимизации на этот бой.", [
        BuffEffect("optimize", 2, 3)
    ])

def create_battle_cry():
    return Card("Кик-офф", 2, "skill", "Мощный старт проекта: +4(6) Оптимизации.", [
        BuffEffect("optimize", 4, 6)
    ])