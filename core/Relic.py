class Relic:
    """Базовый родительский класс для всех пассивных артефактов."""
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def on_combat_start(self, combat_manager): pass
    def on_turn_start(self, combat_manager): pass
    def on_damage_calculated(self, base_dmg): return base_dmg # Возвращает урон без изменений по дефолту


class LuckyClover(Relic):
    def __init__(self): super().__init__("Счастливый Клевер", "В первый ход боя вы добираете +2 карты.")
    def on_combat_start(self, combat_manager):
        combat_manager.add_log_message(f"[Реликвия] '{self.name}' активирована!")
        combat_manager.deck_manager.draw_cards(2)


class SpikedBracelet(Relic):
    def __init__(self): super().__init__("Шипастый Браслет", "Вы начинаете каждый бой с 10 единицами Щита.")
    def on_combat_start(self, combat_manager):
        combat_manager.player.gain_shield(10)
        combat_manager.add_log_message(f"[Реликвия] '{self.name}' дает вам 10 Щита!")


# ==============================================================================
#  НОВЫЕ РЕЛИКВИИ
# ==============================================================================
class ЭнергоЯдро(Relic):
    """Твоя будущая Легендарка: пассивно увеличивает макс. энергию на 1"""
    def __init__(self): super().__init__("Энерго-Ядро", "Увеличивает вашу максимальную энергию на +1.")
    
    # Она работает глобально, её эффект мы применим прямо в Player через GameManager чуть позже


class ТочильныйКамень(Relic):
    """Увеличивает урон всех карт на +2"""
    def __init__(self): super().__init__("Точильный Камень", "Увеличивает урон всех ваших атак на +2.")
    
    def on_damage_calculated(self, base_dmg):
        # Прибавляем +2 к базовому урону любой карты перед расчетом статусов
        return base_dmg + 2


class ДревнееОгниво(Relic):
    """Идея от ИИ №1: Синергия с огнем"""
    def __init__(self): super().__init__("Древнее Огниво", "Увеличивает урон от Горения на +2.")
    # Логику тика добавим в механику статусов существ на следующих этапах


class НамокшаяРукавица(Relic):
    """Идея от ИИ №2: Синергия с водой"""
    def __init__(self): super().__init__("Намокшая Рукавица", "Разыгрывание 'Всплеска' дает вам +4 Щита.")
