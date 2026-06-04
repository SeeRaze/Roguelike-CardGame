# core/cards/base.py
from core.EffectCalculator import EffectCalculator
from core.StatusRegistry import STATUSES
from core.rarity import Rarity


class DamageEffect:
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        base = self.upgrade_val if is_upgraded else self.base_val
        gm_ref = combat_manager.gm if combat_manager is not None else None
        final_dmg = EffectCalculator.calculate_damage(
            player, enemy, base, gm_ref, combat_manager
        )
        enemy.take_damage(final_dmg, attacker=player, combat_manager=combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> {enemy.name} получает {final_dmg} урона."
            )


class VampireDamageEffect:
    """DEPRECATED: заменён на VampireBuffEffect в vampirism.py.
    Оставлен для обратной совместимости импортов в CardRenderer.py."""
    def __init__(self, base_val, upgrade_val):
        self.base_val    = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        # Старая логика — больше не используется в картах
        pass


class ShieldEffect:
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        shield_amount = self.upgrade_val if is_upgraded else self.base_val
        player.gain_shield(shield_amount, combat_manager)  # ← добавить
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Вы получаете +{shield_amount} щита."
            )


class HealEffect:
    """Восстанавливает HP игрока. Не превышает max_hp."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        healed = player.heal(amount, combat_manager)   # <-- передаём cm
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Вы восстанавливаете {healed} HP."
            )


class RegenEffect:
    """Накладывает статус регенерации на игрока."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.add_status("regen", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Вы получаете Регенерацию ({amount})."
            )


class StatusEffect:
    def __init__(self, status_type, base_turns, upgrade_turns):
        self.status_type = status_type
        self.base_turns = base_turns
        self.upgrade_turns = upgrade_turns

    def execute(self, player, enemy, combat_manager, is_upgraded):
        turns = self.upgrade_turns if is_upgraded else self.base_turns
        if self.status_type in STATUSES:
            enemy.add_status(self.status_type, turns, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> На {enemy.name} наложен статус "
                f"{self.status_type} ({turns} х.)"
            )


class PoisonEffect:
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        val = self.upgrade_val if is_upgraded else self.base_val
        # Вирулентность (движок кат.4 Друида): +N к каждому наложению яда.
        # У не-Друидов virulence=0 (никогда не растёт) → класс-чек не нужен.
        val += getattr(player, 'virulence', 0)
        enemy.poison += val
        if combat_manager:
            combat_manager.add_log_message(
                f" -> {enemy.name} отравлен на +{val} ед. яда!"
            )


class BarrierEffect:
    """Накладывает Барьер на игрока — несгораемый щит, не сбрасывается между ходами.
    Каждый стак барьера = +1 к щиту при СБРОСЕ в начале хода (см. CombatManager).
    Это движок кат.4 для Воина: «защита = атака» через Возмездие."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        amount = self.upgrade_val if is_upgraded else self.base_val
        player.add_status("barrier", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Барьер +{amount} (всего: {player.barrier})."
            )


class DetonateEffect:
    """Подрывает все ГОТОВЫЕ детонации на цели (см. core/DetonationRegistry.py):
    для каждой записи, чьи requires-статусы все > 0, вызывает handler. Карта с
    этим кирпичом — «детонатор» (напр. «Перегрузка»). Статусы тратит handler.

    requires проверяется заново перед каждым handler — детонация, потратившая
    статусы, корректно гасит зависящие от них последующие."""

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None:
            return
        from core.DetonationRegistry import all_detonations
        for det in all_detonations().values():
            if all(enemy.get_status(req) > 0 for req in det["requires"]):
                combat_manager.add_log_message(det["log"])
                det["handler"](enemy, combat_manager)


class Card:
    def __init__(self, name, cost, card_type, description, effects,
                 rarity=Rarity.COMMON, exile=False, card_class=None):
        self.name = name
        self.cost = cost
        self.card_type = card_type
        self.description = description
        self.effects = effects
        self.rarity = rarity
        self.upgraded = False
        self.exile = exile
        # Принадлежность классу: None = нейтральная (generic), иначе имя класса
        # (напр. "Summoner"). Проставляется централизованно в core/cards/catalog.py.
        self.card_class = card_class

    def upgrade(self):
        if not self.upgraded:
            self.upgraded = True
            self.name += "+"

    def apply(self, player, enemy, combat_manager=None):
        for effect in self.effects:
            effect.execute(player, enemy, combat_manager, self.upgraded)