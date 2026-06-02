from managers.DeckManager import DeckManager
from managers.network_manager import send_run_record

class CombatManager:
    """Менеджер боя, адаптированный под графический движок Pygame."""
    def __init__(self, player, enemy, starting_deck, game_manager=None):
        # 1. Привязываем ссылку на GameManager до любых фаз
        self.gm = game_manager

        self.player = player
        self.enemy = enemy
        self.deck_manager = DeckManager(starting_deck)
        self.turn_count = 1

        self.combat_log = []
        self.add_log_message("=== БОЙ НАЧАЛСЯ ===")

        # 2. ИСПРАВЛЕНО: реликвии срабатывают ДО первого хода
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_combat_start(self)

        # 3. Только после реликвий запускаем первый ход
        self.start_turn_phase()

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

        if self.player.energy < selected_card.cost:
            self.add_log_message("[!] Не хватает энергии!")
            return False

        self.player.use_energy(selected_card.cost)
        self.add_log_message(f"Вы разыграли: {selected_card.name}")

        selected_card.apply(self.player, self.enemy, self)

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

            self.enemy.execute_intent(self.player, self)
            self.enemy.tick_statuses()

        # В конце раунда тикают дебаффы игрока
        self.player.tick_statuses()

        # ИСПРАВЛЕНО: проверяем победу ДО начала нового хода
        # Если враг умер (в т.ч. от яда) -- не начинаем новый ход
        if self.enemy.hp <= 0:
            self.add_log_message("=== ВРАГ ПОВЕРЖЕН! ===")
            return  # InputHandler поймает enemy.hp <= 0 и выдаст награду

        # Если все выжили -- переходим на новый ход
        if self.player.hp > 0:
            self.turn_count += 1
            self.start_turn_phase()

        # Поражение: игрок умер
        if self.player.hp <= 0:
            self.player.hp = 0
            print("[СИСТЕМА] Здоровье игрока упало до 0! Запускаем финал катки...")

            from managers.network_manager import send_run_record

            current_floor = self.gm.current_floor if self.gm else 1
            kills_count = self.gm.stats["monsters_killed"] + self.gm.stats["bosses_killed"] if self.gm else 0
            max_dmg = self.gm.stats["max_damage_dealt"] if self.gm else 0

            print("[СЕТЬ] Отправляем рекорд напрямую в Google...")
            send_run_record(max_floor=current_floor, kills=kills_count, max_damage=max_dmg)

            if self.gm:
                from ui.LeaderboardView import LeaderboardView
                LeaderboardView.load_data()
                self.gm.current_state = "LEADERBOARD"