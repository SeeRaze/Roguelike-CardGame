import random
from player import Player
from enemy import Enemy
from CombatManager import CombatManager
from Card import Strike, Defend, Splash, Ignite, Bash, Neutralize

class BotCombatManager(CombatManager):
    """
    Специальный менеджер боя для бота. 
    Он полностью убирает ручной ввод (input) и заставляет бота разыгрывать карты автоматически.
    """
    def player_turn_loop(self):
        # Бот крутит цикл хода, пока у него есть энергия и карты
        while True:
            # Если у бота не осталось карт в руке — ход окончен
            if not self.deck_manager.hand:
                break
                
            # Ищем, какие карты из руки бот в принципе может разыграть по энергии
            playable_cards = [card for card in self.deck_manager.hand if self.player.energy >= card.cost]
            
            # Если нет доступных по энергии карт — бот завершает ход
            if not playable_cards:
                break
                
            # БОТ-СТРАТЕГИЯ: Бот выбирает случайную карту из тех, на которые хватает энергии
            # (Можно усложнить логику: например, отдавать приоритет атаке или защите)
            selected_card = random.choice(playable_cards)
            
            # Разыгрываем карту
            self.player.use_energy(selected_card.cost)
            selected_card.apply(self.player, self.enemy)
            
            # Переносим в сброс
            self.deck_manager.hand.remove(selected_card)
            self.deck_manager.discard_pile.append(selected_card)
            
            if self.enemy.hp <= 0:
                break

def run_simulation(number_of_runs=500):
    """Функция, которая запускает 500 симуляций боя и собирает статистику"""
    print(f"=== ЗАПУСК АВТОМАТИЧЕСКОЙ СИМУЛЯЦИИ: {number_of_runs} БОЕВ ===")
    print("Пожалуйста, подождите, процессор считает баланс...")
    
    wins = 0
    losses = 0
    total_turns = 0
    player_leftover_hp = 0
    
    # Чтобы симуляция не спамила нам в консоль миллионами строк текста, 
    # мы временно подменим стандартную команду print на «пустышку»
    import builtins
    original_print = builtins.print
    builtins.print = lambda *args, **kwargs: None
    
    for _ in range(number_of_runs):
        # Каждый раз создаем свежих бойцов и колоду
        player = Player(hp=80)
        enemy = Enemy(name="Тестовый Культист", hp=250)
        
        # Задаем колоду, баланс которой хотим проверить
        test_deck = [
            Strike(), Strike(), Defend(), Defend(),
            Bash(), Neutralize(), Splash(), Ignite()
        ]
        
        # Запускаем бой через нашего бота
        combat = BotCombatManager(player, enemy, test_deck)
        combat.start_combat()
        
        # Собираем данные
        total_turns += combat.turn_count
        if player.hp > 0:
            wins += 1
            player_leftover_hp += player.hp
        else:
            losses += 1
            
    # Возвращаем нормальный print обратно, чтобы вывести итоги
    builtins.print = original_print
    
    # Считаем проценты
    win_rate = (wins / number_of_runs) * 100
    avg_turns = total_turns / number_of_runs
    avg_hp = (player_leftover_hp / wins) if wins > 0 else 0
    
    print("\n" + "="*50)
    print(" ИТОГИ СИМУЛЯЦИИ БАЛАНСА")
    print("="*50)
    print(f" Всего симулировано боев: {number_of_runs}")
    print(f" Побед Бота:             {wins} ({win_rate:.1f}%)")
    print(f" Поражений Бота:         {losses} ({100 - win_rate:.1f}%)")
    print(f" Средняя длина боя:       {avg_turns:.1f} ходов")
    print(f" Среднее HP после победы: {avg_hp:.1f} / 80")
    print("="*50)

if __name__ == "__main__":
    run_simulation(500) # Запускаем 500 боев
