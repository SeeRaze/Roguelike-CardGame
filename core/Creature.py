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
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

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
    def heal(self, amount: int):
        healed = min(amount, self.max_hp - self.hp)
        self.hp += healed
        print(f"[{self.name}] восстанавливает {healed} HP. Текущее HP: {self.hp}/{self.max_hp}")
        return healed

    def gain_shield(self, amount):
        self.shield += amount
        print(f"[{self.name}] получает +{amount} к щиту. Текущий щит: {self.shield}")

    def take_damage(self, amount, attacker=None, combat_manager=None):
        print(f"[{self.name}] атакован на {amount} урона. (Щит: {self.shield}, HP: {self.hp})")
        if self.shield >= amount:
            self.shield -= amount
        else:
            damage_left = amount - self.shield
            self.shield = 0
            self.hp    -= damage_left
        self.hp = max(self.hp, 0)
        print(f"[{self.name}] Итог -> Осталось щита: {self.shield}, Осталось HP: {self.hp}")

        # Шипы -- отражение урона атакующему
        if self.statuses.get('thorns', 0) > 0 and attacker is not None:
            print(f" [ШИПЫ] {self.name} отражает {self.statuses['thorns']} урона на {attacker.name}!")
            attacker.hp = max(attacker.hp - self.statuses['thorns'], 0)

        # Кровотечение -- доп. урон сквозь щит при каждом ударе (только если amount > 0)
        bleed = self.statuses.get('bleed', 0)
        if bleed > 0 and amount > 0:
            print(f" [КРОВЬ] {self.name} истекает кровью: +{bleed} урона!")
            self.hp = max(self.hp - bleed, 0)
            if combat_manager:
                combat_manager.add_log_message(
                    f" [КРОВЬ] {self.name} получает +{bleed} от кровотечения!"
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
            if combat_manager and hasattr(combat_manager, 'gm') and combat_manager.gm:
                for relic in combat_manager.gm.relics:
                    ignite_dmg += relic.on_tick_ignited(self)
            print(f" [Горение] {self.name} получает {ignite_dmg} урона от огня!")
            self.hp = max(self.hp - ignite_dmg, 0)
            s['ignited'] -= 1
            if s['ignited'] == 0:
                print(f" [Статус] Огонь на {self.name} потух.")

        if s.get('poison', 0) > 0:
            print(f" [ЯД] {self.name} получает {s['poison']} урона от токсинов сквозь щиты!")
            self.hp = max(self.hp - s['poison'], 0)
            s['poison'] -= 1
            if s['poison'] == 0:
                print(f" [Статус] Яд в теле {self.name} полностью рассеялся.")

        if s.get('regen', 0) > 0:
            healed = self.heal(s['regen'])
            if combat_manager:
                combat_manager.add_log_message(
                    f" [РЕГЕН] {self.name} восстанавливает {healed} HP."
                )
            s['regen'] -= 1
            if s['regen'] == 0:
                print(f" [Статус] Регенерация на {self.name} иссякла.")

        # Кровотечение -- полностью снимается в конце хода
        if s.get('bleed', 0) > 0:
            s['bleed'] = 0
            print(f" [Статус] Кровотечение на {self.name} остановилось.")