from core.cards.base import Card, DamageEffect, StatusEffect

def create_ignite():
    return Card("Поджог", 1, "attack", "Урон 2(4). Поджигает врага на 3(4) х.", [
        DamageEffect(2, 4),
        StatusEffect("ignited", 3, 4)
    ])

def create_fire_breath():
    """Чистое наложение горения мощного действия"""
    return Card("Огненное Дыхание", 2, "skill", "Окутывает врага пламенем, вешая Горение 6(9) х.", [
        StatusEffect("ignited", 6, 9)
    ])
