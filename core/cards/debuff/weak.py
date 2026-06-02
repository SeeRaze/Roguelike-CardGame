from core.cards.base import Card, DamageEffect, StatusEffect

def create_neutralize():
    return Card("Нейтрализация", 0, "attack", "Быстрый выпад на 3(4) урона. Слабость 1(2) х.", [
        DamageEffect(3, 4),
        StatusEffect("weak", 1, 2)
    ])

def create_intimidate():
    return Card("Устрашение", 1, "skill", "Ослабляет врага на 2(3) хода, снижая его атаку.", [
        StatusEffect("weak", 2, 3)
    ])