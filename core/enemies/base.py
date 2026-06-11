import random

from core.Creature import Creature
from core.positioning import intercept_targets


class IntentAttack:
    type = "attack"
    def __init__(self, value): self.value = value

class IntentDefend:
    type = "defend"
    def __init__(self, value): self.value = value

class IntentDebuff:
    type = "debuff"
    def __init__(self, value): self.value = value

class IntentHeal:
    type = "heal"
    def __init__(self, value): self.value = value

class IntentNone:
    type  = "none"
    value = 0


INTENT_REGISTRY = {
    "attack": IntentAttack,
    "defend": IntentDefend,
    "debuff": IntentDebuff,
    "heal":   IntentHeal,
}


class Enemy(Creature):
    """Базовый каркас для всех монстров."""

    def __init__(self, name, hp, max_hp):
        super().__init__(name=name, hp=hp, max_hp=max_hp)
        self.base_test_damage = 0
        self.base_test_shield = 0
        self.intent           = IntentNone()
        self.turn_count       = 0

    # --- Обратная совместимость: старый код читает и пишет .intent_type / .intent_value ---

    @property
    def intent_type(self):
        return self.intent.type

    @intent_type.setter
    def intent_type(self, value: str):
        old_val = self.intent.value if hasattr(self.intent, 'value') else 0
        cls = INTENT_REGISTRY.get(value)
        self.intent = cls(old_val) if cls else IntentNone()

    @property
    def intent_value(self):
        return self.intent.value if hasattr(self.intent, 'value') else 0

    @intent_value.setter
    def intent_value(self, value: int):
        if hasattr(self.intent, 'value'):
            self.intent.value = value
        else:
            self.intent = IntentAttack(value)

    def set_intent(self, intent_type: str, value: int = 0):
        """Атомарная установка намерения — предпочтительный способ."""
        cls = INTENT_REGISTRY.get(intent_type)
        self.intent = cls(value) if cls else IntentNone()

    def choose_intent(self):
        pass

    def _choose_attack_target(self, player, combat_manager):
        """Цель ОДИНОЧНОЙ атаки врага — через ПОЛНЫЙ ПЕРЕХВАТ позиционки.

        Партия = {игрок + союзники}. `intercept_targets` (core/positioning) даёт
        допустимые цели: пока жив ФРОНТ — урон не проходит в ТЫЛ; когда фронт пал —
        открывается тыл. Если позиционка ВЫКЛЮЧЕНА (ни у кого нет ранга), кандидаты
        = {игрок + живые союзники} → выбор байт-в-байт прежний.

        Случайность сохранена (фундамент под статус «провокация»). random.choice
        зовём только при >1 кандидате — иначе цель однозначна (важно: старый код
        не дёргал random без живых союзников; этот инвариант держит тесты)."""
        if not combat_manager:
            return player
        party = [player] + list(getattr(combat_manager, "allies", []))
        candidates = intercept_targets(party)
        if not candidates:
            return player
        if len(candidates) == 1:
            return candidates[0]
        return random.choice(candidates)

    def execute_intent(self, player, combat_manager=None):
        self.turn_count += 1
        # ДИЛЮЦИЯ (Кофе+Токс, С58): обезвреживание — враг не может СПЕЦ-намерения
        # (debuff/heal), только базовая атака/защита. Осознанно ситуативна (против
        # элиток/боссов со спец-намерениями = техника; на трэше = no-op).
        if (self.get_status("coffee") > 0 and self.get_status("tox") > 0
                and self.intent.type in ("debuff", "heal")):
            if combat_manager:
                combat_manager.add_log_message(
                    f" [ДИЛЮЦИЯ] {self.name}: спец-намерение обезврежено."
                )
            return
        if combat_manager:
            combat_manager.add_log_message(f"Ход существа [{self.name}]:")

        from core.EffectCalculator import EffectCalculator
        intent = self.intent

        if isinstance(intent, IntentAttack):
            gm = combat_manager.gm if combat_manager else None
            target = self._choose_attack_target(player, combat_manager)
            final_dmg = EffectCalculator.calculate_damage(
                self, target, intent.value, gm, combat_manager
            )
            target.take_damage(final_dmg, attacker=self, combat_manager=combat_manager)
            if combat_manager:
                if target is player:
                    combat_manager.add_log_message(
                        f" -> Бьет вас на {final_dmg} урона."
                    )
                else:
                    combat_manager.add_log_message(
                        f" -> Бьёт союзника {target.name} на {final_dmg} урона."
                    )
                    combat_manager._check_ally_death(target)

        elif isinstance(intent, IntentDefend):
            self.gain_shield(intent.value, combat_manager)  # ← фикс
            if combat_manager:
                combat_manager.add_log_message(
                    f" -> Закрывается щитом на +{intent.value}."
                )

        elif isinstance(intent, IntentDebuff):
            player.tox += intent.value
            if combat_manager:
                combat_manager.add_log_message(
                    f" -> Накладывает на вас Токсичность ({intent.value})"
                )

        elif isinstance(intent, IntentHeal):
            self.heal(intent.value, combat_manager)
            if combat_manager:
                combat_manager.add_log_message(
                    f" -> Восстанавливает {intent.value} HP."
                )