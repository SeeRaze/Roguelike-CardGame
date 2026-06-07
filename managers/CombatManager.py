from managers.DeckManager import DeckManager
from managers.network_manager import send_run_record
from managers import SaveManager
from core.forge import TriggerGuard
from managers.combat import CardPlayMixin, PositioningMixin, ResolutionMixin


class CombatManager(PositioningMixin, CardPlayMixin, ResolutionMixin):
    """Менеджер боя, адаптированный под графический движок Pygame.
    Поддерживает как одного врага, так и группу (self.enemies — список).

    Оркестратор: инфра (жизненный цикл боя, лог, предохранитель глубины) живёт здесь;
    поведение — в когезивных миксинах `managers/combat/` (С49, разбор god-object)."""

    # Потолок ПЕРЕНОСА стаи между боями (Призыватель). Внутри боя призыв не
    # ограничен — лимит только на то, сколько выживших уносится в следующий бой.
    # Без него стая копилась бы вечно → бесконечный снежный ком.
    # ГЛАВНАЯ ручка баланса Призывателя: теперь враги бьют СЛУЧАЙНУЮ цель
    # (игрок/союзник, см. Enemy._choose_attack_target), поэтому стая ещё и
    # ТАНКует — потолок прямо задаёт живучесть. Свип с новым таргетингом
    # (медиана этажа смерти / wr50): cap6=43/6% · cap8=46/22% · cap10=54/68%.
    # cap6 ставит медиану вровень с Берсерком (42), не делая класс топ-1.
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
        # Счётчик сыгранных карт за текущий ход (предикаты тегов: first/nth card).
        self.cards_played_this_turn = 0

        self.combat_log = []
        self._elemental_blocked  = False
        self._combo_triggered = False
        # Транзиенты розыгрыша (Сессия 39): разыгрываемая карта + СНИМОК состояния
        # на момент намерения (§10.6) — предикаты тегов читают снимок, не живое поле.
        self._card_being_played = None
        self._play_snapshot = None
        # Предохранитель глубины триггеров (§10.2): считает ВСЕ ретриггеры (Эхо) +
        # детонации суммарно за один розыгрыш карты, обрывает на MAX_TRIGGER_DEPTH —
        # анти-∞-цикл и анти-переполнение чисел в реал-тайме. Сброс на каждом розыгрыше.
        self._trigger_guard = TriggerGuard()

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

        # Позиционка (§5): инициализация строя на старте боя — ПОСЛЕ on_combat_start
        # и start_turn_phase, чтобы саммоны старта боя тоже встали в строй. Сбрасывает
        # рантайм-строй к классовому дефолту (флип Манёвра не переносится между боями)
        # + первичная расстановка. NO-OP без флага positioning_enabled (baseline зелёный).
        self._init_positioning()

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

    def add_log_message(self, message):
        self.combat_log.append(message)
        if len(self.combat_log) > 6:
            self.combat_log.pop(0)

    def start_turn_phase(self):
        # Новый ход — обнуляем счётчик сыгранных карт (предикаты first/nth card).
        self.cards_played_this_turn = 0

        # Все живые враги выбирают намерение.
        # Хук on_turn_start: боссы обновляют состояние перед choose_intent
        # (эскалация/Щит Пустоты/временной заряд). hasattr — duck-typing, как у реликвий.
        for e in self.enemies:
            if e.hp > 0:
                if hasattr(e, 'on_turn_start'):
                    e.on_turn_start(self.player, self)
                e.choose_intent()

        # Пассивка считает carry ДО сброса щита
        self.player.on_turn_start_passive(self)

        # Сбрасываем щит, восстанавливаем carry + БАРЬЕР (несгораемый щит).
        self.player._iron_will_shield = self.player.shield
        carry = getattr(self.player, '_passive_shield_carry', 0)
        self.player._passive_shield_carry = 0
        self.player.shield = carry + self.player.barrier


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

    def _guarded_action(self, label, fn):
        """Верхнеуровневое реакционное действие фазы врага (тик статусов, намерение
        врага, действие союзника). Сбрасывает глубину гарда В НОЛЬ перед вызовом —
        каждое такое действие самостоятельно (своё событие), и одно не должно «съесть»
        бюджет следующего. Внутри действия рекурсия (тик → хук → тик) по-прежнему
        ограничена потолком через вложенные _guarded. Возвращает результат fn()."""
        self._trigger_guard.depth = 0
        return self._guarded(label, fn)

    def _settle_energy_debt(self):
        """Гашение долга энергии (§7, «pay later»): HP-штраф = долг × DEBT_HP_INTEREST.
        Зовётся в end_turn_phase ДО сброса энергии (start_turn_phase обнулил бы долг).
        lose_hp бьёт сквозь щит (как минус-HP Берсерка)."""
        from core.debt import DEBT_HP_INTEREST
        debt = -self.player.energy
        interest = debt * DEBT_HP_INTEREST
        self.add_log_message(
            f"[ДОЛГ] Гашение энергии: -{interest} HP за {debt} ед. долга.")
        self.player.lose_hp(interest)
        self.player.energy = 0

    def end_turn_phase(self):
        self.add_log_message("Вы завершили ход.")
        self.deck_manager.discard_hand()

        # Гашение долга энергии (§7): непогашенный овердрафт оплачивается HP ДО сброса
        # энергии в start_turn_phase. Под _guarded_action (своё событие, сброс гарда).
        if getattr(self.player, 'energy', 0) < 0:
            self._guarded_action("гашение долга энергии", self._settle_energy_debt)

        # Хук on_turn_end реликвий — «конец хода игрока», ДО действий врагов
        # (Гнилое Сердце банкует щит в Барьер до того, как враг ударит). Под
        # _guarded_action: своё событие, сброс глубины гарда (инвариант R3).
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                self._guarded_action(
                    f"конец хода {getattr(relic, 'name', '?')}",
                    lambda relic=relic: relic.on_turn_end(self),
                )

        # Позиционка (§5): пере-расстановка ПРЯМО перед фазой врага → саммоны,
        # призванные в этот ход (карта/способность) или на старте боя, получают ранг
        # ДО выбора цели врагом. NO-OP без флага (baseline зелёный). Идемпотентно.
        self._apply_positioning()

        # Враги действуют: сброс щита → исполнение намерения → тик статусов.
        # Каждый источник — под предохранителем глубины (R3): тик/намерение, что
        # каскадно дёргает реакции (горение→хук реликвии→…), оборвётся на потолке,
        # а не зациклится. Порядок: namerenie ПЕРЕД тиком (атака до догорания).
        for e in self.enemies:
            if e.hp <= 0:
                continue
            e.shield = 0
            self._guarded_action(
                f"намерение {getattr(e, 'name', '?')}",
                lambda e=e: e.execute_intent(self.player, self),
            )
            self._guarded_action(
                f"тик {getattr(e, 'name', '?')}",
                lambda e=e: e.tick_statuses(self),
            )
            self._check_enemy_death(e)
            # Если игрок умер от действий врага — прерываем
            if self.player.hp <= 0:
                break

        self._guarded_action("тик игрока", lambda: self.player.tick_statuses(self))

        # Союзники действуют: выбор цели → атака → тик статусов (всё под гардом).
        for ally in self.allies:
            if ally.hp <= 0:
                continue
            target = ally.choose_action(self)
            if target:
                self._guarded_action(
                    f"союзник {getattr(ally, 'name', '?')}",
                    lambda ally=ally, target=target: ally.execute_action(target, self),
                )
                self._check_enemy_death(target)
            self._guarded_action(
                f"тик союзника {getattr(ally, 'name', '?')}",
                lambda ally=ally: ally.tick_statuses(self),
            )
            self._check_ally_death(ally)

        # Проверка: все враги мертвы? (добиты союзником/статусом в фазу врага)
        if all(e.hp <= 0 for e in self.enemies):
            self.add_log_message("=== ВСЕ ВРАГИ ПОВЕРЖЕНЫ! ===")
            self._check_victory()
            return

        if self.player.hp > 0:
            self.turn_count += 1
            self.start_turn_phase()

        self.check_player_defeat()

    def _guarded(self, label, fn):
        """Выполнить реакционный вызов `fn()` под предохранителем глубины (§10.2).

        Возвращает результат fn(), либо None если потолок глубины достигнут (каскад
        оборван). Единая точка для ВСЕХ реакционных путей вне первичного apply:
        post-хуки розыгрыша (реликвии/враги), тики статусов, действия союзников —
        чтобы взаимно-рекурсивная цепочка (будущий хук, играющий эффект, который
        снова дёргает хук) гарантированно завершилась, а не зациклилась/переполнила
        числа. Порядок задаёт ReactionOrder, конечность — этот гард (ортогонально).

        `label` — человекочитаемая метка для лога обрыва."""
        guard = self._trigger_guard
        if not guard.enter():
            self.add_log_message(
                f"[ПРЕДОХРАНИТЕЛЬ] Каскад триггеров оборван ({label}, глубина)."
            )
            return None
        try:
            return fn()
        finally:
            guard.exit()

    def check_player_defeat(self) -> bool:
        """Проверка смерти игрока и запуск конца игры.
        Вызывается в конце хода И после активной способности
        (Берсерк бьёт себя сквозь щит и может умереть в свой ход)."""
        if self.player.hp > 0:
            return False

        self.player.hp = 0
        print("[СИСТЕМА] Здоровье игрока упало до 0!")

        current_floor = self.gm.current_floor if self.gm else 1
        monsters = self.gm.stats["monsters_killed"] if self.gm else 0
        bosses   = self.gm.stats["bosses_killed"]   if self.gm else 0
        kills_count = monsters + bosses
        max_dmg = self.gm.stats["max_damage_dealt"] if self.gm else 0
        player_class = type(self.player).__name__

        # Локальная мета-прогрессия (local-first): пишем итог забега на диск ДО сети,
        # чтобы лидерборд и «игра помнит тебя» работали даже офлайн (сеть — обогащение).
        from managers.network_manager import _get_username
        SaveManager.record_run({
            "username":   _get_username(),
            "class":      player_class,
            "max_floor":  current_floor,
            "kills":      kills_count,
            "bosses":     bosses,
            "max_damage": max_dmg,
        })

        print("[СЕТЬ] Отправляем рекорд напрямую в Google...")
        send_run_record(
            max_floor=current_floor, kills=kills_count,
            max_damage=max_dmg, player_class=player_class,
        )

        if self.gm:
            from ui.LeaderboardView import LeaderboardView
            LeaderboardView.load_data()
            self.gm.current_state = "LEADERBOARD"
        return True