from core.EffectCalculator import EffectCalculator  # Указываем новый путь к калькулятору

class DamageEffect:
    """Кирпичик №1: Нанесение урона с безопасной передачей менеджеров"""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        
        # БЕЗОПАСНОЕ ИЗВЛЕЧЕНИЕ: если combat_manager есть, берем его gm, иначе None
        gm_ref = combat_manager.gm if combat_manager is not None else None
        
        final_dmg = EffectCalculator.calculate_damage(
            attacker=player, 
            target=enemy, 
            base_damage=base, 
            game_manager=gm_ref,
            combat_manager=combat_manager
        )
        enemy.take_damage(final_dmg)
        if combat_manager:
            combat_manager.add_log_message(f" -> {enemy.name} получает {final_dmg} урона.")
        # Фиксируем самый мощный удар в статистику GameManager
        if combat_manager and combat_manager.gm:
            if final_dmg > combat_manager.gm.stats["max_damage_dealt"]:
                combat_manager.gm.stats["max_damage_dealt"] = final_dmg
                print(f" [РЕКОРД УРОНА] Новый мощный удар: {final_dmg} ед.!")

class ShieldEffect:
    """Кирпичик №2: Наложение брони/щита на игрока"""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        shield_amount = self.upgrade_val if is_upgraded else self.base_val
        player.gain_shield(shield_amount)
        if combat_manager:
            combat_manager.add_log_message(f" -> Вы получаете +{shield_amount} щита.")


class StatusEffect:
    """Кирпичик №3: Наложение любых статусных дебаффов (слабость, уязвимость, стихии)"""
    def __init__(self, status_type, base_turns, upgrade_turns):
        self.status_type = status_type  # "weak", "vulnerable", "wet", "ignited"
        self.base_turns = base_turns
        self.upgrade_turns = upgrade_turns

    def execute(self, player, enemy, combat_manager, is_upgraded):
        turns = self.upgrade_turns if is_upgraded else self.base_turns
        
        if self.status_type == "weak": enemy.weak += turns
        elif self.status_type == "vulnerable": enemy.vulnerable += turns
        elif self.status_type == "wet": enemy.wet += turns
        elif self.status_type == "ignited": enemy.ignited += turns
        
        if combat_manager:
            combat_manager.add_log_message(f" -> На {enemy.name} наложен статус {self.status_type} ({turns} х.)")


class Card:
    """Универсальный класс-конструктор карт. Собирается из списка эффектов effects."""
    def __init__(self, name, cost, card_type, description, effects):
        self.name = name
        self.cost = cost
        self.card_type = card_type
        self.description = description
        self.effects = effects  # Сюда мы передаем массив из кирпичиков выше
        self.upgraded = False

    def upgrade(self):
        """Прокачка карты активирует логику изменения описаний у её кирпичиков"""
        if not self.upgraded:
            self.upgraded = True
            self.name += "+"
            self.apply_upgrade_logic()

    def apply_upgrade_logic(self):
        """Динамически пересобирает описание на лету (напишем автоматику чуть позже, пока заглушка)"""
        pass

    def apply(self, player, enemy, combat_manager=None):
        """Карта просто по очереди запускает каждый кирпичик из своего набора"""
        for effect in self.effects:
            effect.execute(player, enemy, combat_manager, self.upgraded)


# ==============================================================================
#  ФАБРИКА СТАРТОВЫХ КАРТ (Генерируем объекты карт из кирпичиков в одну строчку!)
# ==============================================================================
def create_strike():
    return Card("Удар", 1, "attack", "Наносит 6 (9) урона.", [DamageEffect(6, 9)])

def create_defend():
    return Card("Защита", 1, "defense", "Дает 5 (8) щита.", [ShieldEffect(5, 8)])

def create_bash():
    return Card("Скручивание", 2, "attack", "Урон 8(12). Уязвимость 2(3) х.", [
        DamageEffect(8, 12),
        StatusEffect("vulnerable", 2, 3)
    ])

def create_neutralize():
    return Card("Нейтрализация", 0, "attack", "Урон 3(4). Слабость 1(2) х.", [
        DamageEffect(3, 4),
        StatusEffect("weak", 1, 2)
    ])

def create_splash():
    return Card("Всплеск", 1, "attack", "Урон 2(4). Мокрый на 3(4) х.", [
        DamageEffect(2, 4),
        StatusEffect("wet", 3, 4)
    ])

def create_ignite():
    return Card("Поджог", 1, "attack", "Урон 2(4). Горение на 3(4) х.", [
        DamageEffect(2, 4),
        StatusEffect("ignited", 3, 4)
    ])
