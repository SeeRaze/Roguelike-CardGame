from managers.network_manager import send_run_record
import random
import math
import os
from core.relics import LuckyClover, SpikedBracelet
from core.players import Warrior
from core.cards import (
    create_strike, create_defend, create_heavy_blade, create_iron_wall,
    create_bash, create_neutralize, create_intimidate,
    create_ignite, create_fire_breath,
    create_splash, create_rain_cloud,
    create_poison_stab, create_toxic_cloud, create_acid_shield
)

# Типы узлов и их веса для генерации (этажи 2-18)
NODE_WEIGHTS = {
    "COMBAT":   55,
    "CAMPFIRE": 15,
    "SHOP":     10,
    "CHEST":    12,
    "EVENT":    8,
}

FLOORS_PER_ACT = 20  # Этажей до босса


class MapNode:
    """Один узел на карте: тип комнаты + список соединений вниз."""
    def __init__(self, node_type: str, col: int, row: int):
        self.node_type = node_type  # COMBAT / CAMPFIRE / SHOP / CHEST / EVENT / BOSS
        self.col = col              # 0, 1, 2 — колонка
        self.row = row              # 0..19 — строка (0 = первый этаж)
        self.connections = []       # индексы колонок узлов СЛЕДУЮЩЕЙ строки


