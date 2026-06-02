from core.cards.base import Card, DamageEffect, StatusEffect

def create_bash():
    return Card("Скручивание", 2, "attack", "Урон 8(12). Накладывает Уязвимость 2(3) х.", [
        DamageEffect(8, 12),
        StatusEffect("vulnerable", 2, 3)
    ])