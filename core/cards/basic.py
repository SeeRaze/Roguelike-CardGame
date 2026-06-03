from core.cards.base import Card, DamageEffect, ShieldEffect

def create_strike():
    return Card("Удар", 1, "attack", "Наносит 6 (9) чистейшего урона.", [DamageEffect(6, 9)])

def create_defend():
    return Card("Защита", 1, "defense", "Дает 5 (8) базового щита.", [ShieldEffect(5, 8)])

def create_heavy_blade():
    return Card("Тяжелый Клинок", 2, "attack", "Мощный рубящий удар на 14 (20) урона.", [DamageEffect(14, 20)])

def create_iron_wall():
    return Card("Железная Стена", 2, "defense", "Непробиваемый барьер на 12 (18) щита.", [ShieldEffect(12, 18)])

