# core/relics/advanced/synergy.py
# СИНЕРГИЯ-РЕЛИКВИИ (Блок 3, С65) — усиливают углублённый стихийный пул (Блок 2:
# комбо/детонации/spread). Закрывают дыру recon'а: новые стихии (shortcircuit/leak/
# decomp) почти без поддержки реликвий (хуки были только у legacy/coffee).
#
# Все на СУЩЕСТВУЮЩИХ хуках — без новых реактивных (решение дизайна). Детонационные
# движки не АМПЛИФИЦИРУЮТ детонацию (она идёт мимо EffectCalculator), а ПОДАЮТ заряды:
# авто-детонация на пороге SHORTCIRCUIT_THRESHOLD уже есть в end_turn_phase.
# Числа = ЗАГЛУШКИ (баланс-капстоун калибрует). Все LOCKED (награда за прогресс).
import random

from core.relics.base import Relic
from core.rarity import Rarity
from core.StatusRegistry import ELEMENT_KEYS


# ── COMMON: стихия-энейблеры (зеркало Кофемашины) ────────────────────────────
class ТестовыйСервер(Relic):
    """В начале боя случайный живой враг получает Короткое замыкание 2 — детонатор
    взведён с порога. Ранний энейблер детонационных сборок."""

    def __init__(self):
        super().__init__(
            "Тестовый сервер",
            "В начале каждого боя случайный враг получает Короткое замыкание 2.",
            Rarity.COMMON,
        )

    def on_combat_start(self, combat_manager):
        living = [e for e in combat_manager.enemies if e.hp > 0]
        if not living:
            return
        target = random.choice(living)
        target.add_status("shortcircuit", 2, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': {target.name} — Короткое замыкание 2!"
        )


class ДежурныйПейджер(Relic):
    """В начале боя случайный живой враг получает Утечку памяти 2 — энейблер leak-
    сборок (урон при доборе карт)."""

    def __init__(self):
        super().__init__(
            "Дежурный пейджер",
            "В начале каждого боя случайный враг получает Утечку памяти 2.",
            Rarity.COMMON,
        )

    def on_combat_start(self, combat_manager):
        living = [e for e in combat_manager.enemies if e.hp > 0]
        if not living:
            return
        target = random.choice(living)
        target.add_status("leak", 2, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': {target.name} — Утечка памяти 2!"
        )


# ── UNCOMMON: условная синергия ──────────────────────────────────────────────
class ДашбордМетрик(Relic):
    """В начале хода +SHIELD_PER_ELEMENT Щита за каждую РАЗНУЮ стихию на цели.
    Оборонное зеркало «размазывания» — награда за диверсифицированную доску."""

    SHIELD_PER_ELEMENT = 2

    def __init__(self):
        super().__init__(
            "Дашборд метрик",
            "В начале хода +2 Щита за каждую разную стихию на цели.",
            Rarity.UNCOMMON,
        )

    def on_turn_start(self, combat_manager):
        target = combat_manager.get_target_enemy()
        if target is None:
            return
        count = sum(1 for k in ELEMENT_KEYS if target.get_status(k) > 0)
        if count > 0:
            amount = count * self.SHIELD_PER_ELEMENT
            combat_manager.player.gain_shield(amount, combat_manager)
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': {count} стихи(й) → +{amount} Щита."
            )


class ХотфиксСкрипт(Relic):
    """Сыграл карту: если на цели ОДНОВРЕМЕННО Кофе и Legacy (пара ХОТФИКСа взведена)
    — добор 1. Награда за выстроенное комбо (картдвижение под темп)."""

    def __init__(self):
        super().__init__(
            "Хотфикс-скрипт",
            "Когда вы играете карту: если на цели и Разлитый кофе, и Legacy-код —\n"
            "добор 1 карты.",
            Rarity.UNCOMMON,
        )

    def on_card_played(self, card, combat_manager):
        target = combat_manager.get_target_enemy()
        if target is None:
            return
        if target.get_status("coffee") > 0 and target.get_status("legacy") > 0:
            combat_manager.deck_manager.draw_cards(1)
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': пара ХОТФИКСа на цели → добор 1."
            )


# ── RARE: движки / билд-дефайнеры ────────────────────────────────────────────
class Пайплайн(Relic):
    """«CI/CD пайплайн». В начале хода первый враг получает +1 Короткое замыкание.
    Пассивный детонатор-движок: сам набивает порог → авто-детонация в фазе врага.
    Делает детонационную сборку самоподдерживающейся (без хука детонации — подаём
    заряд)."""

    def __init__(self):
        super().__init__(
            "CI/CD пайплайн",
            "В начале каждого хода цель получает +1 Короткое замыкание\n"
            "(само набьёт порог детонации).",
            Rarity.RARE,
        )

    def on_turn_start(self, combat_manager):
        target = combat_manager.get_target_enemy()
        if target is None:
            return
        target.add_status("shortcircuit", 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': +1 Короткое замыкание цели."
        )


