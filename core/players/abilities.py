# core/players/abilities.py
# Активные способности всех классов игрока.

from core.players.ability import ClassAbility


class WarriorAbility(ClassAbility):
    """
    «Щитовой удар»
    Наносит врагу урон равный 50% текущего щита Воина.
    Один раз за бой.
    """

    def __init__(self):
        super().__init__(
            name="Щитовой удар",
            description="Нанести врагу урон = 50% текущего щита.\nОдин раз за бой.",
        )

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        shield = combat_manager.player.shield
        if shield <= 0:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': нет щита для удара!"
            )
            return False

        dmg = max(1, shield // 2)
        combat_manager.enemy.take_damage(dmg, attacker=combat_manager.player,
                                         combat_manager=combat_manager)
        self._used = True
        combat_manager.add_log_message(
            f"[ВОИН] Щитовой удар: {dmg} урона врагу (50% от {shield} щита)!"
        )
        return True


class RogueAbility(ClassAbility):
    """
    «Вскрытие»
    Удваивает текущее кровотечение на враге.
    Взамен: -1 энергия в следующем ходу.
    Один раз за бой.
    """

    def __init__(self):
        super().__init__(
            name="Вскрытие",
            description="Удвоить кровотечение на враге.\n-1 энергия в следующем ходу.\nОдин раз за бой.",
        )
        self._penalty_pending = False

    def on_combat_start(self, combat_manager) -> None:
        super().on_combat_start(combat_manager)
        self._penalty_pending = False

    def on_turn_start(self, combat_manager) -> None:
        if self._penalty_pending:
            combat_manager.player.energy = max(
                0, combat_manager.player.energy - 1
            )
            combat_manager.add_log_message(
                "[РАЗБОЙНИК] Вскрытие: -1 энергия (штраф прошлого хода)."
            )
            self._penalty_pending = False

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        bleed = combat_manager.enemy.bleed
        if bleed <= 0:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': у врага нет кровотечения!"
            )
            return False

        combat_manager.enemy.bleed *= 2
        self._used            = True
        self._penalty_pending = True
        combat_manager.add_log_message(
            f"[РАЗБОЙНИК] Вскрытие: кровотечение {bleed} -> "
            f"{combat_manager.enemy.bleed}! -1 энергия в следующем ходу."
        )
        return True


class MageAbility(ClassAbility):
    """
    «Стихийный барьер»
    Блокирует наложение стихий на врага на 1 ход.
    Взамен: щит = сумма всех стихийных стаков на поле * 3.
    Один раз за бой.

    Стихийные статусы: ignited, wet, poison (яд -- стихийный у Мага).
    Флаг _elemental_blocked проверяется в Creature.add_status.
    """

    ELEMENTAL_STATUSES = ("ignited", "wet", "poison")

    def __init__(self):
        super().__init__(
            name="Стихийный барьер",
            description="Блокировать стихии на врага на 1 ход.\n"
                        "Щит = сумма стихийных стаков * 3.\n"
                        "Один раз за бой.",
        )

    def on_combat_start(self, combat_manager) -> None:
        super().on_combat_start(combat_manager)

    def on_turn_start(self, combat_manager) -> None:
        """Снимаем блок в начале следующего хода."""
        if getattr(combat_manager, '_elemental_blocked', False):
            combat_manager._elemental_blocked = False
            combat_manager.add_log_message(
                "[МАГ] Стихийный барьер: блок стихий снят."
            )

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        # Считаем сумму стихийных стаков на обоих существах
        total = 0
        for creature in (combat_manager.player, combat_manager.enemy):
            for key in self.ELEMENTAL_STATUSES:
                total += max(0, getattr(creature, key, 0))

        shield_gain = total * 3
        combat_manager._elemental_blocked = True
        self._used = True

        if shield_gain > 0:
            combat_manager.player.gain_shield(shield_gain, combat_manager)
            combat_manager.add_log_message(
                f"[МАГ] Стихийный барьер: +{shield_gain} щита "
                f"(стаки {total} * 3)! Стихии заблокированы на 1 ход."
            )
        else:
            combat_manager.add_log_message(
                "[МАГ] Стихийный барьер: стихий нет, щит не получен. "
                "Стихии заблокированы на 1 ход."
            )
        return True


class DruidAbility(ClassAbility):
    """
    «Токсичный взрыв»
    Снимает весь яд с врага, наносит этот урон разом.
    Друид получает Регенерацию = половина снятого яда.
    Один раз за бой.
    """

    def __init__(self):
        super().__init__(
            name="Токсичный взрыв",
            description="Снять весь яд с врага, нанести разом.\n"
                        "Регенерация = половина снятого яда.\n"
                        "Один раз за бой.",
        )

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        poison = combat_manager.enemy.poison
        if poison <= 0:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': у врага нет яда!"
            )
            return False

        combat_manager.enemy.poison = 0
        combat_manager.enemy.take_damage(
            poison, attacker=combat_manager.player,
            combat_manager=combat_manager
        )

        regen_gain = max(1, poison // 2)
        combat_manager.player.add_status("regen", regen_gain, combat_manager)

        self._used = True
        combat_manager.add_log_message(
            f"[ДРУИД] Токсичный взрыв: {poison} урона врагу! "
            f"+{regen_gain} Регенерации Друиду."
        )
        return True


class BerserkerAbility(ClassAbility):
    """
    «Кровавая ярость»
    Берсерк наносит себе урон сквозь щит (10% макс HP, мин 1).
    Взамен получает Ярость = нанесённый урон * 2.
    Один раз за бой.
    """

    def __init__(self):
        super().__init__(
            name="Кровавая ярость",
            description="Нанести себе 10% макс HP сквозь щит.\n"
                        "Ярость = урон * 2.\n"
                        "Один раз за бой.",
        )

    def activate(self, combat_manager) -> bool:
        if self._used:
            combat_manager.add_log_message(
                f"[Способность] '{self.name}': уже использована!"
            )
            return False

        player = combat_manager.player
        self_dmg = max(1, player.max_hp // 10)

        # Урон сквозь щит -- напрямую в HP
        player.hp = max(0, player.hp - self_dmg)
        strength_gain = self_dmg * 2

        player.strength += strength_gain
        self._used = True

        combat_manager.add_log_message(
            f"[БЕРСЕРК] Кровавая ярость: -{self_dmg} HP себе, "
            f"+{strength_gain} Ярости!"
        )

        if player.hp <= 0:
            combat_manager.add_log_message(
                "[!] Берсерк пал от собственной ярости..."
            )
        return True