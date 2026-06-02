from core.cards.base import Card, DamageEffect, PoisonEffect, ShieldEffect

def create_poison_stab():
    return Card("Ядовитый укол", 1, "attack", "Наносит 4(6) урона. Накладывает 3(5) Яда.", [
        DamageEffect(4, 6),
        PoisonEffect(3, 5)
    ])

def create_toxic_cloud():
    return Card("Токсичное Облако", 2, "skill", "Выпускает газ: накладывает 7(10) ед. Яда.", [
        PoisonEffect(7, 10)
    ])

def create_acid_shield():
    return Card("Кислотный Барьер", 1, "defense", "Дает 6(9) щита. Накладывает 2(3) Яда.", [
        ShieldEffect(6, 9),
        PoisonEffect(2, 3)
    ])
