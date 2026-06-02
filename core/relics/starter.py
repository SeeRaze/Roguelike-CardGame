from core.relics.base import Relic

class LuckyClover(Relic):
    def __init__(self): 
        super().__init__("Счастливый Клевер", "В первый ход боя вы добираете +2 карты.")
    def on_combat_start(self, combat_manager):
        combat_manager.add_log_message(f"[Реликвия] '{self.name}' активирована!")
        combat_manager.deck_manager.draw_cards(2)

class SpikedBracelet(Relic):
    def __init__(self): 
        super().__init__("Шипастый Браслет", "Вы начинаете каждый бой с 10 единицами Щита.")
    def on_combat_start(self, combat_manager):
        combat_manager.player.gain_shield(10)
        combat_manager.add_log_message(f"[Реликвия] '{self.name}' дает вам 10 Щита!")

class ТочильныйКамень(Relic):
    def __init__(self):
        super().__init__("Точильный Камень", "Увеличивает урон всех ваших атак на +2.")

    def on_damage_calculated(self, base_dmg, is_player_attack=True):
        if is_player_attack:
            return base_dmg + 2
        return base_dmg
