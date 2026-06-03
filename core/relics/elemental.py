from core.relics.base import Relic

class ЭнергоЯдро(Relic):
    def __init__(self):
        super().__init__("Энерго-Ядро", "Увеличивает максимальную энергию на +1.")
        self._applied = False

    def on_combat_start(self, combat_manager):
        if not self._applied:
            combat_manager.player.max_energy += 1
            combat_manager.player.energy += 1
            self._applied = True
            combat_manager.add_log_message(f"[Реликвия] '{self.name}': макс. энергия +1!")


class ДревнееОгниво(Relic):
    def __init__(self):
        super().__init__("Древнее Огниво", "Каждый тик Горения наносит +2 урона.")

    def on_tick_ignited(self, creature):
        return 2


class НамокшаяРукавица(Relic):
    def __init__(self):
        super().__init__("Намокшая Рукавица", "При наложении 'Мокрый' на врага -- +4 Щита.")

    def on_wet_applied(self, combat_manager):
        combat_manager.player.gain_shield(4, combat_manager)  # ← фикс
        combat_manager.add_log_message(f"[Реликвия] '{self.name}': +4 Щита!")