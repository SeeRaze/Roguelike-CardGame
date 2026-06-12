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
        player.add_status("healthcheck", amount, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Вы получаете Хелсчек ({amount})."
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


class BarrierEffect:
    """Накладывает Барьер на игрока — несгораемый щит, не сбрасывается между ходами.
    Каждый стак барьера = +1 к щиту при СБРОСЕ в начале хода (см. CombatManager).
    Это движок кат.4 для Воина: «защита = атака» через Регрессионку."""
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
    """Карта-детонатор: подрывает Короткое замыкание на цели (ЗАМЫКАНИЕ-ПОЗВОНОЧНИК,
    core/DetonationRegistry.detonate). Со-присутствующий элемент задаёт вкус детонации.
    Инертно, если на цели нет заряда. Под предохранителем глубины (анти-каскад)."""

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None:
            return
        from core.DetonationRegistry import detonate
        guard = getattr(combat_manager, "_trigger_guard", None)
        if guard is not None and not guard.enter():
            combat_manager.add_log_message(
                "[ПРЕДОХРАНИТЕЛЬ] Детонация оборвана (глубина)."
            )
            return
        detonate(enemy, combat_manager)


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


class AoEStatusEffect:
    """Накладывает статус на ВСЕХ живых врагов (площадь). Для AoE-стихий (напр.
    «Разлив в опенспейсе» — Кофе по всем)."""
    def __init__(self, status_type, base_val, upgrade_val):
        self.status_type = status_type
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        val = self.upgrade_val if is_upgraded else self.base_val
        if self.status_type not in STATUSES:
            return
        if combat_manager is not None:
            targets = [e for e in getattr(combat_manager, "enemies", [enemy])
                       if e.hp > 0]
        else:
            targets = [enemy]
        for t in targets:
            t.add_status(self.status_type, val, combat_manager)
        if combat_manager:
            combat_manager.add_log_message(
                f" -> {self.status_type} {val} всем врагам."
            )


class DrawEffect:
    """Игрок добирает N карт (топливо/синергия Утечки). Тихо инертен без боя."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        n = self.upgrade_val if is_upgraded else self.base_val
        if combat_manager is not None and hasattr(combat_manager, "deck_manager"):
            drew = combat_manager.deck_manager.draw_cards(n)
            combat_manager.add_log_message(f" -> Добор {drew} карт(ы).")


class DecompEffect:
    """Накладывает Декомпиляцию на врага: глушит генерацию щита N ходов (gain_shield-
    гейт, см. Creature) + СРАЗУ −50% текущего щита. «Окно эксплойта»: пока висит —
    реакции по цели бьют сильнее (см. реакц.слой)."""
    def __init__(self, base_turns, upgrade_turns):
        self.base_turns = base_turns
        self.upgrade_turns = upgrade_turns

    def execute(self, player, enemy, combat_manager, is_upgraded):
        turns = self.upgrade_turns if is_upgraded else self.base_turns
        enemy.add_status("decomp", turns, combat_manager)
        if enemy.shield > 0:
            enemy.shield = enemy.shield // 2
        if combat_manager:
            combat_manager.add_log_message(
                f" -> Декомпиляция {turns} х.: генерация щита заглушена, "
                f"текущий щит −50%."
            )


class EnergyEffect:
    """+N энергии в этот ход (рамп/бурст). Карта «Перерыв» (Кофе-брейк). Кап источника
    здесь (карта даёт фикс N); player.gain_energy допускает временный выход за max."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        n = self.upgrade_val if is_upgraded else self.base_val
        if hasattr(player, "gain_energy"):
            player.gain_energy(n)
            if combat_manager:
                combat_manager.add_log_message(f" -> +{n} энергии в этот ход.")


class DiscardRedrawEffect:
    """«Переключить окно» (Alt+Tab): сбросить руку, добрать столько же (КАЧЕСТВО —
    перетасовать неподходящее). Карта-носитель ещё в руке (изымётся cardplay после),
    поэтому её ИСКЛЮЧАЕМ из сброса/счёта."""
    def __init__(self, *_):
        pass

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None or not hasattr(combat_manager, "deck_manager"):
            return
        dm = combat_manager.deck_manager
        playing = getattr(combat_manager, "_card_being_played", None)
        others = [c for c in dm.hand if c is not playing]
        n = len(others)
        dm.discard_pile.extend(others)
        dm.hand[:] = [c for c in dm.hand if c is playing]
        dm.draw_cards(n)
        if combat_manager:
            combat_manager.add_log_message(f" -> Сброс руки, добор {n} карт(ы).")


class ExileFromHandEffect:
    """«Удалить безвозвратно» (Shift+Delete): изгнать карту из руки — DEBUG-инструмент
    слоя багов (прореживание). Без UI-выбора берёт первую НЕ-себя карту (в игре выбор =
    UI-слой). Сама карта exile=True (не возвращается в круговорот боя)."""
    def __init__(self, *_):
        pass

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None or not hasattr(combat_manager, "deck_manager"):
            return
        dm = combat_manager.deck_manager
        playing = getattr(combat_manager, "_card_being_played", None)
        victim = next((c for c in dm.hand if c is not playing), None)
        if victim is not None:
            dm.hand.remove(victim)
            dm.exile_pile.append(victim)
            if combat_manager:
                combat_manager.add_log_message(
                    f" -> {victim.name} удалена безвозвратно (изгнана)."
                )


class ScryEffect:
    """«Просмотр стека» (Stack Trace): заглянуть в верх колоды (ИНФО/консистентность).
    Без UI-выбора авто-фильтрует: самую ДОРОГУЮ из верхних N карт — в сброс (прочистка к
    играбельному). Полноценный выбор «любые в сброс» — UI-слой (G2)."""
    def __init__(self, base_val, upgrade_val):
        self.base_val = base_val
        self.upgrade_val = upgrade_val

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None or not hasattr(combat_manager, "deck_manager"):
            return
        n = self.upgrade_val if is_upgraded else self.base_val
        dm = combat_manager.deck_manager
        top = dm.draw_pile[-n:] if dm.draw_pile else []
        if top:
            worst = max(top, key=lambda c: getattr(c, "cost", 0))
            dm.draw_pile.remove(worst)
            dm.discard_pile.append(worst)
            if combat_manager:
                combat_manager.add_log_message(
                    f" -> Просмотр стека: {worst.name} отправлена в сброс."
                )


class UndoEffect:
    """«Отменить» (Ctrl+Z) — РЕТРОАКТИВ: вернуть последнюю сыгранную карту из сброса в
    руку (переиграть). Берёт верх discard (на момент розыгрыша = ПРЕДЫДУЩАЯ карта).

    Пропускает карты-Отмены в сбросе: иначе две «Отменить» в руке возвращали бы друг
    друга бесконечно (cost 0 → энергия не ограничивает → вечный ход / софт-лок)."""
    def __init__(self, *_):
        pass

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None or not hasattr(combat_manager, "deck_manager"):
            return
        dm = combat_manager.deck_manager
        # Ищем сверху первую НЕ-Undo карту (сами Отмены не воскрешаем).
        for i in range(len(dm.discard_pile) - 1, -1, -1):
            cand = dm.discard_pile[i]
            if any(isinstance(e, UndoEffect) for e in cand.effects):
                continue
            dm.discard_pile.pop(i)
            dm.hand.append(cand)
            combat_manager.add_log_message(
                f" -> Отменить: {cand.name} возвращена в руку."
            )
            return


class CopyEffect:
    """«Копировать» (Ctrl+C) — сохранить ПОСЛЕДНЮЮ сыгранную карту в Буфер (ПЕРЕЗАТИРАЕТ
    прошлый). Буфер живёт между ходами. Источник = верх discard (предыдущая карта).

    Не копирует «Вставить»: Буфер, читающий сам себя, — бесконечная рекурсия перефайра."""
    def __init__(self, *_):
        pass

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None or not hasattr(combat_manager, "deck_manager"):
            return
        dm = combat_manager.deck_manager
        if dm.discard_pile and not any(
            isinstance(e, PasteEffect) for e in dm.discard_pile[-1].effects
        ):
            combat_manager._clipboard = dm.discard_pile[-1]
            combat_manager.add_log_message(
                f" -> Копировать: {dm.discard_pile[-1].name} → Буфер."
            )


class PasteEffect:
    """«Вставить» (Ctrl+V) — заново исполнить содержимое Буфера. НЕ очищает (перефайр-
    движок; тормоз = энергия за Ctrl+V + единственный слот).

    Пропускает вложенные PasteEffect — иначе Буфер с «Вставить» рекурсил бы бесконечно
    (страховка на случай, если Paste попал в Буфер в обход CopyEffect-фильтра)."""
    def __init__(self, *_):
        pass

    def execute(self, player, enemy, combat_manager, is_upgraded):
        if combat_manager is None:
            return
        card = getattr(combat_manager, "_clipboard", None)
        if card is not None:
            combat_manager.add_log_message(f" -> Вставить: перефайр {card.name}.")
            for eff in getattr(card, "effects", []):
                if isinstance(eff, PasteEffect):
                    continue
                eff.execute(player, enemy, combat_manager, getattr(card, "upgraded", False))


class Card:
    def __init__(self, name, cost, card_type, description, effects,
                 rarity=Rarity.COMMON, exile=False, card_class=None,
                 unplayable=False):
        self.name = name
        self.cost = cost
        self.card_type = card_type
        self.description = description
        self.effects = effects
        self.rarity = rarity
        self.upgraded = False
        self.exile = exile
        # Принадлежность классу: None = нейтральная (generic), иначе имя класса
        # (напр. "Warrior"). Проставляется централизованно в core/cards/catalog.py.
        self.card_class = card_class
        # Слой БАГОВ (ярус 1): несыгрываемая карта-долг (модель StS Wound). Занимает
        # слот руки, дилютит добор, но play_card_by_index её НЕ разыгрывает. Counterplay —
        # DEBUG-эффект (карта «Код-ревью»), не энергия. Персист в gm.current_deck.
        self.unplayable = unplayable

    def upgrade(self):
        if not self.upgraded:
            self.upgraded = True
            self.name += "+"

    def apply(self, player, enemy, combat_manager=None):
        for effect in self.effects:
            effect.execute(player, enemy, combat_manager, self.upgraded)