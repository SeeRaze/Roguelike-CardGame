from core.relics.base import Relic

class ЭнергоЯдро(Relic):
    def __init__(self): 
        super().__init__("Энерго-Ядро", "Увеличивает вашу максимальную энергию на +1.")

class ДревнееОгниво(Relic):
    def __init__(self): 
        super().__init__("Древнее Огниво", "Увеличивает урон от Горения на +2.")

class НамокшаяРукавица(Relic):
    def __init__(self): 
        super().__init__("Намокшая Рукавица", "Разыгрывание 'Всплеска' дает вам +4 Щита.")
