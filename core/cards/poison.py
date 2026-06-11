# core/cards/poison.py
# Старые «ядовитые» карты (вне generic-пула): сырьё Химика + ивент-награды.
# С58-фолд: Яд влит в Legacy-код (один DoT, уважает щит; пробитие = Кислотный
# дождь Legacy+Токс). Карты накладывают legacy; имена-флавор перетрясёт волна карт.
from core.cards.base import Card, DamageEffect, StatusEffect, ShieldEffect

def create_poison_stab():
    return Card("Ядовитый укол", 1, "attack", "Наносит 4(6) урона. Накладывает Legacy-код 3(5).", [
        DamageEffect(4, 6),
        StatusEffect("legacy", 3, 5)
    ])

def create_toxic_cloud():
    return Card("Токсичное Облако", 2, "skill", "Выпускает газ: накладывает Legacy-код 7(10).", [
        StatusEffect("legacy", 7, 10)
    ])

def create_acid_shield():
    return Card("Кислотный Барьер", 1, "defense", "Даёт 6(9) щита. Накладывает Legacy-код 2(3).", [
        ShieldEffect(6, 9),
        StatusEffect("legacy", 2, 3)
    ])