class РаннерТестов(Relic):
    """Каждая CADENCE-я сыгранная за бой карта → первый враг получает Legacy-код 3.
    DoT-движок от темпа розыгрыша (компаундит с Дебаггером: +2 урона/тик)."""

    CADENCE = 3

    def __init__(self):
        super().__init__(
            "Раннер тестов",
            "Каждая 3-я сыгранная за бой карта накладывает на цель Legacy-код 3.",
            Rarity.RARE,
        )
        self._count = 0

    def on_combat_start(self, combat_manager):
        self._count = 0

    def on_card_played(self, card, combat_manager):
        self._count += 1
        if self._count % self.CADENCE != 0:
            return
        target = combat_manager.get_target_enemy()
        if target is None:
            return
        target.add_status("legacy", 3, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': прогон тестов → Legacy-код 3 цели."
        )


class ГрантНаРефакторинг(Relic):
    """Каждый побеждённый босс: +FP_PER_BOSS очков ковки (forge points). Кормит
    FP-ось (глубина оффенса / ceiling-движок прокачки карт) — единственная реликвия-
    источник FP. По забегу 5 боссов = +N×5 FP."""

    FP_PER_BOSS = 4

    def __init__(self):
        super().__init__(
            "Грант на рефакторинг",
            "Каждый побеждённый босс приносит +4 очка ковки (FP).",
            Rarity.RARE,
        )

    def on_boss_defeated(self, player, combat_manager=None):
        player.forge_points = getattr(player, "forge_points", 0) + self.FP_PER_BOSS
        if combat_manager:
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': +{self.FP_PER_BOSS} FP "
                f"(всего {player.forge_points})."
            )


# ── EPIC: масштабные стихийные движки ────────────────────────────────────────
class Микросервисы(Relic):
    """В начале хода на первого врага накладывается по +1 стаку ELEMENTS_PER_TURN
    СЛУЧАЙНЫХ РАЗНЫХ стихий. Массовый spread-движок: кормит комбо/детонации/
    Технический регресс непредсказуемо (хаос/дофамин). Без повтора стихий в ходу."""

    ELEMENTS_PER_TURN = 3

    def __init__(self):
        super().__init__(
            "Микросервисы",
            "В начале каждого хода цель получает по 1 стаку 3 случайных стихий.",
            Rarity.EPIC,
        )

    def on_turn_start(self, combat_manager):
        target = combat_manager.get_target_enemy()
        if target is None:
            return
        picks = random.sample(ELEMENT_KEYS, self.ELEMENTS_PER_TURN)
        for elem in picks:
            target.add_status(elem, 1, combat_manager)
        combat_manager.add_log_message(
            f"[Реликвия] '{self.name}': spread ({', '.join(picks)}) на цель."
        )


class ЗелёныйБилд(Relic):
    """В начале хода: если на цели THRESHOLD+ РАЗНЫХ стихий — игрок получает Эхо 1 +
    добор 1. Payoff-движок выстроенной стихийной доски (темп+карты, когда билд
    собран). Награда за диверсификацию."""

    THRESHOLD = 3

    def __init__(self):
        super().__init__(
            "Зелёный билд",
            "В начале хода, если на цели 3+ разных стихий: вы получаете Эхо 1\n"
            "и добираете 1 карту.",
            Rarity.EPIC,
        )

    def on_turn_start(self, combat_manager):
        target = combat_manager.get_target_enemy()
        if target is None:
            return
        count = sum(1 for k in ELEMENT_KEYS if target.get_status(k) > 0)
        if count >= self.THRESHOLD:
            combat_manager.player.add_status("echo", 1, combat_manager)
            combat_manager.deck_manager.draw_cards(1)
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': билд зелёный ({count} стихий) → "
                f"Эхо 1 + добор 1!"
            )


# ── LEGENDARY: правило-ломатель с трейдоффом ─────────────────────────────────
class ЗероДаунтайм(Relic):
    """LEGENDARY-джокер. В начале хода КАЖДАЯ уже наложенная стихия на КАЖДОМ враге
    растёт на +1 стак (снежный ком техдолга по полю → экспоненциальная доска).
    Трейдофф: в конце хода игрок получает урон = числу РАЗНЫХ типов стихий на поле
    (нестабильность бьёт по тебе; макс 6/ход). Любой посев стихии → самоусиливающийся
    движок ценой растущего самоурона. Растит и shortcircuit (→ детонации), и decomp
    (окно)."""

    def __init__(self):
        super().__init__(
            "Зеро-даунтайм",
            "В начале хода все наложенные стихии на всех врагах +1 стак.\n"
            "Но в конце хода вы получаете урон = числу разных типов стихий на поле.",
            Rarity.LEGENDARY,
        )

    def on_turn_start(self, combat_manager):
        grew = False
        for e in combat_manager.enemies:
            if e.hp <= 0:
                continue
            for k in ELEMENT_KEYS:
                cur = e.get_status(k)
                if cur > 0:
                    e.set_status(k, cur + 1)
                    grew = True
        if grew:
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': снежный ком — все стихии +1."
            )

    def on_turn_end(self, combat_manager):
        types = set()
        for e in combat_manager.enemies:
            if e.hp <= 0:
                continue
            for k in ELEMENT_KEYS:
                if e.get_status(k) > 0:
                    types.add(k)
        dmg = len(types)
        if dmg > 0:
            combat_manager.player.take_damage(
                dmg, attacker=None, combat_manager=combat_manager
            )
            combat_manager.add_log_message(
                f"[Реликвия] '{self.name}': нестабильность — {dmg} урона себе "
                f"({dmg} типов стихий)."
            )
