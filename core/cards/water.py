from core.cards.base import Card, DamageEffect, StatusEffect

def create_splash():
    return Card("Всплеск", 1, "attack", "Урон 2(4). Обливает врага водой: Мокрый на 3(4) х.", [
        DamageEffect(2, 4),
        StatusEffect("wet", 3, 4)
    ])

def create_rain_cloud():
    """Глобальное наложение влаги"""
    return Card("Дождевая Туча", 1, "skill", "Проливает ливень: статус Мокрый на 5(7) х.", [
        StatusEffect("wet", 5, 7)
    ])
