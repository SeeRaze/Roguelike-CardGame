from managers.DeckManager import DeckManager
from managers.network_manager import send_run_record


class CombatManager:
    """Менеджер боя, адаптированный под графический движок Pygame.
    Поддерживает как одного врага, так и группу (self.enemies — список)."""

    # Потолок ПЕРЕНОСА стаи между боями (Призыватель). Внутри боя призыв не
    # ограничен — лимит только на то, сколько выживших уносится в следующий бой.
    # Без него союзники (враги их не бьют) копились бы вечно → бесконечный
    # снежный ком. Это ручка тюнинга баланса Призывателя (см. Этап 5).
    # Замер чувствительности (эт.25 дошёл): cap4=10% · cap6=33% · cap8=56%.
    MAX_PERSISTENT_ALLIES = 6

    def __init__(self, player, enemies, starting_deck, game_manager=None):
        self.gm = game_manager
        self.player = player
        # Приводим к списку: если передали одного врага — заворачиваем
        if isinstance(enemies, list):
            self.enemies = enemies
        else:
            self.enemies = [enemies]
        self.allies: list = []          # призванные союзники
        self._restore_persistent_allies()
        self.deck_manager = DeckManager(starting_deck)
        self.turn_count = 1

        self.combat_log = []
        self._elemental_blocked  = False
        self._combo_triggered = False

        self.add_log_message("=== БОЙ НАЧАЛСЯ ===")

        # Хук on_combat_start -- реликвии
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_combat_start(self)

        # Хук on_combat_start -- активная способность
        ability = getattr(self.player, 'active_ability', None)
        if ability:
            ability.on_combat_start(self)

        self.start_turn_phase()

    # --- Обратная совместимость: старый код читает self.enemy ---
    @property
    def enemy(self):
        """Первый враг в списке (для совместимости со старым кодом)."""
        return self.enemies[0] if self.enemies else None

    @enemy.setter
    def enemy(self, value):
        if self.enemies:
            self.enemies[0] = value
        else:
            self.enemies.append(value)

    def get_target_enemy(self):
        """Первый живой враг — цель для авто-таргетинга."""
        for e in self.enemies:
            if e.hp > 0:
                return e
        return None

    def add_log_message(self, message):
        self.combat_log.append(message)
        if len(self.combat_log) > 6:
            self.combat_log.pop(0)

    def start_turn_phase(self):
        # Все живые враги выбирают намерение
        for e in self.enemies:
            if e.hp > 0:
                e.choose_intent()

        # Пассивка считает carry ДО сброса щита
        self.player.on_turn_start_passive(self)

        # Сбрасываем щит, восстанавливаем carry
        self.player._iron_will_shield = self.player.shield
        carry = getattr(self.player, '_passive_shield_carry', 0)
        self.player._passive_shield_carry = 0
        self.player.shield = carry


        self.player.energy = self.player.max_energy

        bonus = getattr(self.player, "bonus_draw", 0)
        self.deck_manager.draw_cards(5 + bonus)

        if type(self.player).__name__ == "Rogue" and self.deck_manager.hand:
            import random
            card = random.choice(self.deck_manager.hand)
            original = card.cost
            card.temp_cost = max(0, original - 1)
            self.add_log_message(
                f" [РАЗБОЙНИК] {card.name}: стоимость {original} -> {card.temp_cost}"
            )

        self.add_log_message(f"--- НАЧАЛО ХОДА {self.turn_count} ---")

        # Хук on_turn_start -- реликвии
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_turn_start(self)

        # Хук on_turn_start -- активная способность (штрафы, кулдауны)
        ability = getattr(self.player, 'active_ability', None)
        if ability:
            ability.on_turn_start(self)

    def play_card_by_index(self, card_index, target=None):
        """Разыграть карту по индексу в руке.
        Если target передан — используется указанный враг, иначе авто-таргетинг."""
        if card_index < 0 or card_index >= len(self.deck_manager.hand):
            return False

        selected_card = self.deck_manager.hand[card_index]
        effective_cost = getattr(selected_card, 'temp_cost', selected_card.cost)

        if self.player.energy < effective_cost:
            self.add_log_message("[!] Не хватает энергии!")
            return False

        self.player.use_energy(effective_cost)
        self.add_log_message(f"Вы разыграли: {selected_card.name}")

        self._combo_triggered = False
        if target is None:
            target = self.get_target_enemy()
        if target is None or target.hp <= 0:
            self.add_log_message("[!] Нет целей для атаки!")
            return False
        selected_card.apply(self.player, target, self)

        self.player.on_card_played_passive(selected_card, self)

        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_card_played(selected_card, self)

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
        self.add_log_message("Вы завершили ход.")
        self.deck_manager.discard_hand()

        # Враги действуют: сброс щита → исполнение намерения → тик статусов
        for e in self.enemies:
            if e.hp <= 0:
                continue
            e.shield = 0
            e.execute_intent(self.player, self)
            e.tick_statuses(self)
            self._check_enemy_death(e)
            # Если игрок умер от действий врага — прерываем
            if self.player.hp <= 0:
                break

        self.player.tick_statuses(self)

        # Союзники действуют: выбор цели → атака → тик статусов
        for ally in self.allies:
            if ally.hp <= 0:
                continue
            target = ally.choose_action(self)
            if target:
                ally.execute_action(target, self)
                self._check_enemy_death(target)
            ally.tick_statuses(self)
            self._check_ally_death(ally)

        # Проверка: все враги мертвы?
        if all(e.hp <= 0 for e in self.enemies):
            self.add_log_message("=== ВСЕ ВРАГИ ПОВЕРЖЕНЫ! ===")
            return

        if self.player.hp > 0:
            self.turn_count += 1
            self.start_turn_phase()

        self.check_player_defeat()

    def _check_enemy_death(self, enemy):
        """Вызывается после каждого источника урона врагу.
        Если враг умер — вызывает on_kill на всех реликвиях и обновляет статистику."""
        if enemy.hp > 0:
            return
        # Уже обработан — не дёргаем повторно
        if getattr(enemy, '_death_processed', False):
            return
        enemy._death_processed = True

        self.add_log_message(f"=== {enemy.name} ПОВЕРЖЕН! ===")

        # Хук on_kill -- реликвии
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_kill(enemy, self)

        # Статистика
        if self.gm and hasattr(self.gm, 'stats'):
            if getattr(enemy, 'is_boss', False):
                self.gm.stats["bosses_killed"] = \
                    self.gm.stats.get("bosses_killed", 0) + 1
            else:
                self.gm.stats["monsters_killed"] = \
                    self.gm.stats.get("monsters_killed", 0) + 1

        # Бой выигран (все враги повержены) — сохранить стаю до следующего боя.
        # Единая точка для всех путей победы (карта/союзник/статус добил врага).
        if all(e.hp <= 0 for e in self.enemies):
            self._persist_allies()

    def _check_ally_death(self, ally):
        """Удалить мёртвого союзника из списка."""
        if ally.hp > 0:
            return
        self.add_log_message(f"[СОЮЗНИК] {ally.name} пал в бою!")
        if ally in self.allies:
            self.allies.remove(ally)

    def _restore_persistent_allies(self):
        """Восстановить выживших союзников из прошлого боя (Призыватель).
        Транзиентное боевое состояние (щит/статусы) обнуляем — переносим
        только саму единицу с её текущим HP."""
        carried = getattr(self.player, 'persistent_allies', None)
        if not carried:
            return
        for ally in carried:
            if ally.hp <= 0:
                continue
            ally.shield = 0
            for key in ally.statuses:
                ally.statuses[key] = 0
            self.allies.append(ally)

    def _persist_allies(self):
        """Сохранить выживших союзников до следующего боя (вызывается при
        победе). Переносим не больше MAX_PERSISTENT_ALLIES — сильнейших
        (по HP, затем по атаке), чтобы стая не копилась безгранично."""
        survivors = [a for a in self.allies if a.hp > 0]
        survivors.sort(key=lambda a: (a.hp, a.attack_power), reverse=True)
        self.player.persistent_allies = survivors[:self.MAX_PERSISTENT_ALLIES]

    def check_player_defeat(self) -> bool:
        """Проверка смерти игрока и запуск конца игры.
        Вызывается в конце хода И после активной способности
        (Берсерк бьёт себя сквозь щит и может умереть в свой ход)."""
        if self.player.hp > 0:
            return False

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
        return True