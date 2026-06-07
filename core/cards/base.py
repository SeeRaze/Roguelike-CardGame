# core/cards/base.py
from core.EffectCalculator import EffectCalculator
from core.StatusRegistry import STATUSES
from core.rarity import Rarity


def _forge_channel_mult(combat_manager, player, channel: str) -> float:
    """Множитель тегов прокачки для оборонного/сустейн канала (shield/heal),
    Развилка №1 (_upgrade_design.md §5). Универсальная ковка: тег на щитовой/
    лечащей карте растит выживаемость `p`. Без ковки/карты/снимка → 1.0 (инертно,
    регресс-нейтрально). Отложенный импорт — реестр тянет EffectCalculator косвенно."""
    from core.ForgeRegistry import forge_effect_multiplier
    return forge_effect_multiplier(combat_manager, player, channel)


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
        # Канал ЩИТА прокачки (Развилка №1): ×mult от оборонных тегов карты.
        mult = _forge_channel_mult(combat_manager, player, "shield")
        if mult != 1.0:
            shield_amount = int(shield_amount * mult)
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
        # Канал ИСЦЕЛЕНИЯ прокачки (Развилка №1): ×mult от сустейн-тегов карты.
        mult = _forge_channel_mult(combat_manager, player, "heal")
        if mult != 1.0:
            amount = int(amount * mult)
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
        # Канал ИСЦЕЛЕНИЯ прокачки (Развилка №1): реген — растянутый хил.
        mult = _forge_channel_mult(combat_manager, player, "heal")
        if mult != 1.0:
            amount = int(amount * mult)
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
        # Канал ЩИТА прокачки (Развилка №1): Барьер = несгораемый щит, компаундит
        # ход-за-ходом → ×mult здесь = истинная экспонента защиты.
        mult = _forge_channel_mult(combat_manager, player, "shield")
        if mult != 1.0:
            amount = int(amount * mult)
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
        from core.ReactionOrder import order_keyed
        # Предохранитель глубины (§10.2): каждый сработавший handler — событие
        # триггера, считается суммарно с Эхо за розыгрыш; на потолке цепочка рвётся.
        guard = getattr(combat_manager, "_trigger_guard", None)
        # Порядок детонаций — по ЯВНОМУ полю priority записи (данные, не позиция в
        # dict), через единый ReactionOrder.order_keyed. requires перепроверяется
        # перед каждым handler → потратившая общий статус детонация гасит зависимые.
        for det_key, det in order_keyed(all_detonations(),
                                        lambda rec: rec["priority"]):
            if all(enemy.get_status(req) > 0 for req in det["requires"]):
                if guard is not None and not guard.enter():
                    combat_manager.add_log_message(
                        "[ПРЕДОХРАНИТЕЛЬ] Каскад детонаций оборван (глубина)."
                    )
                    break
                combat_manager.add_log_message(det["log"])
                det["handler"](enemy, combat_manager)


class TacticalMoveEffect:
    """[Tactical_Move]: атомарно переворачивает СТРОЙ партии (фронт↔тыл) — эффект
    ДЕЙСТВИЯ, а НЕ бесплатная кнопка. Живёт на карте / пассивке реликвии / намерении
    босса. Делает позиционку глубокой комбо/босс-механикой (фронт-танк меняется на
    лету). Позиционка off → инертно: flip_formation сам no-op без флага."""

    def __init__(self, *_):
        # Числовых параметров нет; *_ глотает (base,upgrade) ради единообразия фабрик.
        pass

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None:
            return
        flip = getattr(combat_manager, "flip_formation", None)
        if flip is not None:
            flip()


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