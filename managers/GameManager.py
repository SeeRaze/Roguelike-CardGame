import os
from managers.MapGenerator    import generate_map, FLOORS_PER_ACT
from managers.EnemySpawner    import build_enemy_group, ENEMY_REGISTRY
from managers.RewardManager   import build_rewards
from core.players             import Warrior
from core.forge               import assign_forge_uid, combat_fp_gain, next_cap_for_boss

# ENEMY_REGISTRY реэкспортируется для обратной совместимости (живёт в EnemySpawner).
__all__ = ["GameManager", "ENEMY_REGISTRY"]


class GameManager:
    """Глобальный мозг и менеджер прогрессии игры."""

    def __init__(self):
        try:
            self.player_name = os.getlogin()
        except Exception:
            self.player_name = "Искатель"

        print(f"--- GameManager: Авторизован пользователь ОС: {self.player_name} ---")

        self.stats = {
            "name":             self.player_name,
            "max_floor":        1,
            "monsters_killed":  0,
            "bosses_killed":    0,
            "max_damage_dealt": 0,
        }

        self.player        = Warrior()
        self.player_gold   = 100
        self.player_keys   = 0
        self.current_floor = 1
        self.removal_count = 0
        self.relics        = []
        self.current_deck  = self.player.get_starter_deck()
        # Паспорт ковки: каждой карте старт-колоды — стабильный uid инстанса (39.5).
        for card in self.current_deck:
            assign_forge_uid(self.player, card)
        self.current_state = "MAIN_MENU"
        self.active_combat = None
        self.event_result  = None
        self.event_result_card = None

        self.map_grid    = []
        self.player_path = []
        self.current_col = 1

    def start_game(self):
        print("--- GameManager: Глобальный мозг запущен в режиме Главного Меню! ---")

    def get_removal_price(self) -> int:
        base = (15 + self.current_floor * 2) + self.removal_count * 25
        if any(r.name == "Проклятая Корона" for r in self.relics):
            base *= 2
        return base

    def add_card(self, card):
        assign_forge_uid(self.player, card)   # стабильный uid паспорта ковки (39.5)
        self.current_deck.append(card)

    # --- НАВИГАЦИЯ ПО КАРТЕ ---

    def setup_next_floor(self):
        local_step = (self.current_floor - 1) % FLOORS_PER_ACT + 1

        if local_step == 1:
            print(f"\n--- Генерируем новый акт: этажи "
                  f"{self.current_floor}-{self.current_floor + FLOORS_PER_ACT - 1} ---")
            self.map_grid    = generate_map()
            self.player_path = []
            self.current_col = 1

        if local_step == FLOORS_PER_ACT:
            print(" >>> БОСС! <<<")
            self.enter_chosen_room("COMBAT")
        else:
            self.current_state = "MAP"

    def enter_chosen_room(self, chosen_room_type: str, col: int = None):
        if col is not None:
            self.current_col = col
            row = (self.current_floor - 1) % FLOORS_PER_ACT
            self.player_path.append((row, col))

        is_elite = (chosen_room_type == "ELITE")

        # ELITE — это подтип COMBAT, состояние всегда "COMBAT"
        self.current_state = "COMBAT" if is_elite else chosen_room_type

        if self.current_state == "COMBAT":
            self.spawn_procedural_enemy(is_elite=is_elite)

    def get_available_nodes(self):
        row = (self.current_floor - 1) % FLOORS_PER_ACT
        if not self.map_grid:
            return []
        if row == 0:
            return self.map_grid[0]
        if not self.player_path:
            return self.map_grid[row]
        prev_row, prev_col = self.player_path[-1]
        prev_node = self.map_grid[prev_row][prev_col]
        return [self.map_grid[row][c] for c in prev_node.connections]

    # --- БОЙ (спавн врага -> EnemySpawner) ---

    def spawn_procedural_enemy(self, is_elite: bool = False):
        """Создать врага/группу для текущего этажа и запустить бой.

        Статы/имя/класс считает EnemySpawner.build_enemy_group; здесь — только
        привязка к бою (создание CombatManager и active_combat)."""
        enemies = build_enemy_group(self.current_floor, is_elite)
        from managers.CombatManager import CombatManager
        self.active_combat = CombatManager(
            self.player, enemies, self.current_deck, self
        )

    # --- НАГРАДЫ (расчёт -> RewardManager) ---

    def distribute_combat_rewards(self):
        if self.current_state != "COMBAT":
            return

        # Сброс боевого состояния игрока (щит + все боевые статусы)
        self.player.energy = self.player.max_energy
        self.player.reset_combat_statuses()

        # Хук on_combat_end — передаём active_combat для полного доступа
        for relic in self.relics:
            relic.on_combat_end(self.player, self.active_combat)

        if self.current_floor > self.stats["max_floor"]:
            self.stats["max_floor"] = self.current_floor

        local_step = (self.current_floor - 1) % FLOORS_PER_ACT + 1
        is_boss    = (local_step == FLOORS_PER_ACT)
        is_elite   = getattr(getattr(self.active_combat, 'enemy', None),
                             'is_elite', False)

        # Приток FP за выжитый бой (ковка карт, 39.5): динамический по акту +
        # бонус босса ×ARTIFACT_FP_MULT. Та же формула, что у sim-бота
        # (core.forge.combat_fp_gain) ⇒ живая экономика = откалиброванная.
        self.player.forge_points += combat_fp_gain(self.current_floor, is_boss)

        # Хук on_boss_defeated — персистентный слой по забегу (растущие реликвии:
        # «каждый босс ×N»). Триггерит только на босс-этажах (20/40/60/80/100).
        if is_boss:
            for relic in self.relics:
                relic.on_boss_defeated(self.player, self.active_combat)
            # Босс снимает кап уровня карты до следующего майлстоуна (увязка шкал
            # §3): 20→5, 40→10, 60→15, 80→20, 100→25. До босса уровни заперты —
            # железная защита ранней стены (×mult недостижим раньше этажа ~60).
            new_cap = next_cap_for_boss(self.current_floor)
            if new_cap is not None and new_cap > self.player.forge_level_cap:
                self.player.forge_level_cap = new_cap

        # Статистика убийств теперь в CombatManager._check_enemy_death

        # Расчёт наград (золото/реликвия/ключ) -- в RewardManager.
        self.pending_rewards = build_rewards(self, is_boss, is_elite)
        self.current_state   = "VICTORY"