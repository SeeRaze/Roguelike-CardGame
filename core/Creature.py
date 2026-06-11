from core.StatusRegistry import all_keys

_STATUS_KEYS = set(all_keys())

# Статусы, блокируемые МагоМ через «Стихийный барьер» (половинки ХОТФИКСа)
_ELEMENTAL_KEYS = frozenset(("coffee", "legacy"))


class Creature:
    # Потолок лечения от статуса «регенерация» за один тик (см. tick_statuses).
    # Режет перекормленные стаки регена, не трогая одиночные хил-карты.
    REGEN_HEAL_CAP_PER_TURN = 6

    # Доля НЕДОСТАЮЩЕГО HP, восстанавливаемая «Отдыхом» у костра (см. rest_heal_amount).
    REST_HEAL_PCT = 0.30

    def __init__(self, name, hp, max_hp):
        self.name   = name
        self.hp     = hp
        self.max_hp = max_hp
        self.shield = 0
        # Позиция в партии — 2D-сетка (core/positioning): РАНГ × ЛИНИЯ.
        #   rank: FRONT/BACK (ось фронт/тыл, перехват)  — core/positioning.Rank
        #   line: LEFT/CENTER/RIGHT (ось линий, соседство) — core/positioning.Line
        # Дефолт None у обоих = «позиции нет» (позиционка off) → весь позиционный код
        # инертен. Инициализируем здесь, т.к. кастомный __getattr__ кинул бы
        # AttributeError при чтении неинициализированного атрибута.
        self.rank   = None
        self.line   = None
        object.__setattr__(self, 'statuses', {k: 0 for k in _STATUS_KEYS})

    def __getattr__(self, name):
        statuses = object.__getattribute__(self, 'statuses')
        if name in statuses:
            return statuses[name]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name, value):
        if name in _STATUS_KEYS:
            object.__getattribute__(self, 'statuses')[name] = value
        else:
            object.__setattr__(self, name, value)

    def get_status(self, key: str) -> int:
        return self.statuses.get(key, 0)

    def set_status(self, key: str, value: int):
        if key in _STATUS_KEYS:
            self.statuses[key] = max(0, value)

    def add_status(self, key: str, amount: int, combat_manager=None):
        if key not in _STATUS_KEYS:
            return

        # Блок стихий от способности Мага (Try-Except) -- только на врага
        if (key in _ELEMENTAL_KEYS
                and combat_manager is not None
                and getattr(combat_manager, '_elemental_blocked', False)
                and self in getattr(combat_manager, 'enemies', [])):
            combat_manager.add_log_message(
                f"[ВАЙБ-КОДЕР] Try-Except: {key} заблокирован!"
            )
            return

        self.statuses[key] = max(0, self.statuses.get(key, 0) + amount)

        if key == "wet" and combat_manager:
            gm = getattr(combat_manager, 'gm', None)
            if gm:
                for relic in gm.relics:
                    relic.on_wet_applied(combat_manager)

    # ------------------------------------------------------------------
    # Боевые методы
    # ------------------------------------------------------------------
    def heal(self, amount: int, combat_manager=None):
        # CRASH REBOOT (С58): «Перезагрузка» блокирует восстановление HP/реген.
        if self.get_status('heal_block') > 0:
            print(f"[{self.name}] восстановление заблокировано (Перезагрузка).")
            return 0
        healed = min(amount, self.max_hp - self.hp)
        self.hp += healed
        print(f"[{self.name}] восстанавливает {healed} HP. "
              f"Текущее HP: {self.hp}/{self.max_hp}")

        if healed > 0 and combat_manager:
            gm = getattr(combat_manager, 'gm', None)
            if gm:
                for relic in gm.relics:
                    relic.on_heal(healed, self)
            if hasattr(self, 'on_heal_passive'):
                self.on_heal_passive(healed, combat_manager)

        return healed

    def _hp_floor(self) -> int:
        """Пол HP — нижняя граница, до которой может опуститься self.hp.

        Норма → 0 (старое поведение, все клампы байт-в-байт). При HP-ОВЕРДРАФТЕ
        (субстрат Берсерка «Отрицание Смерти», флаг self.hp_overdraft) → отрицательный
        пол hp_debt_floor(max_hp) = −50% от max HP (С57: ПРОЦЕНТ, не флат — масштаб-
        инвариантно к росту max HP). HP уходит в МИНУС (долг жизни), глубина минуса даёт
        множитель урона (EffectCalculator), а достижение пола = неминуемая смерть
        (defeat-проверка). Дефолт-инертен: у врагов/обычных классов флага нет → пол 0."""
        if getattr(self, 'hp_overdraft', False):
            from core.debt import hp_debt_floor
            return hp_debt_floor(self.max_hp)
        return 0

    def lose_hp(self, amount: int) -> int:
        """Прямой урон СКВОЗЬ ЩИТ — напрямую в HP, минуя shield.
        Идиом из berserker.py / DetonationRegistry / яд («сквозь щит»).
        Переиспользуется вне боя (Ритуал крови костра, Проклятый сундук)
        и не дёргает боевые хуки (шипы/вампир). Возвращает фактический урон."""
        lost = max(0, min(amount, self.hp - self._hp_floor()))
        self.hp -= lost
        print(f"[{self.name}] теряет {lost} HP сквозь щит. "
              f"Текущее HP: {self.hp}/{self.max_hp}")
        return lost

    @staticmethod
    def rest_heal_amount(hp: int, max_hp: int) -> int:
        """Лечение «Отдыха» у костра: 30% от НЕДОСТАЮЩЕГО HP (Balatro-стиль —
        чем ближе к смерти, тем эффективнее). Пьюр-формула без побочек,
        тестируется без pygame. При полном HP вернёт 0."""
        return int((max_hp - hp) * Creature.REST_HEAL_PCT)

    def gain_shield(self, amount, combat_manager=None):
        # Декомпиляция (С58): пока висит — генерация щита заглушена (анти-щит «окно
        # эксплойта»). Гейт ДО прибавления → ноль щита, пока decomp активна.
        if amount > 0 and self.statuses.get('decomp', 0) > 0:
            print(f"[{self.name}] генерация щита заглушена (Декомпиляция).")
            if combat_manager:
                combat_manager.add_log_message(
                    f" [ДЕКОМП] Генерация щита {self.name} заглушена."
                )
            return
        self.shield += amount
        print(f"[{self.name}] получает +{amount} к щиту. "
              f"Текущий щит: {self.shield}")
        if amount > 0 and combat_manager:
            gm = getattr(combat_manager, 'gm', None)
            if gm:
                for relic in gm.relics:
                    relic.on_shield_gained(amount, self, combat_manager)

    def take_damage(self, amount, attacker=None, combat_manager=None):
        print(f"[{self.name}] атакован на {amount} урона. "
              f"(Щит: {self.shield}, HP: {self.hp})")
        if self.shield >= amount:
            self.shield -= amount
        else:
            damage_left = amount - self.shield
            self.shield = 0
            self.hp    -= damage_left
        self.hp = max(self.hp, self._hp_floor())
        print(f"[{self.name}] Итог -> Щит: {self.shield}, HP: {self.hp}")

        if self.statuses.get('thorns', 0) > 0 and attacker is not None:
            print(f" [ШИПЫ] {self.name} отражает "
                  f"{self.statuses['thorns']} урона на {attacker.name}!")
            attacker.hp = max(attacker.hp - self.statuses['thorns'], attacker._hp_floor())

        if amount > 0 and attacker is not None:
            vamp = attacker.statuses.get('vampire', 0)
            if vamp > 0:
                # Вампиризм лечит на 40% нанесённого урона (было 50%). Доля
                # снижена, чтобы sustain Разбойника не перекрывал урон врага
                # на поздних этажах. Тема «кровь» сохранена.
                heal_amount = max(1, amount * 2 // 5)
                attacker.heal(heal_amount, combat_manager)
                # Стак вампиризма гаснет ВТРОЕ за триггер (а не вдвое): меньше
                # «бесплатных» лечащих ударов с одного наложения.
                decayed = vamp // 3
                attacker.statuses['vampire'] = decayed
                if combat_manager:
                    combat_manager.add_log_message(
                        f" [ВАМПИР] Вы восстанавливаете {heal_amount} HP. "
                        f"Вампиризм: {vamp} → {decayed}."
                    )

        bleed = self.statuses.get('bleed', 0)
        if bleed > 0 and amount > 0:
            bleed_dmg = bleed
            if combat_manager:
                gm = getattr(combat_manager, 'gm', None)
                if gm:
                    for relic in gm.relics:
                        bleed_dmg = relic.on_bleed_tick(
                            bleed_dmg, self, combat_manager
                        )
            print(f" [КРОВЬ] {self.name} истекает кровью: +{bleed_dmg} урона!")
            self.hp = max(self.hp - bleed_dmg, self._hp_floor())
            if combat_manager:
                combat_manager.add_log_message(
                    f" [КРОВЬ] {self.name} получает +{bleed_dmg} "
                    f"от кровотечения!"
                )

    def tick_statuses(self, combat_manager=None):
        s = self.statuses

        for key in ('vulnerable', 'weak', 'wet', 'decomp', 'stunned',
                    'heal_block'):
            if s.get(key, 0) > 0:
                s[key] -= 1
                if s[key] == 0:
                    print(f" [Статус] {key} на {self.name} прошёл.")

        if s.get('ignited', 0) > 0:
            ignite_dmg = 3
            if combat_manager and hasattr(combat_manager, 'gm') \
                    and combat_manager.gm:
                for relic in combat_manager.gm.relics:
                    ignite_dmg += relic.on_tick_ignited(self)
            print(f" [Горение] {self.name} получает {ignite_dmg} урона!")
            self.hp = max(self.hp - ignite_dmg, 0)
            s['ignited'] -= 1
            if s['ignited'] == 0:
                print(f" [Статус] Огонь на {self.name} потух.")

        # Legacy-код (DoT, С58): УВАЖАЕТ щит. КИСЛОТНЫЙ ДОЖДЬ (Legacy+Токс): Токс
        # делает Legacy ПРОБИВАЮЩИМ щит (кислота ест броню) — дом «пробития»
        # поглощённого Яда, заработок за сетап. Декей-триангуляр: −1 стак/ход.
        if s.get('legacy', 0) > 0:
            dmg = s['legacy']
            if s.get('tox', 0) > 0:
                # Кислотный дождь: напрямую в HP, сквозь щит.
                self.hp = max(self.hp - dmg, 0)
                print(f" [КИСЛОТНЫЙ ДОЖДЬ] {self.name}: {dmg} урона СКВОЗЬ щит.")
            else:
                absorbed = min(self.shield, dmg)
                self.shield -= absorbed
                rem = dmg - absorbed
                if rem > 0:
                    self.hp = max(self.hp - rem, 0)
                print(f" [LEGACY] {self.name} получает {dmg} урона "
                      f"(щит впитал {absorbed}).")
            s['legacy'] -= 1
            if s['legacy'] == 0:
                print(f" [Статус] Legacy-код в {self.name} дочитан.")

        if s.get('regen', 0) > 0:
            # Потолок лечения от регена за один тик: высокие стаки регена
            # (несколько хил-карт сразу) больше не возвращают HP «на полную».
            regen_heal = min(s['regen'], self.REGEN_HEAL_CAP_PER_TURN)
            healed = self.heal(regen_heal, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f" [РЕГЕН] {self.name} восстанавливает {healed} HP."
                )
            s['regen'] -= 1
            if s['regen'] == 0:
                print(f" [Статус] Регенерация на {self.name} иссякла.")

        if s.get('bleed', 0) > 0:
            gm = getattr(combat_manager, 'gm', None) if combat_manager else None
            has_gniloy_klyk = gm and any(
                r.name == "Гнилой Клык" for r in gm.relics
            )
            # Разбойник врождённо «бередит раны»: его Кровотечение убывает вдвое,
            # а не в ноль — это даёт frenzy-усиленным наложениям накапливаться
            # (движок кат.4). Проверяем класс игрока через combat_manager.
            player = getattr(combat_manager, 'player', None) if combat_manager else None
            is_rogue = type(player).__name__ == "Rogue" if player else False
            if has_gniloy_klyk or is_rogue:
                s['bleed'] = s['bleed'] // 2
                print(f" [Статус] Кровотечение на {self.name} "
                      f"уменьшилось до {s['bleed']}.")
            else:
                s['bleed'] = 0
                print(f" [Статус] Кровотечение на {self.name} остановилось.")