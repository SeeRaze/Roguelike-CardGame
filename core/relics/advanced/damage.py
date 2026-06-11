# core/relics/advanced/damage.py
# Реликвии темы «урон и ослабление врага».
from core.relics.base import Relic
from core.rarity import Rarity


class ПроклятаяКорона(Relic):
    def __init__(self):
        super().__init__(
            "Проклятая Корона",
            "Урон атаками x2. Цена удаления карт x2. Золото из наград исчезает.",
            Rarity.LEGENDARY,
        )

    def on_damage_calculated(self, base_dmg, is_player_attack=True, dry_run=False):
        if is_player_attack:
            return base_dmg * 2
        return base_dmg


class УтреннийСозвон(Relic):
    """Первая атака в каждом бою наносит +3 урона (разовый заряд на бой)."""

    def __init__(self):
        super().__init__(
            "Утренний созвон",
            "Раскачались на стендапе: первая атака в каждом бою наносит +3 урона.",
            Rarity.COMMON,
        )
        self._used_this_combat = False

    def on_combat_start(self, combat_manager):
        self._used_this_combat = False

    def on_damage_calculated(self, base_dmg, is_player_attack=True, dry_run=False):
        if is_player_attack and not self._used_this_combat:
            # В превью (dry_run) показываем бонус, но НЕ расходуем одноразовый заряд.
            if not dry_run:
                self._used_this_combat = True
            return base_dmg + 3
        return base_dmg


class СвинцовыйНабалдашник(Relic):
    """Первая атака в ходу гарантированно накладывает Слабость 1."""

    def __init__(self):
        super().__init__(
            "Свинцовый Набалдашник",
            "Первая атака в каждом ходу накладывает Слабость 1 на врага.",
            Rarity.UNCOMMON,
        )
        self._used_this_turn = False

    def on_card_played(self, card, combat_manager):
        if self._used_this_turn:
            return
        if card.card_type == "attack":
            # Цель — ЖИВОЙ враг (в групповом бою enemies[0] может быть трупом).
            target = combat_manager.get_target_enemy()
            if target is None:
                return
            target.add_status("weak", 1, combat_manager)
            self._used_this_turn = True
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': Слабость 1 на врага!"
            )

    def on_turn_start(self, combat_manager):
        self._used_this_turn = False


class ТрофейныйКлык(Relic):
    """При убийстве врага: +1 Сила до конца боя."""

    def __init__(self):
        super().__init__(
            "Трофейный Клык",
            "Каждый раз, когда вы убиваете врага,\nполучаете +1 Силы до конца боя.",
            Rarity.UNCOMMON,
        )

    def on_kill(self, enemy, combat_manager):
        combat_manager.player.strength += 1
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': +1 Сила (текущая: {combat_manager.player.strength})!"
        )


class БагРепорт(Relic):
    """В начале боя враг получает Уязвимость 1 (получаемый урон ×1.5)."""

    def __init__(self):
        super().__init__(
            "Баг-репорт",
            "Завели тикет на врага: в начале каждого боя он получает Уязвимость 1.",
            Rarity.COMMON,
        )

    def on_combat_start(self, combat_manager):
        combat_manager.enemy.add_status("vulnerable", 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': Уязвимость 1 на врага!"
        )


class ЛидЗаСпиной(Relic):
    """В начале боя игрок получает Ярость 1 (+1 к урону всех атак в этом бою).

    Ярость сбрасывается между боями (reset_combat_statuses) — флэт-бонус на бой,
    без компаунда."""

    def __init__(self):
        super().__init__(
            "Лид за спиной",
            "Лид стоит над душой: в начале каждого боя получаете Ярость 1.",
            Rarity.COMMON,
        )

    def on_combat_start(self, combat_manager):
        combat_manager.player.add_status("strength", 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': Ярость 1!"
        )


class БерсеркМедальон(Relic):
    """При убийстве врага: +1 Энергия."""

    def __init__(self):
        super().__init__(
            "Берсерк-Медальон",
            "Каждый раз, когда вы убиваете врага,\nвосстанавливаете +1 Энергию.",
            Rarity.RARE,
        )

    def on_kill(self, enemy, combat_manager):
        combat_manager.player.energy += 1
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': +1 Энергия!"
        )


class ТехническийДолг(Relic):
    """Классовый КАТ.4-компаунд Берсерка (резонанс: выпадает только ему). Каждое
    ДОБИВАНИЕ врага в HP-долге → +1 стак НАВСЕГДА (весь забег, переносится между боями).
    Каждый стак = +PER_STACK ко всему урону игрока. Растёт с числом киллов-в-долге И
    персистентен → закрывает дефицит кат.4 ([[scaling-audit]]: у игрока не было компаунда,
    который растёт И переносится). Малый % + низкий тир = «слоу-берн» под ДЛИННЫЙ забег
    (дольше = сильнее), не бурст; без капа — крошечный per-stack не ломает иерархию тиров.
    Тематика: проценты по долгу капают в твою пользу, пока платишь кровью."""

    PER_STACK = 0.01   # +1% урона за стак (ручка калибровки; малый → можно без капа)

    def __init__(self):
        super().__init__(
            "Технический Долг",
            "Добили врага в HP-долге → +1% ко всему урону НАВСЕГДА (растёт весь забег).",
            Rarity.UNCOMMON,
            relic_class="Berserker",
        )
        self.stacks = 0

    def on_combat_start(self, combat_manager):
        # Стаки НЕ сбрасываются (кат.4-перенос по забегу) — намеренно без сброса здесь.
        pass

    def on_kill(self, enemy, combat_manager):
        # Гейт «в долге»: награда именно за долговой плейстайл (hp<0 в момент килла).
        if combat_manager.player.hp < 0:
            self.stacks += 1
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': долг капает → +1% урона "
                f"(стаков: {self.stacks})."
            )

    def on_damage_calculated(self, base_dmg, is_player_attack=True, dry_run=False):
        if is_player_attack and self.stacks:
            return int(base_dmg * (1 + self.stacks * self.PER_STACK))
        return base_dmg
