from core.cards.base import Card

from core.cards.buff.strength import BuffEffect


def create_thorn_armor():
    return Card("Ханипот", 1, "defense", "Ловушка для атакующего: +3(5) Файрвола.", [
        BuffEffect("firewall", 3, 5)
    ])