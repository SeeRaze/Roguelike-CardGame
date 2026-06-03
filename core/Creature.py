from core.StatusRegistry import all_keys

_STATUS_KEYS = set(all_keys())


class Creature:
    def __init__(self, name, hp, max_hp):
        self.name   = name
        self.hp     = hp
        self.max_hp = max_hp
        self.shield = 0
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
        if key in _STATUS_KEYS:
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
        healed = min(amount, self.max_hp - self.hp)
        self.hp += healed
        print(f"[{self.name}] восстанавливает {healed} HP. "
              f"Текущее HP: {self.hp}/{self.max_hp}")

        if healed > 0 and combat_manager:
            gm = getattr(combat_manager, 'gm', None)
            # Хук on_heal -- реликвии реагируют на хил
            if gm:
                for relic in gm.relics:
                    relic.on_heal(healed, self)
            # Хук классовой пассивки -- только для игрока (Druid: Токсичный круговорот)
            if hasattr(self, 'on_heal_passive'):
                self.on_heal_passive(healed, combat_manager)

        return healed

    def gain_shield(self, amount, combat_manager=None):
        self.shield += amount
        print(f"[{self.name}] получает +{amount} к щиту. "
              f"Текущий щит: {self.shield}")
        # Хук on_shield_gained
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
        self.hp = max(self.hp, 0)
        print(f"[{self.name}] Итог -> Щит: {self.shield}, HP: {self.hp}")

        # Шипы
        if self.statuses.get('thorns', 0) > 0 and attacker is not None:
            print(f" [ШИПЫ] {self.name} отражает "
                f"{self.statuses['thorns']} урона на {attacker.name}!")
            attacker.hp = max(attacker.hp - self.statuses['thorns'], 0)

        # Вампиризм атакующего -- триггер при любом уроне > 0
        if amount > 0 and attacker is not None:
            vamp = attacker.statuses.get('vampire', 0)
            if vamp > 0:
                heal_amount = max(1, amount // 2)
                attacker.heal(heal_amount, combat_manager)
                attacker.statuses['vampire'] = vamp // 2
                if combat_manager:
                    combat_manager.add_log_message(
                        f" [ВАМПИР] Вы восстанавливаете {heal_amount} HP. "
                        f"Вампиризм: {vamp} → {vamp // 2}."
                    )

        # Кровотечение -- с хуком on_bleed_tick
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
            self.hp = max(self.hp - bleed_dmg, 0)
            if combat_manager:
                combat_manager.add_log_message(
                    f" [КРОВЬ] {self.name} получает +{bleed_dmg} "
                    f"от кровотечения!"
                )

    def tick_statuses(self, combat_manager=None):
        s = self.statuses

        for key in ('vulnerable', 'weak', 'wet'):
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

        if s.get('poison', 0) > 0:
            print(f" [ЯД] {self.name} получает {s['poison']} урона от яда!")
            self.hp = max(self.hp - s['poison'], 0)
            s['poison'] -= 1
            if s['poison'] == 0:
                print(f" [Статус] Яд в теле {self.name} рассеялся.")

        if s.get('regen', 0) > 0:
            healed = self.heal(s['regen'], combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f" [РЕГЕН] {self.name} восстанавливает {healed} HP."
                )
            s['regen'] -= 1
            if s['regen'] == 0:
                print(f" [Статус] Регенерация на {self.name} иссякла.")

        # Кровотечение -- сброс с учётом реликвий
        if s.get('bleed', 0) > 0:
            gm = getattr(combat_manager, 'gm', None) if combat_manager else None
            has_gniloy_klyk = gm and any(
                r.name == "Гнилой Клык" for r in gm.relics
            )
            if has_gniloy_klyk:
                s['bleed'] = s['bleed'] // 2
                print(f" [Статус] Кровотечение на {self.name} "
                      f"уменьшилось до {s['bleed']}.")
            else:
                s['bleed'] = 0
                print(f" [Статус] Кровотечение на {self.name} остановилось.")