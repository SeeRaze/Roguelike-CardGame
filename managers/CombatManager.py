# Указываем точный путь: DeckManager лежит в одной папке с CombatManager (в managers)
from managers.DeckManager import DeckManager

class CombatManager:
    """Менеджер боя, адаптированный под графический движок Pygame."""
    def __init__(self, player, enemy, starting_deck, game_manager=None):
        # 1. СРАЗУ намертво привязываем ссылку на мозг игры, до любых фаз и доборов!
        self.gm = game_manager
        
        # 2. А все остальные строчки опускаем ниже
        self.player = player
        self.enemy = enemy
        self.deck_manager = DeckManager(starting_deck)
        self.turn_count = 1
        
        self.combat_log = []
        self.add_log_message("=== БОЙ НАЧАЛСЯ ===")
        
        # 3. Запускаем фазу хода, когда все менеджеры уже знают друг друга в памяти
        self.start_turn_phase()
        
        # --- ТРИГГЕР РЕЛИКВИЙ НА СТАРТЕ БОЯ ---
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_combat_start(self)

    def add_log_message(self, message):
        """Метод добавления новой строчки в лог (хранит до 6 событий)"""
        self.combat_log.append(message)
        if len(self.combat_log) > 6:
            self.combat_log.pop(0)

    def start_turn_phase(self):
        """Начало нового хода: подготовка ресурсов игрока"""
        self.enemy.choose_intent()
        
        # Сбрасываем щит игрока в начале его хода
        self.player.shield = 0
        
        self.player.energy = self.player.max_energy
        self.deck_manager.draw_cards(5)
        self.add_log_message(f"--- НАЧАЛО ХОДА {self.turn_count} ---")

    def play_card_by_index(self, card_index):
        """Разыгрывание карты по её порядковому номеру в руке"""
        if card_index < 0 or card_index >= len(self.deck_manager.hand):
            return False
            
        selected_card = self.deck_manager.hand[card_index]
        
        # Проверяем ресурсы энергии
        if self.player.energy < selected_card.cost:
            self.add_log_message("[!] Не хватает энергии!")
            return False
            
        # Списываем стоимость
        self.player.use_energy(selected_card.cost)
        self.add_log_message(f"Вы разыграли: {selected_card.name}")
        
        # Применяем эффект карты к объектам, передавая этот менеджер (self) для записи урона в лог
        selected_card.apply(self.player, self.enemy, self)
        
        # Переносим карту в сброс
        self.deck_manager.hand.remove(selected_card)
        self.deck_manager.discard_pile.append(selected_card)
        
        return True

    def end_turn_phase(self):
        """Конец хода игрока: фаза действий монстра"""
        self.add_log_message("Вы завершили ход.")
        self.deck_manager.discard_hand()
        
        if self.enemy.hp > 0:
            # Монстр сбрасывает старый щит перед своим действием
            self.enemy.shield = 0
            
            # Враг выполняет свое намерение
            self.enemy.execute_intent(self.player, self)
            self.enemy.tick_statuses()
            
        # В конце всего раунда тикают дебаффы игрока
        self.player.tick_statuses()
        
        # Если все выжили, переходим на новый ход
        if self.player.hp > 0 and self.enemy.hp > 0:
            self.turn_count += 1
            self.start_turn_phase()
