from managers.DeckManager import DeckManager
from managers.network_manager import send_run_record


class CombatManager:
    """Менеджер боя, адаптированный под графический движок Pygame."""

    def __init__(self, player, enemy, starting_deck, game_manager=None):
        self.gm = game_manager
        self.player = player
        self.enemy = enemy
        self.deck_manager = DeckManager(starting_deck)
        self.turn_count = 1

        self.combat_log = []
        self.add_log_message("=== БОЙ НАЧАЛСЯ ===")

        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_combat_start(self)

        self.start_turn_phase()

    def add_log_message(self, message):
        self.combat_log.append(message)
        if len(self.combat_log) > 6:
            self.combat_log.pop(0)

    def start_turn_phase(self):
        """Начало нового хода: подготовка ресурсов игрока."""
        self.enemy.choose_intent()

        # Сохраняем щит ДО сброса -- для Железной Воли
        self.player._iron_will_shield = self.player.shield
        self.player.shield = 0
        self.player.energy = self.player.max_energy

        bonus = getattr(self.player, "bonus_draw", 0)
        self.deck_manager.draw_cards(5 + bonus)

        # ПАССИВ РАЗБОЙНИКА: снижаем кост случайной карты в руке на 1
        if type(self.player).__name__ == "Rogue" and self.deck_manager.hand:
            import random
            card = random.choice(self.deck_manager.hand)
            original = card.cost
            card.temp_cost = max(0, original - 1)
            self.add_log_message(
                f" [РАЗБОЙНИК] {card.name}: стоимость {original} -> {card.temp_cost}"
            )

        self.add_log_message(f"--- НАЧАЛО ХОДА {self.turn_count} ---")

        # Хук on_turn_start -- ПОСЛЕ сброса щита, чтобы Железная Воля могла восстановить
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_turn_start(self)

    def play_card_by_index(self, card_index):
        """Разыгрывание карты по её порядковому номеру в руке."""
        if card_index < 0 or card_index >= len(self.deck_manager.hand):
            return False

        selected_card = self.deck_manager.hand[card_index]
        effective_cost = getattr(selected_card, 'temp_cost', selected_card.cost)

        if self.player.energy < effective_cost:
            self.add_log_message("[!] Не хватает энергии!")
            return False

        self.player.use_energy(effective_cost)
        self.add_log_message(f"Вы разыграли: {selected_card.name}")

        selected_card.apply(self.player, self.enemy, self)

        # Хук on_card_played
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_card_played(selected_card, self)

        # Сбрасываем temp_cost после разыгрывания
        if hasattr(selected_card, 'temp_cost'):
            del selected_card.temp_cost

        self.deck_manager.hand.remove(selected_card)
        if getattr(selected_card, 'exile', False):
            self.deck_manager.exile_pile.append(selected_card)
            self.add_log_message(
                f" [ИЗГНАНИЕ] {selected_card.name} изгнана до конца боя."
            )
        else:
            self.deck_manager.discard_pile.append(selected_card)
        return True

    def end_turn_phase(self):
        """Конец хода игрока: фаза действий монстра."""
        self.add_log_message("Вы завершили ход.")
        self.deck_manager.discard_hand()

        if self.enemy.hp > 0:
            self.enemy.shield = 0
            self.enemy.execute_intent(self.player, self)
            self.enemy.tick_statuses(self)

        self.player.tick_statuses(self)

        if self.enemy.hp <= 0:
            self.add_log_message("=== ВРАГ ПОВЕРЖЕН! ===")
            return

        if self.player.hp > 0:
            self.turn_count += 1
            self.start_turn_phase()

        if self.player.hp <= 0:
            self.player.hp = 0
            print("[СИСТЕМА] Здоровье игрока упало до 0!")

            current_floor = self.gm.current_floor if self.gm else 1
            kills_count = (
                self.gm.stats["monsters_killed"] + self.gm.stats["bosses_killed"]
                if self.gm else 0
            )
            max_dmg = self.gm.stats["max_damage_dealt"] if self.gm else 0

            print("[СЕТЬ] Отправляем рекорд напрямую в Google...")
            send_run_record(
                max_floor=current_floor, kills=kills_count, max_damage=max_dmg
            )

            if self.gm:
                from ui.LeaderboardView import LeaderboardView
                LeaderboardView.load_data()
                self.gm.current_state = "LEADERBOARD"