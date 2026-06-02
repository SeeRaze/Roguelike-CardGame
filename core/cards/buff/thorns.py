from core.cards.base import Card

from core.cards.buff.strength import BuffEffect


def create_thorn_armor():
    return Card("Шипованная Броня", 1, "defense", "Надевает броню с шипами: +3(5) Шипов.", [
        BuffEffect("thorns", 3, 5)
    ])