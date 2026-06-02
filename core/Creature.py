class Creature:
    """
    Базовый класс для всех живых существ.
    Статусы: vulnerable, weak, wet, ignited, poison.
    Баффы: strength (Ярость), thorns (Шипы).
    """
    def __init__(self, name, hp, max_hp):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.shield = 0

        self.wet = 0
        self.ignited = 0
        self.poison = 0
        self.vulnerable = 0
        self.weak = 0

        self.strength = 0
        self.thorns = 0

    def gain_shield(self, amount):
        self.shield += amount
        print(f"[{self.name}] получает +{amount} к щиту. Текущий щит: {self.shield}")

    def take_damage(self, amount, attacker=None):
        # Уязвимость уже учтена в EffectCalculator -- здесь не трогаем
        print(f"[{self.name}] атакован на {amount} урона. (Щит: {self.shield}, HP: {self.hp})")

        if self.shield >= amount:
            self.shield -= amount
        else:
            damage_left = amount - self.shield
            self.shield = 0
            self.hp -= damage_left

        self.hp = max(self.hp, 0)
        print(f"[{self.name}] Итог -> Осталось щита: {self.shield}, Осталось HP: {self.hp}")

        if self.thorns > 0 and attacker is not None:
            print(f" [ШИПЫ] {self.name} отражает {self.thorns} урона на {attacker.name}!")
            attacker.hp = max(attacker.hp - self.thorns, 0)

    def tick_statuses(self, combat_manager=None):
        """Тикает статусы в конце хода. Баффы (strength, thorns) не трогаем."""
        if self.vulnerable > 0:
            self.vulnerable -= 1
            if self.vulnerable == 0:
                print(f" [Статус] Уязвимость на существе {self.name} прошла.")

        if self.weak > 0:
            self.weak -= 1
            if self.weak == 0:
                print(f" [Статус] Слабость на существе {self.name} прошла.")

        if self.ignited > 0:
            # Базовый урон от горения + бонус от реликвий
            ignite_dmg = 3
            if combat_manager and hasattr(combat_manager, 'gm') and combat_manager.gm:
                for relic in combat_manager.gm.relics:
                    ignite_dmg += relic.on_tick_ignited(self)
            print(f" [Горение] {self.name} получает {ignite_dmg} урона от огня!")
            self.hp = max(self.hp - ignite_dmg, 0)
            self.ignited -= 1
            if self.ignited == 0:
                print(f" [Статус] Огонь на {self.name} потух.")

        if self.poison > 0:
            print(f" [ЯД] {self.name} получает {self.poison} урона от токсинов сквозь щиты!")
            self.hp = max(self.hp - self.poison, 0)
            self.poison -= 1
            if self.poison == 0:
                print(f" [Статус] Яд в теле {self.name} полностью рассеялся.")

        if self.wet > 0:
            self.wet -= 1
            if self.wet == 0:
                print(f" [Статус] {self.name} высох.")