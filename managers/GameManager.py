import random
import math
# Импортируем наших живых персонажей и фабрику карт из папки core
from core.Relic import LuckyClover, SpikedBracelet
from core.player import Player
from core.enemy import Enemy
from core.Card import create_strike, create_defend, create_bash, create_neutralize, create_splash, create_ignite

class GameManager:
    """Глобальный мозг и менеджер прогрессии игры. Хранит золото, этажи и колоду."""
    def __init__(self):
        # 1. Создаем игрока один раз на всю игру!
        self.player = Player(hp=80)
        self.player_gold = 60  # Стартовый капитал для Торговца
        self.current_floor = 1
        self.removal_price = 25  # Базовая цена за сжигание карты в магазине
                # Сумка для пассивных артефактов
        self.relics = []  # никаких артефактов на старте, чистый хардкор!

        # 2. Формируем стартовую колоду из чистой базы через новые фабричные кирпичики
        self.current_deck = [
            create_strike(), create_strike(), create_strike(), create_strike(),
            create_defend(), create_defend(), create_defend(), create_defend()
        ]
        
        # ТЕКУЩЕЕ СОСТОЯНИЕ ИГРЫ: Стартуем с Главного меню!
        self.current_state = "MAIN_MENU"
        self.active_combat = None
        self.procedural_map = []

    def start_game(self):
        """Теперь старт игры просто рапортует в консоль, не запуская этажи раньше времени"""
        print("--- GameManager: Глобальный мозг запущен в режиме Главного Меню! ---")

    def setup_next_floor(self):
        """Процедурно генерирует карту развилок на 10 этажей наперед и контролирует баланс."""
        # --- НОВЫЙ СТАНДАРТ: Шаг яруса теперь от 1 до 10! ---
        local_step = (self.current_floor - 1) % 10 + 1

        # Если мы на первом шаге нового яруса башни (1, 11, 21...) — генерируем карту на 10 этажей
        if local_step == 1:
            print(f"\n--- GameManager: Генерируем новый ярус башни для этажей {self.current_floor}-{self.current_floor+9} ---")
            self.generate_new_map_progression()
            
        # Если игрок дошел до 10-го финального шага — он безвыборно идет к БОССУ
        if local_step == 10:
            print(f" >>> ВНИМАНИЕ: Вход в Логово Главного Босса яруса! <<<")
            self.enter_chosen_room("COMBAT")
        else:
            # В остальных случаях отправляем на экран карты развилок для выбора пути
            self.current_state = "MAP"

    def generate_new_map_progression(self):
        """Создает массив из 10 развилок. Идеальный холст под будущие события."""
        self.procedural_map.clear()
        
        # Цикл генерирует 10 комнат вперед
        for f in range(1, 11):
            if f == 1:
                self.procedural_map.append(["COMBAT", "COMBAT"])
            elif f == 9:
                # На 9-м этаже (прямо перед боссом) всегда гарантированный привал / закуп
                self.procedural_map.append(["CAMPFIRE", "SHOP"])
            elif f == 10:
                # Финал яруса
                self.procedural_map.append(["COMBAT", "COMBAT"])
            else:
                # 2-8 этажи: случайное распределение
                # В будущем сюда легко добавятся события "EVENT" или "TREASURE"
                room_a = random.choices(["COMBAT", "CAMPFIRE", "SHOP"], weights=[65, 20, 15], k=1)[0]
                room_b = random.choices(["COMBAT", "CAMPFIRE", "SHOP"], weights=[65, 20, 15], k=1)[0]
                self.procedural_map.append([room_a, room_b])

    def spawn_procedural_enemy(self):
        """Сглаженный калькулятор баланса под 10-этажный формат."""
        floor = self.current_floor
        local_step = (floor - 1) % 10 + 1
        tier = (floor - 1) // 10 + 1
        
        # --- СМЯГЧЕНИЕ БАЛАНСА (Чтобы игра стала проходимой!) ---
        # Рядовые враги теперь растут медленнее: ХП +8 за этаж, атака +1 за этаж (было +15 и +2)
        enemy_hp = 40 + (floor * 8) + (tier * 25)
        enemy_dmg = 5 + (floor * 1) + (tier * 4)
        enemy_shld = int(3 + (floor * 1.0))
        
        # Проверяем, финал ли это акта (10-й шаг яруса)
        is_boss = (local_step == 10)
        
        if is_boss:
            # Босс яруса монументален
            enemy_hp = int(enemy_hp * 2.2)  # Около 250-300 HP
            enemy_dmg = int(enemy_dmg * 1.3) # Около 20-22 урона
            enemy_shld = int(enemy_shld * 1.8)
            
            boss_titles = ["Древний Страж Башни", "Верховный Культист Неона", "Гидра Стихий"]
            e_name = f"👑 БОСС: {random.choice(boss_titles)} [Ярус {tier + 1}]"
        else:
            prefixes = ["Дикий", "Проклятый", "Чумной", "Стальной", "Адский"]
            types = ["Слизень", "Культист", "Гоблин", "Орк", "Страж"]
            e_name = f"{random.choice(prefixes)} {random.choice(types)} [Этаж {floor}]"
        
        enemy = Enemy(name=e_name, hp=enemy_hp, max_hp=enemy_hp)
        enemy.base_test_damage = enemy_dmg
        enemy.base_test_shield = enemy_shld
        
        if is_boss:
            enemy.shield = enemy_shld * 2
            
        from managers.CombatManager import CombatManager
        self.active_combat = CombatManager(self.player, enemy, self.current_deck, self)



    def enter_chosen_room(self, chosen_room_type):
        """Метод вызывается, когда игрок физически кликнул по кнопке выбора на карте"""
        self.current_state = chosen_room_type
        
        if self.current_state == "COMBAT":
            self.spawn_procedural_enemy()
        # Для костра и магазина дополнительных спавнов не нужно, их экраны просто откроются в draw()


    def spawn_procedural_enemy(self):
        """Автоматический калькулятор баланса статов мобов и Боссов."""
        floor = self.current_floor
        local_step = (floor - 1) % 10 + 1
        tier = (floor - 1) // 10 + 1
        
        # 1. МАТЕМАТИКА БАЗОВОГО РОСТА СТАДЫ ВРАГА
        enemy_hp = 45 + (floor * 15) + (tier * 20)
        enemy_dmg = 6 + (floor * 2) + (tier * 3)
        enemy_shld = int(4 + (floor * 1.5))
        
        # Проверяем: если это 10-й шаг яруса — перед нами БОСС!
        is_boss = (local_step == 10)
        
        if is_boss:
            # Накатываем босс-множители баланса
            enemy_hp = int(enemy_hp * 2.5)
            enemy_dmg = int(enemy_dmg * 1.3)
            enemy_shld = int(enemy_shld * 2.0)
            
            # Придумываем эпичные имена для Боссов
            boss_titles = ["Хранитель Очага", "Архимаг Пустоты", "Стальной Разрушитель"]
            e_name = f"👑 БОСС: {random.choice(boss_titles)} [Ярус {tier}]"
        else:
            # Обычные процедурные монстры
            prefixes = ["Дикий", "Проклятый", "Чумной", "Стальной", "Адский"]
            types = ["Слизень", "Культист", "Гоблин", "Орк", "Страж"]
            e_name = f"{random.choice(prefixes)} {random.choice(types)} [Этаж {floor}]"
        
        # 2. СПАВНИМ СУЩЕСТВО
        enemy = Enemy(name=e_name, hp=enemy_hp, max_hp=enemy_hp)
        enemy.base_test_damage = enemy_dmg
        enemy.base_test_shield = enemy_shld
        
        # Если это Босс, давай наделим его пассивной Слабостью/Уязвимостью на старте для интереса
        if is_boss:
            enemy.shield = enemy_shld * 2 # Босс начинает бой сразу в броне!
            
        from managers.CombatManager import CombatManager
        self.active_combat = CombatManager(self.player, enemy, self.current_deck, self)


    def distribute_combat_rewards(self):
        """Начисление золота и случайный дроп реликвий с шансом 20%"""
        # 1. Начисляем золото
        gold_drop = random.randint(15, 25) + (self.current_floor * 2)
        self.player_gold += gold_drop
        
        log_msg = f"Залутано +{gold_drop} монет!"
        
        # 2. РОЛЛ РЕЛИКВИИ: Шанс 20% (число от 1 до 5, если выпала 1 — дроп!)
        if random.randint(1, 2) == 1:
            from core.Relic import LuckyClover, SpikedBracelet, ЭнергоЯдро, ТочильныйКамень, ДревнееОгниво, НамокшаяРукавица
            
            # Собираем полный пул всех существующих реликвий
            all_pool = [LuckyClover, SpikedBracelet, ЭнергоЯдро, ТочильныйКамень, ДревнееОгниво, НамокшаяРукавица]
            
            # Фильтруем пул: убираем те реликвии, которые у игрока УЖЕ есть в сумке
            current_relic_names = [r.name for r in self.relics]
            available_relics = [r for r in all_pool if r().name not in current_relic_names]
            
            if available_relics:
                # Берем случайную новую реликвию, создаем её объект и кладем в сумку!
                dropped_relic_class = random.choice(available_relics)
                new_relic = dropped_relic_class()
                self.relics.append(new_relic)
                
                # Если выпало Энерго-Ядро, сразу пассивно качаем игроку максимальную энергию!
                if new_relic.name == "Энерго-Ядро":
                    self.player.max_energy += 1
                    
                log_msg += f" [НАГРАДА] Вы выбили артефакт: '{new_relic.name}'!"
                
        # Пишем итоговый праздничный лог в боевой экран перед уходом
        if self.active_combat:
            self.active_combat.add_log_message(log_msg)
