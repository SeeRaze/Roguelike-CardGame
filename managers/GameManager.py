import random
import os
from managers.network_manager import send_run_record
from managers.MapGenerator    import generate_map, FLOORS_PER_ACT
from core.relics              import LuckyClover, SpikedBracelet, RELIC_POOL, ALL_RELICS
from core.rarity              import Rarity
from core.players             import Warrior
from core.cards import (
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_bash, create_neutralize, create_intimidate,
    create_ignite, create_fire_breath,
    create_splash, create_rain_cloud,
    create_poison_stab, create_toxic_cloud, create_acid_shield,
)

# Реестр врагов: имя-ключ -> класс.
# Добавить врага = один импорт + одна строка здесь.
from core.enemies import Cultist, SlimeAndGoblins, BossTitan, Enemy

ENEMY_REGISTRY = {
    "Культист": Cultist,
    "Страж":    Cultist,
    "Слизень":  SlimeAndGoblins,
    "Гоблин":   SlimeAndGoblins,
    "Орк":      SlimeAndGoblins,
}


class GameManager:
    """Глобальный мозг и менеджер прогрессии игры."""

    def __init__(self):
        try:
            self.player_name = os.getlogin()
        except:
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
        self.current_floor = 1
        self.removal_count = 0
        self.relics        = []
        self.current_deck  = self.player.get_starter_deck()
        self.current_state = "MAIN_MENU"
        self.active_combat = None
        self.event_result  = None

        self.map_grid    = []
        self.player_path = []
        self.current_col = 1

    def start_game(self):
        print("--- GameManager: Глобальный мозг запущен в режиме Главного Меню! ---")

    def get_removal_price(self) -> int:
        return (15 + self.current_floor * 2) + self.removal_count * 25

    def add_card(self, card):
        self.current_deck.append(card)

    # ------------------------------------------------------------------
    # НАВИГАЦИЯ
    # ------------------------------------------------------------------

    def setup_next_floor(self):
        """Вызывается после каждой комнаты."""
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
        """Игрок выбрал узел на карте."""
        if col is not None:
            self.current_col = col
            row = (self.current_floor - 1) % FLOORS_PER_ACT
            self.player_path.append((row, col))

        self.current_state = chosen_room_type

        if self.current_state == "COMBAT":
            self.spawn_procedural_enemy()

    def get_available_nodes(self):
        """Узлы, доступные для выбора на текущем шаге."""
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

    # ------------------------------------------------------------------
    # БОЙ
    # ------------------------------------------------------------------

    def spawn_procedural_enemy(self):
        """Процедурная генерация врага по этажу."""
        floor      = self.current_floor
        local_step = (floor - 1) % FLOORS_PER_ACT + 1
        tier       = (floor - 1) // FLOORS_PER_ACT + 1

        enemy_hp   = 20 + (floor * 3) + (tier * 10)
        enemy_dmg  = 3  + (tier * 1)
        enemy_shld = 2
        is_boss    = (local_step == FLOORS_PER_ACT)

        if is_boss:
            enemy_hp   = int(enemy_hp   * 2.2)
            enemy_dmg  = int(enemy_dmg  * 1.3)
            enemy_shld = int(enemy_shld * 1.8)
            boss_titles = ["Древний Страж Башни", "Верховный Культист Неона",
                           "Гидра Стихий"]
            e_name = f"БОСС: {random.choice(boss_titles)} [Ярус {tier + 1}]"
            enemy_class = BossTitan
        else:
            prefixes = ["Дикий", "Проклятый", "Чумной", "Стальной", "Адский"]
            types    = list(ENEMY_REGISTRY.keys())
            e_type   = random.choice(types)
            e_name   = f"{random.choice(prefixes)} {e_type} [Этаж {floor}]"
            enemy_class = ENEMY_REGISTRY.get(e_type, Enemy)

        enemy = enemy_class(name=e_name, hp=enemy_hp, max_hp=enemy_hp)
        enemy.base_test_damage = enemy_dmg
        enemy.base_test_shield = enemy_shld
        if is_boss:
            enemy.shield = enemy_shld * 2

        from managers.CombatManager import CombatManager
        self.active_combat = CombatManager(
            self.player, enemy, self.current_deck, self
        )

    # ------------------------------------------------------------------
    # НАГРАДЫ
    # ------------------------------------------------------------------

    def distribute_combat_rewards(self):
        """Начисление золота, ролл реликвий, запись статистики."""
        if self.current_floor > self.stats["max_floor"]:
            self.stats["max_floor"] = self.current_floor

        local_step = (self.current_floor - 1) % FLOORS_PER_ACT + 1

        if local_step == FLOORS_PER_ACT:
            self.stats["bosses_killed"] += 1
        else:
            self.stats["monsters_killed"] += 1

        gold_drop = random.randint(20, 35) + (self.current_floor * 3)
        self.player_gold += gold_drop
        log_msg = f"Залутано +{gold_drop} монет!"

        if random.randint(1, 2) == 1:
            # Ролл редкости: 60% COMMON, 30% UNCOMMON, 10% RARE
            roll = random.random()
            if roll < 0.60:
                rarity = Rarity.COMMON
            elif roll < 0.90:
                rarity = Rarity.UNCOMMON
            else:
                rarity = Rarity.RARE

            pool = RELIC_POOL.get(rarity, [])
            # Фолбэк: если пул пуст — берём из ALL_RELICS
            if not pool:
                pool = ALL_RELICS

            current_names    = {r.name for r in self.relics}
            available_relics = [r for r in pool if r().name not in current_names]

            if not available_relics:
                available_relics = [r for r in ALL_RELICS
                                    if r().name not in current_names]

            if available_relics:
                new_relic = random.choice(available_relics)()
                self.relics.append(new_relic)
                log_msg += (f" [НАГРАДА] Артефакт [{rarity.value}]: "
                            f"'{new_relic.name}'!")

        if self.active_combat:
            self.active_combat.add_log_message(log_msg)