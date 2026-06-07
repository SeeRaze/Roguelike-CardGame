from managers.DeckManager import DeckManager
from managers.network_manager import send_run_record
from managers import SaveManager
from core.forge import TriggerGuard


class CombatManager:
    """Менеджер боя, адаптированный под графический движок Pygame.
    Поддерживает как одного врага, так и группу (self.enemies — список)."""

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

    def play_card_by_index(self, card_index, target=None):
        """Разыграть карту по индексу в руке.
        Если target передан — используется указанный враг, иначе авто-таргетинг."""
        if card_index < 0 or card_index >= len(self.deck_manager.hand):
            return False

        selected_card = self.deck_manager.hand[card_index]
        effective_cost = getattr(selected_card, 'temp_cost', selected_card.cost)

        overdraft = getattr(self.player, 'energy_overdraft', False)
        if self.player.energy < effective_cost:
            if not overdraft:
                self.add_log_message("[!] Не хватает энергии!")
                return False
            # Долговой движок (§7): уходим в минус, но НЕ глубже жёсткого пола
            # (амплитудный гард-рейл DEBT_MAX_OVERDRAFT).
            from core.debt import DEBT_MAX_OVERDRAFT
            if effective_cost - self.player.energy > DEBT_MAX_OVERDRAFT:
                self.add_log_message("[!] Долг энергии слишком глубок!")
                return False

        self.player.use_energy(effective_cost, allow_debt=overdraft)
        self.add_log_message(f"Вы разыграли: {selected_card.name}")

        self._combo_triggered = False
        if target is None:
            target = self.get_target_enemy()
        if target is None or target.hp <= 0:
            self.add_log_message("[!] Нет целей для атаки!")
            return False
        # Транзиентная ссылка на разыгрываемую карту: FlowEffect (стихия Воздух)
        # читает её, чтобы НЕ удешевлять саму себя (она ещё в руке во время apply).
        self._card_being_played = selected_card
        # СНИМОК состояния на момент намерения (§10.6): предикаты тегов прокачки
        # читают ЕГО, а не живое поле — заморожен до того, как apply/эхо/детонации
        # изменят руку/статусы/цель. Считается ОДИН раз за розыгрыш.
        self._play_snapshot = self._build_play_snapshot(target)
        # Сброс предохранителя на новый розыгрыш: детонации/Эхо этой карты считаются
        # с нуля (§10.2). Первичный apply — не триггер, бюджет не тратит.
        self._trigger_guard.depth = 0
        selected_card.apply(self.player, target, self)

        # Эхо (ретриггер): каждый заряд эха на игроке заставляет карту
        # сработать повторно. Заряды снимаются ДО повторов — карта, генерирующая
        # эхо сама, НЕ зациклится (новые заряды лягут уже после всех повторов).
        echo_stacks = self.player.echo
        if echo_stacks > 0:
            self.player.echo = 0
            for i in range(echo_stacks):
                # Каждый ретриггер — событие триггера: предохранитель обрывает
                # цепочку на MAX_TRIGGER_DEPTH (суммарно с детонациями розыгрыша).
                if not self._trigger_guard.enter():
                    self.add_log_message(
                        "[ПРЕДОХРАНИТЕЛЬ] Каскад триггеров оборван (глубина)."
                    )
                    break
                selected_card.apply(self.player, target, self)
                self.add_log_message(
                    f"[ЭХО] {selected_card.name} срабатывает повторно "
                    f"({i + 1}/{echo_stacks})!"
                )

        self._card_being_played = None
        self._play_snapshot = None
        # Карта сыграна — счётчик для предикатов first/nth card (читается ИЗ снимка,
        # инкремент ПОСЛЕ розыгрыша, чтобы первая карта за ход видела play_index=0).
        self.cards_played_this_turn += 1

        self.player.on_card_played_passive(selected_card, self)

        # Post-хуки розыгрыша под предохранителем (R2): реликвии и враги реагируют
        # на сыгранную карту. Сейчас они только меняют состояние (щит/золото/
        # эскалация), но будущий хук, играющий эффект, мог бы рекурсить — гард
        # обрывает каскад. Это ОТДЕЛЬНОЕ событие после полного разрешения розыгрыша
        # (apply+эхо+детонации завершены) → свой бюджет глубины, сброс с нуля, чтобы
        # хуки не наказывались за глубину эхо карты, но были защищены от своей рекурсии.
        self._trigger_guard.depth = 0
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                self._guarded(
                    f"реликвия {getattr(relic, 'name', '?')}",
                    lambda relic=relic: relic.on_card_played(selected_card, self),
                )

        # Хук боссов/врагов: реакция на розыгрыш карты (Архивариус: +щит за карту).
        for e in self.enemies:
            if e.hp > 0 and hasattr(e, 'on_card_played'):
                self._guarded(
                    f"враг {getattr(e, 'name', '?')}",
                    lambda e=e: e.on_card_played(selected_card, self.player, self),
                )

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

        # Смерть врага обрабатывается в МОМЕНТ убивающего действия (как в фазе врага):
        # on_kill реликвий, счётчик убийств, перенос стаи. ДО _check_victory, иначе
        # победа картой ушла бы в награды мимо обработки смерти (потеря снежного кома).
        self._process_enemy_deaths()

        # Победа МОГЛА наступить прямо в этом розыгрыше (карта/эхо/детонации добили
        # последнего врага) → обрываем ход немедленно, без «лишней» фазы.
        self._check_victory()
        return True

    def _build_play_snapshot(self, target, card=None) -> dict:
        """Снимок контекста на момент намерения разыграть карту (§10.6). Предикаты
        тегов прокачки (core/ForgeRegistry.py) читают ТОЛЬКО его — заморожен до
        apply/эха/детонаций. Цель тоже заморожена → null-safe (§10.7): даже если
        враг погибнет в каскаде, снимок хранит прежний стак яда/крови. Ключи
        совпадают с тем, что читают предикаты ForgeRegistry. `card` — разыгрываемая
        (или наведённая, для превью) карта; по умолчанию — текущая транзиентная."""
        p = self.player
        card = card if card is not None else self._card_being_played
        max_hp = getattr(p, "max_hp", 0) or 1
        # Рука ПОСЛЕ изъятия текущей карты (для empty_hand): карта ещё в hand на
        # момент снимка, поэтому −1.
        hand_after = max(0, len(self.deck_manager.hand) - 1)
        # Сколько АТАКУЮЩИХ карт осталось бы в руке (для оборонного тега bulwark:
        # «рука только из защиты»). Считаем по наличию DamageEffect, исключая
        # саму разыгрываемую/наведённую карту.
        from core.cards.base import DamageEffect
        hand_attack = sum(
            1 for c in self.deck_manager.hand
            if c is not card
            and any(isinstance(e, DamageEffect) for e in getattr(c, "effects", []))
        )
        return {
            "play_index": self.cards_played_this_turn,   # 0 = первая карта за ход
            "hand_after": hand_after,
            "hand_attack": hand_attack,
            "hp_frac":    p.hp / max_hp,
            "shield":     getattr(p, "shield", 0),
            "barrier":    getattr(p, "barrier", 0),
            "mastery":    getattr(p, "mastery", 0),
            "minions":    sum(1 for a in self.allies if a.hp > 0),
            "tgt_poison": getattr(target, "poison", 0),
            "tgt_bleed":  getattr(target, "bleed", 0),
        }

    def build_preview_snapshot(self, card, target) -> dict:
        """Снимок для ПРЕВЬЮ урона на карте (UI): тот же контент, что у розыгрыша,
        но для произвольной наведённой карты и БЕЗ установки живых транзиентов
        (_card_being_played/_play_snapshot). Используется EffectCalculator.preview."""
        return self._build_play_snapshot(target, card=card)

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

    def _check_victory(self) -> bool:
        """Немедленный переход в награды, как только ВСЕ враги мертвы.

        Зовётся сразу после любого источника урона игрока (розыгрыш карты, эхо,
        детонации, активная способность) и в конце фазы врага. Раньше победа
        ловилась только по клику в InputHandler → после убийства последнего врага
        у игрока оставалась «лишняя» фаза хода (можно было играть карты/способности).
        Теперь бой обрывается сразу.

        Безопасно для симулятора: bot-`gm` (_StubGM) не имеет distribute_combat_rewards
        и не держит current_state == "COMBAT" → ветка не срабатывает, baseline цел.
        Идемпотентно: distribute_combat_rewards сам выходит, если state != COMBAT."""
        if not self.enemies or any(e.hp > 0 for e in self.enemies):
            return False
        gm = self.gm
        if (gm is not None
                and getattr(gm, "current_state", None) == "COMBAT"
                and hasattr(gm, "distribute_combat_rewards")):
            gm.distribute_combat_rewards()
            return True
        return False

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

    def _process_enemy_deaths(self):
        """Обработать смерть ВСЕХ врагов после действия игрока (розыгрыш карты /
        активная способность). Симметрично фазе врага, где _check_enemy_death
        предшествует проверке победы. AoE-детонации (electro_blast и т.п.) могут
        добить нескольких сразу → свип по всему self.enemies.

        Под _guarded_action: своё событие, сброс глубины гарда, конечность каскада
        (инвариант R2/R3). on_kill срабатывает ПОСЛЕ всех per-play реакций (после
        RELIC_HOOK/ENEMY_HOOK), т.е. в момент убивающего действия, а не в конце хода.
        Идемпотентно: _check_enemy_death помечает enemy._death_processed → повторный
        свип в end_turn_phase no-op."""
        self._guarded_action(
            "обработка смертей врагов",
            lambda: [self._check_enemy_death(e) for e in self.enemies],
        )

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