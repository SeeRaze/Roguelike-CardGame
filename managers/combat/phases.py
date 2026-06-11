"""Фазы хода боя: начало хода, конец хода, гашение долга энергии (С49).

start_turn_phase — намерения врагов, пассив/щит/энергия/добор, хуки старта.
end_turn_phase — сброс руки, гашение долга, on_turn_end реликвий, действия врагов
и союзников (всё под предохранителем глубины), проверка победы/поражения.
"""
from core.DetonationRegistry import detonate, SHORTCIRCUIT_THRESHOLD

RECURSION_THRESHOLD = 10   # стек Legacy через добор > порога → крит + перенос на соседа
CRASH_REBOOT_TURNS  = 2    # CRASH REBOOT блокирует восстановление врага на N ходов


class TurnPhaseMixin:
    """Начало/конец хода + гашение долга энергии. Опирается на инфру оркестратора
    (deck_manager/player/enemies/allies/_guarded_action/_check_enemy_death/
    _check_ally_death/_check_victory/_apply_positioning/start_turn_phase/
    check_player_defeat)."""

    def apply_leak_on_draw(self):
        """Утечка памяти (С58): на АКТ ДОБОРА каждый враг с `leak` получает
        leak × размер руки урона (ось «рука = Контекстное Окно», семя Демиурга).
        Раз на батч (не на карту). Урон УВАЖАЕТ щит (take_damage).

        Со-присутственные реакции движка (на этом же тике):
          ГИДРОДИНАМИКА (Кофе+Утечка) — тик добирает ещё карту (компаунд карт-преим-ва;
            петли нет — добор не рефайрит leak).
          РЕКУРСИЯ (Legacy+Утечка) — добор стакает Legacy; на >порога → крит + перенос
            половины на соседа (позиционка; без соседей перенос инертен)."""
        hand_size = len(self.deck_manager.hand)
        if hand_size == 0:
            return
        for e in list(self.enemies):
            if e.hp <= 0:
                continue
            stacks = e.get_status("leak")
            if stacks <= 0:
                continue
            dmg = stacks * hand_size
            self.add_log_message(
                f" [УТЕЧКА] {e.name}: {stacks} × рука {hand_size} = {dmg} урона."
            )
            e.take_damage(dmg, combat_manager=self)

            # ГИДРОДИНАМИКА (Кофе+Утечка): тик добирает ещё карту.
            if e.get_status("coffee") > 0:
                drew = self.deck_manager.draw_cards(1)
                if drew:
                    self.add_log_message(
                        " [ГИДРОДИНАМИКА] +1 карта (компаунд Утечки)."
                    )

            # РЕКУРСИЯ (Legacy+Утечка): добор стакает Legacy; >порога → крит.
            if e.get_status("legacy") > 0:
                e.set_status("legacy", e.get_status("legacy") + 1)
                if e.get_status("legacy") > RECURSION_THRESHOLD:
                    self._recursion_crit(e)
        # Реакции могли добить врага — проверяем смерти.
        for e in list(self.enemies):
            if e.hp <= 0:
                self._check_enemy_death(e)

    def _recursion_crit(self, e):
        """РЕКУРСИЯ переполнилась: стек Legacy > порога → крит-бурст (×2) + перенос
        половины стека на соседей по позиционке. Без соседей перенос инертен. Legacy
        сожжён в крите."""
        leg = e.get_status("legacy")
        burst = leg * 2
        self.add_log_message(
            f" [РЕКУРСИЯ] Стек Legacy {leg} > {RECURSION_THRESHOLD} → крит {burst}!"
        )
        e.take_damage(burst, combat_manager=self)
        neighbors = self._leak_neighbors(e)
        if neighbors:
            half = leg // 2
            for n in neighbors:
                n.set_status("legacy", n.get_status("legacy") + half)
                self.add_log_message(
                    f" [РЕКУРСИЯ] {half} Legacy перетекло на {getattr(n, 'name', '?')}."
                )
        e.set_status("legacy", 0)

    def _leak_neighbors(self, e):
        """Соседи цели по позиционке для переноса Рекурсии. Инертно ([]), если
        позиционка off (нет линий/рангов) — перенос тогда не происходит."""
        neighbors_fn = getattr(self, "neighbors", None)
        if callable(neighbors_fn):
            try:
                return [n for n in neighbors_fn(e) if n.hp > 0]
            except Exception:
                return []
        return []

    def apply_copresence_reactions(self):
        """CRASH REBOOT (Утечка+Токс, С58): «перезагрузка» — снос щита и баффов врага +
        блокировка восстановления/регена на CRASH_REBOOT_TURNS ходов. Анти-сустейн через
        ШАТДАУН состояния (не невидимое число). Со-присутственный свип, раз/ход."""
        BUFF_KEYS = ("strength", "regen", "thorns", "barrier", "vampire",
                     "mastery", "discipline", "instability", "echo")
        for e in list(self.enemies):
            if e.hp <= 0:
                continue
            if e.get_status("leak") > 0 and e.get_status("tox") > 0:
                e.shield = 0
                for k in BUFF_KEYS:
                    e.set_status(k, 0)
                e.set_status("heal_block", CRASH_REBOOT_TURNS)
                self.add_log_message(
                    f" [CRASH REBOOT] {getattr(e, 'name', '?')}: щит/баффы снесены, "
                    f"восстановление заблокировано."
                )

    def start_turn_phase(self):
        # Новый ход — обнуляем счётчик сыгранных карт (предикаты first/nth card).
        self.cards_played_this_turn = 0
        # БЕЗУМИЕ (Берсерк) длится один ход — сбрасываем (надо переактивировать). NO-OP
        # для классов без безумия (атрибут просто становится False).
        self.player.madness_active = False
        # ENGINE: неиспользованный флаг «Диспетчер задач» гаснет в начале хода.
        self._dispatcher_pending = False

        # CRASH REBOOT (Утечка+Токс): шатдаун врага ДО выбора намерения (снос баффов/щита,
        # блок восстановления). Инертно, если ни у кого нет пары leak+tox.
        self.apply_copresence_reactions()

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

        # РЕАГЕНТ (Химик, §2): фикс-приток в начало хода (ресурс-тормоз слияния карт).
        # Гейт fusion_enabled → NO-OP для всех классов кроме Химика (baseline зелёный).
        if getattr(self.player, "fusion_enabled", False):
            self.player.reagent += getattr(self.player, "reagent_per_turn", 0)

        bonus = getattr(self.player, "bonus_draw", 0)
        self.deck_manager.draw_cards(5 + bonus)
        # Утечка памяти (С58): на акт добора враги с leak теряют leak × размер руки.
        self.apply_leak_on_draw()

        self.add_log_message(f"--- НАЧАЛО ХОДА {self.turn_count} ---")

        # Хук on_turn_start -- реликвии
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                relic.on_turn_start(self)

        # Хук on_turn_start -- активная способность (штрафы, кулдауны)
        ability = getattr(self.player, 'active_ability', None)
        if ability:
            ability.on_turn_start(self)

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

    def _settle_hp_debt(self):
        """Хук расплаты по ДОЛГУ HP (§4, С49, субстрат Берсерка). По умолчанию NO-OP:
        игрок остаётся в минусе (близость к полу-смерти = структурная расплата, множитель
        даёт EffectCalculator). СЕАМ под класс Берсерка: если у игрока есть
        on_hp_debt_settle(cm) — зовём его в минусе (грация-ход + конверсия |HP|→FP при
        победе подключатся ТАМ, не в ядре). Инертно без хука/без минуса → baseline зелёный."""
        if self.player.hp < 0:
            hook = getattr(self.player, 'on_hp_debt_settle', None)
            if hook:
                hook(self)

    def _tick_delayed_effects(self):
        """Очередь отложенных эффектов (§3): уменьшить ВСЕ таймеры на 1, исполнить
        созревшие. Каждый созревший — под _guarded_action (своё событие, сброс глубины
        гарда → конечность каскада, инвариант R3); эффект, планирующий НОВОЕ отложенное
        при исполнении, не теряется (tick переустановил очередь до возврата). После
        исполнения — свип смертей врагов через _process_enemy_deaths (тайм-бомба могла
        добить врага; идемпотентно с фазой врага). NO-OP при пустой очереди — потребителя
        пока нет (как субстрат позиционки до §1), baseline зелёный.

        ТАЙМИНГ (дизайн-дефолт, пересмотреть при появлении потребителя): срабатывание в
        конце хода игрока. Развилка зафиксирована в _project_map (§ отложенные эффекты)."""
        due = self.delayed_queue.tick()
        if not due:
            return
        for effect in due:
            self._guarded_action(
                f"отложенный эффект: {effect.label or '?'}",
                lambda effect=effect: effect.action(self),
            )
        self._process_enemy_deaths()

    def end_turn_phase(self):
        self.add_log_message("Вы завершили ход.")
        self.deck_manager.discard_hand()

        # Гашение долга энергии (§7): непогашенный овердрафт оплачивается HP ДО сброса
        # энергии в start_turn_phase. Под _guarded_action (своё событие, сброс гарда).
        if getattr(self.player, 'energy', 0) < 0:
            self._guarded_action("гашение долга энергии", self._settle_energy_debt)

        # Расплата по долгу HP (§4): хук-сеам под Берсерка. NO-OP без хука/без минуса.
        self._guarded_action("расплата долга HP", self._settle_hp_debt)

        # Строгая расплата (Берсерк «Отрицание Смерти»): если долг HP убил игрока в конце
        # ЕГО хода (остался в минусе и не победил) — прерываем фазу ДО действий врагов
        # (мёртвый не получает удары/тики). NO-OP для обычных классов: _settle_hp_debt не
        # форсировал смерть → check_player_defeat вернёт False (hp>пола) → bail не сработает.
        if self.check_player_defeat():
            return

        # Хук on_turn_end реликвий — «конец хода игрока», ДО действий врагов
        # (Точка отказа банкует щит в Барьер до того, как враг ударит). Под
        # _guarded_action: своё событие, сброс глубины гарда (инвариант R3).
        if self.gm and hasattr(self.gm, 'relics'):
            for relic in self.gm.relics:
                self._guarded_action(
                    f"конец хода {getattr(relic, 'name', '?')}",
                    lambda relic=relic: relic.on_turn_end(self),
                )

        # Очередь отложенных эффектов (§3): созревшие «через N ходов» срабатывают в
        # КОНЦЕ ХОДА ИГРОКА (после on_turn_end реликвий, ПЕРЕД фазой врага). NO-OP без
        # потребителя — очередь пуста, baseline зелёный.
        self._tick_delayed_effects()

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
            # НЕЙРОТОКСИН (С58): оглушённый враг пропускает намерение, но статусы тикают
            # (стан спадает в его тик ниже). Видимый фидбэк — часть механики CC.
            if e.get_status("stunned") > 0:
                self.add_log_message(
                    f" [CRASH] {getattr(e, 'name', '?')} оглушён — пропускает ход."
                )
            else:
                self._guarded_action(
                    f"намерение {getattr(e, 'name', '?')}",
                    lambda e=e: e.execute_intent(self.player, self),
                )
            self._guarded_action(
                f"тик {getattr(e, 'name', '?')}",
                lambda e=e: e.tick_statuses(self),
            )
            # Авто-детонация Замыкания при достижении порога (после тика — заряды
            # за ход уже накоплены). Под гардом (анти-каскад).
            if e.get_status("shortcircuit") >= SHORTCIRCUIT_THRESHOLD:
                self._guarded_action(
                    f"авто-детонация {getattr(e, 'name', '?')}",
                    lambda e=e: detonate(e, self),
                )
            self._check_enemy_death(e)
            # Если игрок ПОГИБ от действий врага — прерываем. Порог = пол HP (овердрафт-
            # класс в минусе ещё жив; обычный класс — пол 0, байт-в-байт).
            if self.player.hp <= self.player._hp_floor():
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

        # Игрок ЖИВ (выше пола HP — для Берсерка это может быть МИНУС) → новый ход.
        # Раньше было `hp > 0`: овердрафт-класс в минусе (живой!) не получал добор/сброс
        # энергии и завис бы. Теперь порог = пол (_hp_floor), для обычных классов = 0
        # (байт-в-байт). Если игрок мёртв (hp<=пол) — turn НЕ растёт, ниже фиксируем смерть.
        if self.player.hp > self.player._hp_floor():
            self.turn_count += 1
            self.start_turn_phase()

        self.check_player_defeat()
