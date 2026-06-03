import random


class DeckManager:
    """
    Управляет круговоротом карт: Добор -> Рука -> Сброс.
    Изгнанные карты (exile) хранятся отдельно и не участвуют в бою.
    """
    def __init__(self, starting_pool):
        self.pool = starting_pool

        self.draw_pile    = []
        self.hand         = []
        self.discard_pile = []
        self.exile_pile   = []   # Изгнанные карты -- вне боя до победы

        self.reset_deck()

    def reset_deck(self):
        """Полная перезагрузка колоды (старт нового боя).
        Изгнанные карты возвращаются в пул."""
        # Возвращаем изгнанные карты обратно в пул перед сбросом
        if self.exile_pile:
            self.pool.extend(self.exile_pile)
            self.exile_pile.clear()
            print("--- Изгнанные карты возвращены в колоду! ---")

        self.draw_pile = self.pool.copy()
        self.hand.clear()
        self.discard_pile.clear()

        random.shuffle(self.draw_pile)
        print("--- Менеджер Колоды: Все карты собраны в добор и перемешаны! ---")

    def draw_cards(self, amount):
        """Безопасный добор карт с защитой от бесконечных циклов.
        Возвращает количество реально добраных карт."""
        print(f"--- Менеджер Колоды: Пытаемся добрать карт: {amount} ---")
        drawn = 0

        for _ in range(amount):
            if not self.draw_pile:
                if self.discard_pile:
                    print("--- Сброс перемешивается обратно в колоду добора! ---")
                    self.draw_pile = self.discard_pile.copy()
                    self.discard_pile.clear()
                    random.shuffle(self.draw_pile)
                else:
                    print("[!] Больше нет карт для добора (все карты в руке).")
                    break

            if self.draw_pile:
                card = self.draw_pile.pop()
                self.hand.append(card)
                drawn += 1
                print(f" Взяли в руку карту: {card.name}")

        return drawn

    def discard_hand(self):
        """Сброс всех карт из руки в конце хода."""
        for card in self.hand:
            if hasattr(card, 'temp_cost'):
                del card.temp_cost          # сбрасываем скидку Разбойника
        self.discard_pile.extend(self.hand)
        self.hand.clear()
        print("--- Менеджер Колоды: Все карты из руки отправлены в сброс! ---")