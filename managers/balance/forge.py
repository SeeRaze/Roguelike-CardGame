# managers/balance/forge.py
# СЕССИЯ 39, Шаг 39.1 — прокачка карт = движок кат.4 (см. _upgrade_design.md).
# Сим-слой ковки: моделирует экономику Forge Points (FP), уровни карт, босс-капы
# и предохранитель глубины триггеров. По образцу EconomyPolicy (economy.py):
# подключается в runner ОПЦИОНАЛЬНО (forge=None по умолчанию → регресс-нейтрально,
# baseline-гард остаётся зелёным; сухие цифры снимаются отдельным A/B).
#
# ВАЖНО (39.1): применяется ТОЛЬКО линейный слой (+δ за уровень = слой СТЕНЫ,
# кат.1). Условные теги (+mult/×mult = слой ПОТОЛКА, кат.4) — шаг 39.2.
#
# Детерминизм: модуль НЕ дёргает random → RNG-поток драфта/боя идентичен прогону
# без ковки при том же seed ⇒ чистый A/B (единственная разница — прокачанные карты).

from managers.balance.builds import _card_score, _card_themes, _deck_themes
from core.ForgeRegistry import pick_tag

# ─── РУЧКИ (гипотезы; калибруются в 39.3, затем в _balance_knobs.md) ──────────
# Экономика FP.
FORGE_POINTS_PER_COMBAT = 1     # FP за выжитый обычный бой (ручка скорости c)
FORGE_POINTS_PER_BOSS   = 3     # бонус FP за босса
# Линейный слой стены.
LINEAR_BONUS_PER_LEVEL  = 1     # δ: +N к числовым эффектам карты за уровень
# Растущая цена уровня ВНУТРИ тира: cost(level→level+1) = BASE + level·STEP.
# Тактический прессинг: добить карту до майлстоуна всё дороже (анти-degenerate).
LEVEL_COST_BASE = 1
LEVEL_COST_STEP = 1
# Кап уровня карты до первого босса (act 1). Ниже первого майлстоуна (5) →
# теги недоступны на ранних этажах (железная защита стены).
INITIAL_LEVEL_CAP = 4
# Босс-этаж → новый кап уровня карты (увязка шкал, _upgrade_design.md §3):
# босс-20 открывает майлстоун-5 (слот-1), 40 → 10 (слот-2), 60 → 15 (слот-3, ×mult).
BOSS_LEVEL_CAPS = {20: 5, 40: 10, 60: 15, 80: 20, 100: 25}
# Уровни-майлстоуны (открывают теговые слоты). Тир тега по майлстоуну
# (_upgrade_design.md §4): 5/10 → ранний (+mult), 15 → легендарный (×mult).
MILESTONES = (5, 10, 15)
MILESTONE_TIER = {5: "early", 10: "early", 15: "legendary"}

# ─── ПРЕДОХРАНИТЕЛЬ ГЛУБИНЫ ТРИГГЕРОВ (гард-рейл §10.2) ───────────────────────
# Жёсткий потолок вложенных триггеров (Эхо/детонации/каскады тегов) за одно
# действие — анти-∞-цикл и анти-переполнение чисел. В 39.1 — готовая утилита +
# константа; врезка в боевые триггер-пути — 39.2 (теги) / 39.5 (живой код).
MAX_TRIGGER_DEPTH = 5


class TriggerGuard:
    """Счётчик глубины каскада триггеров. enter() возвращает False, если потолок
    достигнут (цепочку надо оборвать). Использование:
        if guard.enter():
            try: ...каскадный эффект...
            finally: guard.exit()
    """

    def __init__(self, max_depth: int = MAX_TRIGGER_DEPTH):
        self.max_depth = max_depth
        self.depth = 0

    def enter(self) -> bool:
        if self.depth >= self.max_depth:
            return False
        self.depth += 1
        return True

    def exit(self) -> None:
        self.depth = max(0, self.depth - 1)


def apply_linear_level(card, delta: int) -> None:
    """Применить ОДИН линейный уровень к карте: +delta ко всем числовым эффектам
    (base_val/upgrade_val). Слой СТЕНЫ — строго линейный, БЕЗ множителей
    (_upgrade_design.md §10.3: компаунд заперт только в условных тегах)."""
    for e in card.effects:
        if hasattr(e, "base_val") and hasattr(e, "upgrade_val"):
            e.base_val    += delta
            e.upgrade_val += delta


def _ensure_state(player) -> None:
    """Лениво инициализировать ковочное состояние на игроке (как persistent_allies
    — живёт весь забег, НЕ сбрасывается reset_combat_statuses)."""
    if not hasattr(player, "deck_forge_state"):
        player.deck_forge_state = {}          # uid -> {"level": int, "slots": []}
        player.forge_points     = 0
        player.forge_level_cap  = INITIAL_LEVEL_CAP
        player._forge_uid_next  = 0


