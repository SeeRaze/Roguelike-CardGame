# core/Creature.py
# Базовый класс для всех живых существ.
# Статусы хранятся в self.statuses = {} -- единый словарь.
# Обратная совместимость: creature.weak, creature.vulnerable и т.д.
# работают через __getattr__ / __setattr__ без изменений в других файлах.

from core.StatusRegistry import all_keys

# Ключи статусов -- всё что идёт через self.statuses
_STATUS_KEYS = set(all_keys())


class Creature:
    def __init__(self, name, hp, max_hp):
        self.name   = name
        self.hp     = hp
        self.max_hp = max_hp
        self.shield = 0
        # Единый словарь статусов (все значения начинаются с 0)
        object.__setattr__(self, 'statuses', {k: 0 for k in _STATUS_KEYS})

    # ------------------------------------------------------------------
    # Прозрачный доступ: creature.weak  <->  creature.statuses["weak"]
    # ------------------------------------------------------------------
    def __getattr__(self, name):
        # Вызывается только если атрибут НЕ найден обычным путём
        statuses = object.__getattribute__(self, 'statuses')
        if name in statuses:
            return statuses[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in _STATUS_KEYS:
            # Пишем в словарь статусов
            object.__getattribute__(self, 'statuses')[name] = value
        else:
            object.__setattr__(self, name, value)

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------
    def get_status(self, key: str) -> int:
        """Явное чтение статуса по ключу."""
        return self.statuses.get(key, 0)

    def set_status(self, key: str, value: int):
        """Явная запись статуса по ключу."""
        if key in _STATUS_KEYS:
            self.statuses[key] = max(0, value)

    def add_status(self, key: str, amount: int):
        """Добавить к статусу (накопление)."""
        if key in _STATUS_KEYS:
            self.statuses[key] = max(0, self.statuses.get(key, 0) + amount)

    # ------------------------------------------------------------------
    # Боевые методы
    # ------------------------------------------------------------------
    def gain_shield(self, amount):
        self.shield += amount
        print(f"[{self.name}] получает +{amount} к щиту. Текущий щит: {self.shield}")

    def take_damage(self, amount, attacker=None):
        print(f"[{self.name}] атакован на {amount} урона. (Щит: {self.shield}, HP: {self.hp})")
        if self.shield >= amount:
            self.shield -= amount
        else:
            damage_left = amount - self.shield
            self.shield = 0
            self.hp    -= damage_left
        self.hp = max(self.hp, 0)
        print(f"[{self.name}] Итог -> Осталось щита: {self.shield}, Осталось HP: {self.hp}")

        if self.statuses.get('thorns', 0) > 0 and attacker is not None:
            print(f" [ШИПЫ] {self.name} отражает {self.statuses['thorns']} урона на {attacker.name}!")
            attacker.hp = max(attacker.hp - self.statuses['thorns'], 0)

    def tick_statuses(self, combat_manager=None):
        """Тикает статусы в конце хода. Баффы (strength, thorns) не убывают."""
        s = self.statuses  # короткий псевдоним

        # Длительностные дебаффы -- убывают на 1
        for key in ('vulnerable', 'weak', 'wet'):
            if s.get(key, 0) > 0:
                s[key] -= 1
                if s[key] == 0:
                    print(f" [Статус] {key} на {self.name} прошёл.")

        # Горение -- урон + убывает
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

        # Яд -- урон сквозь щит + убывает
        if s.get('poison', 0) > 0:
            print(f" [ЯД] {self.name} получает {s['poison']} урона от токсинов сквозь щиты!")
            self.hp = max(self.hp - s['poison'], 0)
            s['poison'] -= 1
            if s['poison'] == 0:
                print(f" [Статус] Яд в теле {self.name} полностью рассеялся.")