# core/relics/advanced/epic_legendary.py
# Высокотировый контент — мощные ВНУТРИБОЕВЫЕ движки (EPIC) и «Проклятые
# Артефакты»-джокеры (LEGENDARY: меняют правила игры ценой трейдоффа).
# Все — на ДОЛГОЖИВУЩИХ примитивах (echo/barrier/щит/×урон/изгнание карт), без
# привязки к конкретным классам (классы переписывают — см. [[class-redesign-incoming]]).
import random

from core.relics.base import Relic
from core.rarity import Rarity


class Автоматизация(Relic):
    """В начале каждого хода игрок получает Эхо 1 (следующая разыгранная карта
    срабатывает повторно). Универсальный ретриггер-движок: удваивает первую карту
    каждого хода независимо от класса/архетипа. Эхо — внутрибоевой статус
    (сбрасывается между боями), поэтому это движок ТЕМПА, а не компаунда по забегу."""

    def __init__(self):
        super().__init__(
            "Автоматизация",
            "Автоматизация рутины: в начале каждого хода вы получаете Эхо 1 —\n"
            "следующая сыгранная карта срабатывает дважды.",
            Rarity.EPIC,
        )

    def on_turn_start(self, combat_manager):
        combat_manager.player.add_status("echo", 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': Эхо 1 — следующая карта сработает дважды!"
        )


class Аутсорс(Relic):
    """Каждый раз, когда игрок получает щит, половина этого щита дублируется в
    Барьер (несгораемый — не сбрасывается в начале хода). Оборонный движок:
    обычный щит сгорает каждый ход, а Барьер копится → стена растёт от любой
    карты защиты. Половина (а не весь) — чтобы не превращать каждый блок в
    перманент мгновенно (баланс оборонного компаунда)."""

    # Доля полученного щита, уходящая в несгораемый Барьер.
    BARRIER_FRACTION = 0.5

    def __init__(self):
        super().__init__(
            "Аутсорс",
            "Половина полученного щита уходит в Аутсорс — несгораемый Барьер\n"
            "(не сбрасывается между ходами).",
            Rarity.EPIC,
        )

    def on_shield_gained(self, amount, creature, combat_manager=None):
        if combat_manager is None or creature is not combat_manager.player:
            return
        bonus = int(amount * self.BARRIER_FRACTION)
        if bonus <= 0:
            return
        # add_status("barrier") НЕ дёргает gain_shield → без рекурсии on_shield_gained.
        creature.add_status("barrier", bonus, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': +{bonus} Барьера (несгораемый)!"
        )


class ДеплойВПятницу(Relic):
    """LEGENDARY-джокер. Все атаки наносят ×DAMAGE_MULT урона, но при розыгрыше
    ЛЮБОЙ карты с шансом BURN_CHANCE она сгорает из колоды НАВСЕГДА (до конца
    забега). «Машина смерти, у которой кончаются патроны» — огромный множитель
    урона ценой истончения колоды (риск остаться без карт на поздних этажах).

    Реализация: ×урон через on_damage_calculated (как Марш смерти, считается
    и в превью); сжигание — удаление сыгранной карты из мастер-колоды
    `gm.current_deck` (тот же объект, что в руке) в on_card_played. Карта успевает
    отыграть текущий розыгрыш (хук — ДО discard), исчезает со следующего боя."""

    DAMAGE_MULT = 3
    BURN_CHANCE = 0.10

    def __init__(self):
        super().__init__(
            "Деплой в пятницу",
            "Атаки наносят тройной урон.\n"
            "Но каждая сыгранная карта с шансом 10% сгорает из колоды навсегда.",
            Rarity.LEGENDARY,
        )

    def on_damage_calculated(self, base_dmg, is_player_attack=True, dry_run=False):
        if is_player_attack:
            return base_dmg * self.DAMAGE_MULT
        return base_dmg

    def on_card_played(self, card, combat_manager):
        if random.random() >= self.BURN_CHANCE:
            return
        gm = getattr(combat_manager, 'gm', None)
        deck = getattr(gm, 'current_deck', None) if gm else None
        if deck is not None and card in deck:
            deck.remove(card)
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': карта '{card.name}' сгорела НАВСЕГДА!"
            )


class ТочкаОтказа(Relic):
    """LEGENDARY-джокер. Твой максимальный запас HP падает до 1 — но весь
    полученный за ход щит превращается в несгораемый Барьер, а Оптимизация растёт от
    накопленного Барьера. «Идеальный симулятор выживания под глухой стеной»:
    любой неотражённый удар убивает (1 HP), поэтому надо выблокировать всё —
    а накопленная оборона конвертируется в атаку.

    Реализация на долгоживущих примитивах: on_combat_start сажает max_hp=1;
    on_turn_end (новый хук, ДО удара врага) банкует текущий щит в Барьер
    (несгораемый — переносится через start_turn_phase: shield=carry+barrier) и
    выставляет Силу = Барьер//SHIELD_TO_RAGE. Вклад в Силу отслеживается
    инкрементально (self._granted_rage), чтобы не затирать Силу из других
    источников (Лид за спиной и т.п.)."""

    # Сколько Барьера даёт +1 к Силе.
    SHIELD_TO_RAGE = 10

    def __init__(self):
        super().__init__(
            "Точка отказа",
            "Макс. HP падает до 1.\n"
            "Весь полученный за ход щит становится несгораемым Барьером,\n"
            "а Оптимизация растёт от накопленного Барьера (Барьер ÷ 10).",
            Rarity.LEGENDARY,
        )
        # Сколько Силы уже выдано этой реликвией в текущем бою (для инкремента).
        self._granted_rage = 0

    def on_combat_start(self, combat_manager):
        player = combat_manager.player
        player.max_hp = 1
        player.hp = 1
        self._granted_rage = 0
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': макс. HP = 1. Выживание на одном Барьере!"
        )

    def on_turn_end(self, combat_manager):
        player = combat_manager.player
        # Банкуем щит, накопленный за ход, в несгораемый Барьер.
        if player.shield > 0:
            player.barrier += player.shield
        # Оптимизация = Барьер//K; обновляем ТОЛЬКО свой вклад (не затирая чужую).
        target_rage = player.barrier // self.SHIELD_TO_RAGE
        player.optimize += target_rage - self._granted_rage
        self._granted_rage = target_rage
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': Барьер {player.barrier}, Оптимизация +{target_rage}."
        )
