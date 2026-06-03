# tests/test_deck_manager.py
# Проверяем «круговорот» карт: Добор -> Рука -> Сброс, изгнание и инвариант
# «карты не теряются и не дублируются».
from managers.DeckManager import DeckManager


class _Карта:
    """Простая заглушка карты — DeckManager'у нужно только имя."""
    def __init__(self, name):
        self.name = name


def _колода(n):
    return [_Карта(f"Карта{i}") for i in range(n)]


def test_reset_кладёт_все_карты_в_добор():
    dm = DeckManager(_колода(5))
    assert len(dm.draw_pile) == 5
    assert dm.hand == [] and dm.discard_pile == []


def test_добор_перекладывает_карты_в_руку():
    dm = DeckManager(_колода(5))
    dm.draw_cards(3)
    assert len(dm.hand) == 3 and len(dm.draw_pile) == 2


def test_пустой_добор_перемешивает_сброс_обратно():
    dm = DeckManager(_колода(3))
    dm.draw_cards(3)            # вся колода в руке, добор пуст
    dm.discard_hand()          # рука -> сброс (3 карты)
    dm.draw_cards(2)           # добор пуст -> сброс перемешивается обратно
    assert len(dm.hand) == 2 and len(dm.draw_pile) == 1


def test_сброс_руки_чистит_временную_скидку():
    dm = DeckManager(_колода(2))
    dm.draw_cards(1)
    dm.hand[0].temp_cost = 0    # скидка Разбойника
    dm.discard_hand()
    assert not hasattr(dm.discard_pile[0], "temp_cost")


def test_изгнанные_карты_возвращаются_в_колоду_на_reset():
    dm = DeckManager(_колода(3))
    изгнанная = _Карта("Изгнанная")
    dm.exile_pile.append(изгнанная)
    dm.reset_deck()
    assert изгнанная in dm.draw_pile and dm.exile_pile == []


def test_инвариант_карты_не_теряются():
    # Сумма карт во всех стопках всегда равна исходному размеру колоды.
    dm = DeckManager(_колода(6))
    dm.draw_cards(4)
    всего = len(dm.draw_pile) + len(dm.hand) + len(dm.discard_pile) + len(dm.exile_pile)
    assert всего == 6
    dm.discard_hand()
    всего = len(dm.draw_pile) + len(dm.hand) + len(dm.discard_pile) + len(dm.exile_pile)
    assert всего == 6