class ForgePolicy:
    """Политика ковки бота: копит FP за бои, на костре раз в акт тратит их на
    прокачку ЯДРА билда (концентрация), уважая текущий кап уровня. Состояние
    живёт на player (FP/уровни/кап) → один инстанс безопасно переиспользуется
    для обеих метрик (как EconomyPolicy). Без random → чистый A/B.

    В 39.1 ceiling-метрика включает ковку, wall — нет (forge=None) ⇒ ковка
    проявляется только в потолке (это и есть движок билда)."""

    def on_combat_won(self, player, floor: int, is_boss: bool = False) -> None:
        """Начислить FP за выжитый бой (+бонус за босса)."""
        _ensure_state(player)
        player.forge_points += FORGE_POINTS_PER_COMBAT
        if is_boss:
            player.forge_points += FORGE_POINTS_PER_BOSS

    def on_boss_defeated(self, player, floor: int) -> None:
        """Босс снимает кап уровня до следующего майлстоуна (увязка шкал §3)."""
        _ensure_state(player)
        new_cap = BOSS_LEVEL_CAPS.get(floor)
        if new_cap is not None and new_cap > player.forge_level_cap:
            player.forge_level_cap = new_cap

    def forge_between_acts(self, player, deck: list, class_name: str = "") -> None:
        """Раз в акт (на костре): тратить FP, прокачивая ЛУЧШУЮ доступную карту
        ядра на +1 уровень, пока хватает FP и не упёрлись в кап. Концентрация:
        всегда добираем сильнейшую карту, какую можем оплатить; растущая цена
        сама переключает на следующую, когда лидер дорожает."""
        _ensure_state(player)
        if player.forge_points <= 0 or not deck:
            return
        themes = _deck_themes(deck)
        cap = player.forge_level_cap

        # Кандидаты по убыванию ценности для билда (та же эвристика, что у драфта).
        def build_value(card) -> float:
            bonus = len(_card_themes(card) & themes)
            return _card_score(card) + bonus

        ranked = sorted(deck, key=build_value, reverse=True)

        progressed = True
        while progressed and player.forge_points > 0:
            progressed = False
            for card in ranked:
                rec = self._record(player, card)
                if rec["level"] >= cap:
                    continue
                cost = self._level_cost(rec["level"])
                if player.forge_points < cost:
                    continue
                player.forge_points -= cost
                rec["level"] += 1
                apply_linear_level(card, LINEAR_BONUS_PER_LEVEL)
                # Пересекли майлстоун (5/10/15)? Открыть теговый слот резонансным
                # классу тегом (Smart Weighting §10.1: «нужный тег всплыл в драфте
                # из 3, бот его взял» = детерминированный pick_tag). Ранний
                # майлстоун → +mult, легендарный (15) → ×mult.
                if rec["level"] in MILESTONE_TIER:
                    tier = MILESTONE_TIER[rec["level"]]
                    rec["slots"].append({"tag_id": pick_tag(class_name, tier)})
                progressed = True
                break       # переоценить с вершины (концентрация на лучшей)

    # ── внутреннее ───────────────────────────────────────────────────────────
    @staticmethod
    def _level_cost(level: int) -> int:
        """Цена +1 уровня при текущем уровне (растёт внутри тира)."""
        return LEVEL_COST_BASE + level * LEVEL_COST_STEP

    @staticmethod
    def _record(player, card) -> dict:
        """Запись ковки для карты (по уникальному uid инстанса). uid выдаётся
        лениво — паспорт инстанса в симе (зеркало будущего Card.uid в живой игре)."""
        if not hasattr(card, "_fuid"):
            card._fuid = player._forge_uid_next
            player._forge_uid_next += 1
        state = player.deck_forge_state
        if card._fuid not in state:
            state[card._fuid] = {"level": 0, "slots": []}
        return state[card._fuid]


# ─── ЗАКОН МИНИМАЛЬНОГО ТИРА НАГРАД (§10.5) ───────────────────────────────────
# Карта 0-го уровня из позднего драфта/Магазина = мусор против экспоненты врага.
# Награды на этаже F создаются уже пред-прокачанными до уровня акта (зеркало
# босс-капов §3): Акт 2 (этажи 21+) → базовый уровень 5 и т.д. Возвращает
# целевой уровень для карты, полученной на данном этаже.
def reward_level_for_floor(floor: int) -> int:
    """Минимальный уровень карты в награде на этаже `floor` (§10.5). Привязан к
    пройденным босс-гейтам: до первого босса — 0, после 20 → 5, 40 → 10, 60 → 15."""
    level = 0
    for boss_floor, milestone in sorted(BOSS_LEVEL_CAPS.items()):
        if floor > boss_floor:
            level = milestone
    return level