class GameManager:
    """Глобальный мозг и менеджер прогрессии игры."""
    def __init__(self):
        try:
            self.player_name = os.getlogin()
        except:
            self.player_name = "Искатель"

        print(f"--- GameManager: Авторизован пользователь ОС: {self.player_name} ---")

        self.stats = {
            "name": self.player_name,
            "max_floor": 1,
            "monsters_killed": 0,
            "bosses_killed": 0,
            "max_damage_dealt": 0
        }

        self.player = Warrior()
        self.player_gold = 100
        self.current_floor = 1
        self.removal_count = 0
        self.relics = []
        self.current_deck = self.player.get_starter_deck()
        self.current_state = "MAIN_MENU"
        self.active_combat = None
        self.event_result = None   # результат последнего события

        # Карта: список строк, каждая строка — список из 3 MapNode
        self.map_grid = []
        # Текущий путь игрока: список (row, col) пройденных узлов
        self.player_path = []
        # Колонка, выбранная игроком на текущей строке
        self.current_col = 1  # стартуем по центру

    def start_game(self):
        print("--- GameManager: Глобальный мозг запущен в режиме Главного Меню! ---")

    def get_removal_price(self) -> int:
        return (15 + self.current_floor * 2) + self.removal_count * 25

    # ------------------------------------------------------------------
    # ГЕНЕРАЦИЯ КАРТЫ
    # ------------------------------------------------------------------

    def generate_new_map_progression(self):
        """Генерирует сетку 20×3 узлов с маршрутами в стиле Slay the Spire."""
        self.map_grid.clear()
        self.player_path.clear()
        self.current_col = 1

        # 1. Создаём узлы
        for row in range(FLOORS_PER_ACT):
            row_nodes = []
            for col in range(3):
                node_type = self._pick_node_type(row)
                row_nodes.append(MapNode(node_type, col, row))
            self.map_grid.append(row_nodes)

        # 2. Строим связи (каждый узел соединяется с 1-2 соседними в следующей строке)
        for row in range(FLOORS_PER_ACT - 1):
            for col in range(3):
                node = self.map_grid[row][col]
                # Основная связь — прямо вперёд
                targets = {col}
                # Случайно добавляем диагональ (не выходя за границы)
                if col > 0 and random.random() < 0.4:
                    targets.add(col - 1)
                if col < 2 and random.random() < 0.4:
                    targets.add(col + 1)
                node.connections = sorted(targets)

        # 3. Гарантируем, что каждый узел предпоследней строки ведёт к боссу
        for col in range(3):
            self.map_grid[FLOORS_PER_ACT - 2][col].connections = [1]  # все к центру

    def _pick_node_type(self, row: int) -> str:
        """Выбирает тип узла по правилам баланса."""
        # Первый этаж — только бои
        if row == 0:
            return "COMBAT"
        # Последний этаж — босс
        if row == FLOORS_PER_ACT - 1:
            return "BOSS"
        # Предпоследний — костёр или магазин (подготовка к боссу)
        if row == FLOORS_PER_ACT - 2:
            return random.choice(["CAMPFIRE", "SHOP"])
        # Остальные — взвешенный рандом
        types = list(NODE_WEIGHTS.keys())
        weights = list(NODE_WEIGHTS.values())
        return random.choices(types, weights=weights, k=1)[0]

    # ------------------------------------------------------------------
    # НАВИГАЦИЯ ПО КАРТЕ
    # ------------------------------------------------------------------

    def setup_next_floor(self):
        """Вызывается после каждой комнаты. Переходим на карту или к боссу."""
        local_step = (self.current_floor - 1) % FLOORS_PER_ACT + 1

        if local_step == 1:
            print(f"\n--- Генерируем новый акт для этажей "
                  f"{self.current_floor}-{self.current_floor + FLOORS_PER_ACT - 1} ---")
            self.generate_new_map_progression()

        if local_step == FLOORS_PER_ACT:
            print(" >>> БОСС! <<<")
            self.enter_chosen_room("COMBAT")
        else:
            self.current_state = "MAP"

    def enter_chosen_room(self, chosen_room_type: str, col: int = None):
        """Игрок выбрал узел на карте. col — выбранная колонка."""
        if col is not None:
            self.current_col = col
            row = (self.current_floor - 1) % FLOORS_PER_ACT
            self.player_path.append((row, col))

        self.current_state = chosen_room_type

        if self.current_state == "COMBAT":
            self.spawn_procedural_enemy()

    def get_available_nodes(self):
        """Возвращает узлы, доступные для выбора на текущем шаге."""
        row = (self.current_floor - 1) % FLOORS_PER_ACT
        if not self.map_grid:
            return []

        # Первый шаг — все три узла доступны
        if row == 0:
            return self.map_grid[0]

        # Иначе — только те, куда ведут связи из текущей позиции
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
        floor = self.current_floor
        local_step = (floor - 1) % FLOORS_PER_ACT + 1
        tier = (floor - 1) // FLOORS_PER_ACT + 1

        enemy_hp  = 20 + (floor * 3) + (tier * 10)
        enemy_dmg = 3  + (tier * 1)
        enemy_shld = 2

        is_boss = (local_step == FLOORS_PER_ACT)

        if is_boss:
            enemy_hp   = int(enemy_hp * 2.2)
            enemy_dmg  = int(enemy_dmg * 1.3)
            enemy_shld = int(enemy_shld * 1.8)
            boss_titles = ["Древний Страж Башни", "Верховный Культист Неона", "Гидра Стихий"]
            e_name = f"👑 БОСС: {random.choice(boss_titles)} [Ярус {tier + 1}]"
        else:
            prefixes = ["Дикий", "Проклятый", "Чумной", "Стальной", "Адский"]
            types    = ["Слизень", "Культист", "Гоблин", "Орк", "Страж"]
            e_name   = f"{random.choice(prefixes)} {random.choice(types)} [Этаж {floor}]"

        from core.enemies import Cultist, SlimeAndGoblins, BossTitan, Enemy

        if is_boss:
            enemy = BossTitan(name=e_name, hp=enemy_hp, max_hp=enemy_hp)
        elif "Культист" in e_name or "Страж" in e_name:
            enemy = Cultist(name=e_name, hp=enemy_hp, max_hp=enemy_hp)
        elif "Слизень" in e_name or "Гоблин" in e_name or "Орк" in e_name:
            enemy = SlimeAndGoblins(name=e_name, hp=enemy_hp, max_hp=enemy_hp)
        else:
            enemy = Enemy(name=e_name, hp=enemy_hp, max_hp=enemy_hp)

        enemy.base_test_damage = enemy_dmg
        enemy.base_test_shield = enemy_shld
        if is_boss:
            enemy.shield = enemy_shld * 2

        from managers.CombatManager import CombatManager
        self.active_combat = CombatManager(self.player, enemy, self.current_deck, self)

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
            from core.relics import (LuckyClover, SpikedBracelet,
                                     ЭнергоЯдро, ТочильныйКамень,
                                     ДревнееОгниво, НамокшаяРукавица)
            all_pool = [LuckyClover, SpikedBracelet, ЭнергоЯдро,
                        ТочильныйКамень, ДревнееОгниво, НамокшаяРукавица]
            current_relic_names = [r.name for r in self.relics]
            available_relics = [r for r in all_pool
                                if r().name not in current_relic_names]
            if available_relics:
                dropped_relic_class = random.choice(available_relics)
                new_relic = dropped_relic_class()
                self.relics.append(new_relic)
                if new_relic.name == "Энерго-Ядро":
                    self.player.max_energy += 1
                log_msg += f" [НАГРАДА] Артефакт: '{new_relic.name}'!"

        if self.active_combat:
            self.active_combat.add_log_message(log_msg)
    def add_card(self, card):
        """Добавляет карту в текущую колоду игрока."""
        self.current_deck.append(card)    