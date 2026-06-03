from core.players.base import Player
from core.cards import (
    create_strike, create_defend,
    create_bandage, create_second_wind,
    create_regenerate, create_vitality,
    create_poison_stab, create_toxic_cloud,
)

def get_druid_deck():
    return [
        create_strike(), create_strike(),
        create_defend(), create_defend(),
        create_bandage(),       # быстрый хил
        create_bandage(),       # ещё один -- класс про выживание
        create_regenerate(),    # реген в конце хода
        create_vitality(),      # усиленный реген
        create_poison_stab(),   # пассивный урон пока лечишься
        create_toxic_cloud(),   # тяжёлый яд
    ]

class Druid(Player):
    def __init__(self):
        super().__init__(
            name="Друид",
            max_hp=70,
            max_energy=3,
            gold=100,
            starter_deck_factory=get_druid_deck,
        )