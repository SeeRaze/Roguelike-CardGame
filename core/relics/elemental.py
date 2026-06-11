import random

from core.relics.base import Relic
from core.rarity import Rarity

class ЭнергоЯдро(Relic):
    """В начале первого боя навсегда увеличивает макс. энергию игрока на +1."""

    def __init__(self):
        super().__init__("Энерго-Ядро", "Увеличивает максимальную энергию на +1.", Rarity.RARE)
        self._applied = False

    def on_combat_start(self, combat_manager):
        if not self._applied:
            combat_manager.player.max_energy += 1
            combat_manager.player.energy += 1
            self._applied = True
            combat_manager.add_log_message(f"[Реликвия] '{self.name}': макс. энергия +1!")


class Дебаггер(Relic):
    """Каждый тик Legacy-кода на любом существе наносит +2 урона (амп DoT)."""

    def __init__(self):
        super().__init__("Дебаггер", "Дебаггер подсвечивает баги: каждый тик Legacy-кода наносит +2 урона.", Rarity.UNCOMMON)

    def on_tick_legacy(self, creature):
        return 2


class ПассивнаяАгрессия(Relic):
    """При наложении 'Разлитый кофе' на врага игрок получает +4 Щита."""

    def __init__(self):
        super().__init__("Пассивная агрессия", "Облил коллегу кофе и спокоен: при наложении 'Разлитый кофе' на врага +4 Щита.", Rarity.UNCOMMON)

    def on_coffee_applied(self, combat_manager):
        combat_manager.player.gain_shield(4, combat_manager)
        combat_manager.add_log_message(f"[Реликвия] '{self.name}': +4 Щита!")


class Кофемашина(Relic):
    """В начале боя случайный живой враг получает Разлитый кофе (2 стака).

    Энейблер ХОТФИКСа: открывает амп урона (+20%/стак) уже на старте, а также
    триггерит реликвии на наложение Кофе (напр. «Пассивная агрессия»)."""

    def __init__(self):
        super().__init__(
            "Кофемашина",
            "В начале каждого боя случайный враг обливается Разлитым кофе (2).",
            Rarity.COMMON,
        )

    def on_combat_start(self, combat_manager):
        living = [e for e in combat_manager.enemies if e.hp > 0]
        if not living:
            return
        target = random.choice(living)
        target.add_status("coffee", 2, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': {target.name} облит кофе!"
        )