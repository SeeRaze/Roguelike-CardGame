from core.relics.base import Relic
from core.rarity import Rarity

class LuckyClover(Relic):
    """В первый ход боя игрок добирает +2 карты (разовый бурст в начале боя)."""

    def __init__(self):
        super().__init__("Счастливый Клевер", "В первый ход боя вы добираете +2 карты.", Rarity.COMMON)
    def on_combat_start(self, combat_manager):
        combat_manager.add_log_message(f"[Реликвия] '{self.name}' активирована!")
        combat_manager.deck_manager.draw_cards(2)

class SpikedBracelet(Relic):
    """В начале каждого боя игрок получает 10 Щита (стартовая оборона)."""

    def __init__(self):
        super().__init__("Шипастый Браслет", "Вы начинаете каждый бой с 10 единицами Щита.", Rarity.COMMON)
    def on_combat_start(self, combat_manager):
        combat_manager.player.gain_shield(10, combat_manager)
        combat_manager.add_log_message(f"[Реликвия] '{self.name}' дает вам 10 Щита!")

class ТочильныйКамень(Relic):
    """Увеличивает урон всех атак игрока на +2 (плоский бонус)."""

    def __init__(self):
        super().__init__("Точильный Камень", "Увеличивает урон всех ваших атак на +2.", Rarity.COMMON)

    def on_damage_calculated(self, base_dmg, is_player_attack=True, dry_run=False):
        if is_player_attack:
            return base_dmg + 2
        return base_dmg
