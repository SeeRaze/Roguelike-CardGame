# managers/balance/forge.py
# СИМ-СЛОЙ ковки карт (Сессия 39). БОТ-ПОЛИТИКА поверх движка прокачки: как
# headless-бот тратит FP (концентрация ковки / Закалка / Заточка по «гонке кривых»).
#
# ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ экономики/уровней/математики — core/forge.py (С39.5):
# константы, цена уровня, приток FP, босс-капы, линейный слой, Закалка/Заточка,
# Гипер-заряд, TriggerGuard. Здесь — ТОЛЬКО то, что специфично симу (бот-решения,
# ленивая инициализация sim-игрока, эвристика ценности билда). Имена ре-экспортятся
# из core для тестов и внешних sim-модулей (events/sweep).
#
# Изменяемые свипом ручки (TEMPER_*/ARTIFACT_*) живут в core.forge и мутируются
# ИМЕННО там (sweep пишет в core.forge); бот читает их через `_cf.<ИМЯ>` в
# рантайме, поэтому свип влияет на поведение без рассинхрона копий.
#
# Детерминизм: модуль НЕ дёргает random → RNG-поток драфта/боя идентичен прогону
# без ковки при том же seed ⇒ чистый A/B (единственная разница — прокачанные карты).

from managers.balance.builds import _card_score, _card_themes, _deck_themes
from managers.MapGenerator import FLOORS_PER_ACT
from core.ForgeRegistry import pick_tag
from core import forge as _cf
# Ре-экспорт чистого слоя из core (источник правды) для тестов/внешних модулей.
from core.forge import (
    TriggerGuard, apply_linear_level, fp_per_combat, combat_fp_gain,
    level_cost, invested_fp, card_forge_channel, card_is_defensive,
    reward_level_for_floor, next_cap_for_boss, milestone_tier, is_overcharge_level,
    overcharge_slot, sharpen as _core_sharpen,
    FORGE_POINTS_PER_ACT, FORGE_POINTS_PER_BOSS, LINEAR_BONUS_PER_LEVEL,
    LEVEL_COST_BASE, LEVEL_COST_STEP, INITIAL_LEVEL_CAP, BOSS_LEVEL_CAPS,
    MILESTONES, MILESTONE_STEP, MILESTONE_TIER, OVERCHARGE_FROM_LEVEL,
    TEMPER_HP_PCT, TEMPER_GOLD_COST, TEMPER_PROACTIVE_RATIO, INCOMING_FIGHT_TURNS,
    SHARPEN_FP_COST, SHARPEN_ATK_PCT, ARTIFACT_FP_MULT, ARTIFACT_MAX_HP_ADD,
    MAX_TRIGGER_DEPTH,
)

# Алиас под старое имя теста (managers.balance — внутреннее API сима).
_card_is_defensive = card_is_defensive

# Публичный API модуля: бот-политика + ре-экспорт чистого слоя из core (источник
# правды). Перечисление гасит F401 на ре-экспортах и документирует поверхность.
__all__ = [
    "ForgePolicy", "deck_prefers_sharpen", "incoming_next_act", "_ensure_state",
    "_card_is_defensive",
    "TriggerGuard", "apply_linear_level", "fp_per_combat", "combat_fp_gain",
    "level_cost", "invested_fp", "card_forge_channel", "card_is_defensive",
    "reward_level_for_floor", "next_cap_for_boss", "milestone_tier",
    "is_overcharge_level", "overcharge_slot",
    "FORGE_POINTS_PER_ACT", "FORGE_POINTS_PER_BOSS", "LINEAR_BONUS_PER_LEVEL",
    "LEVEL_COST_BASE", "LEVEL_COST_STEP", "INITIAL_LEVEL_CAP", "BOSS_LEVEL_CAPS",
    "MILESTONES", "MILESTONE_STEP", "MILESTONE_TIER", "OVERCHARGE_FROM_LEVEL",
    "TEMPER_HP_PCT", "TEMPER_GOLD_COST", "TEMPER_PROACTIVE_RATIO",
    "INCOMING_FIGHT_TURNS", "SHARPEN_FP_COST", "SHARPEN_ATK_PCT",
    "ARTIFACT_FP_MULT", "ARTIFACT_MAX_HP_ADD", "MAX_TRIGGER_DEPTH",
]


def incoming_next_act(floor: int) -> int:
    """Оценка входящего урона за ход в СЛЕДУЮЩЕМ акте (для решений на костре/в
    магазине о стоке выживаемости). Грубое зеркало EnemySpawner: пиковый этаж
    следующего акта × формула урона, с поправкой на группы. «Угроза ваншота».

    Модульная функция (С57): переиспользуется ForgePolicy (Заточка) и
    EconomyPolicy (Закалка на золоте) — общий порог «гонки кривых» без
    перекрёстной зависимости политик."""
    from managers.EnemySpawner import (
        DMG_BASE, DMG_GROWTH, GROUP_3_FROM, GROUP_DMG_MULT,
    )
    next_act_peak = ((floor // FLOORS_PER_ACT) + 1) * FLOORS_PER_ACT
    per_enemy = DMG_BASE * (DMG_GROWTH ** next_act_peak)
    # На поздних этажах враги ходят группами по 3 — суммарный залп за ход.
    if next_act_peak >= GROUP_3_FROM:
        per_turn = per_enemy * GROUP_DMG_MULT[3] * 3
    else:
        per_turn = per_enemy
    # Урон-за-ход → давление боя (накопленный урон за репрезентативный клир).
    return int(per_turn * INCOMING_FIGHT_TURNS)


def deck_prefers_sharpen(deck) -> bool:
    """ТЕМА-ГЕЙТ Заточки (С39.4): офенс-ориентированная колода точит урон
    (Заточка), оборонная копит Max HP (Закалка). Считаем КАРТЫ (не уникальные
    темы — устойчивее к шуму): чисто оборонных меньше прочих ⇒ офенс ⇒ Заточка."""
    if not deck:
        return False
    defensive = sum(1 for c in deck if card_is_defensive(c))
    return (len(deck) - defensive) > defensive


def _ensure_state(player) -> None:
    """Лениво инициализировать ковочное состояние на SIM-игроке (FakePlayer без
    __init__). В живой игре те же поля ставит Player.__init__. Поля живут весь
    забег, НЕ сбрасываются reset_combat_statuses (как persistent_allies)."""
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

    Ceiling-метрика включает ковку, wall — нет (forge=None) ⇒ ковка проявляется
    только в потолке (это и есть движок билда)."""

    def on_combat_won(self, player, floor: int, is_boss: bool = False) -> None:
        """Начислить FP за выжитый бой (динамический приток по акту + бонус босса,
        ×ARTIFACT_FP_MULT — заглушка-катализатор артефактов). Единая формула с
        живой игрой: core.forge.combat_fp_gain (читает core.ARTIFACT_FP_MULT)."""
        _ensure_state(player)
        player.forge_points += combat_fp_gain(floor, is_boss)

    def on_boss_defeated(self, player, floor: int) -> None:
        """Босс снимает кап уровня до следующего майлстоуна (увязка шкал §3)."""
        _ensure_state(player)
        new_cap = next_cap_for_boss(floor)
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
                cost = level_cost(rec["level"])
                if player.forge_points < cost:
                    continue
                player.forge_points -= cost
                rec["level"] += 1
                apply_linear_level(card, LINEAR_BONUS_PER_LEVEL)
                # Пересекли уровень-границу (кратный s)? До 15 → открыть слот;
                # >15 (20/25/…) → Гипер-заряд существующего тега (§4-bis: слотов
                # всегда 3). Канал тега = природа карты (Развилка №1).
                lvl  = rec["level"]
                tier = milestone_tier(lvl)
                if tier is not None:
                    channel = card_forge_channel(card)
                    tag_id  = pick_tag(class_name, tier, channel)
                    rec["slots"].append({"tag_id": tag_id, "grade": 0})
                elif is_overcharge_level(lvl):
                    overcharge_slot(rec)
                progressed = True
                break       # переоценить с вершины (концентрация на лучшей)

    # ── ЗАТОЧКА (Sharpen) — DPS-сток FP в множитель урона (С39.4) ───────────────
    @staticmethod
    def sharpen(player) -> bool:
        """Заточка на костре: сток FP в player.atk_mult (core.forge.sharpen)."""
        _ensure_state(player)
        return _core_sharpen(player)

    def sharpen_if_threatened(self, player, floor: int) -> bool:
        """Проактивная Заточка (С39.4): пока угроза следующего акта держит порог,
        лить FP в множитель урона. atk_mult НЕ меняет max_hp/угрозу → дренит весь
        доступный FP за костёр — именно это даёт компаунд-флип DPS-трио (свип 39.4).

        ⚠️ С57: Закалка (оборонный аналог) переехала на ЗОЛОТО → EconomyPolicy.
        ТЕМА-ГЕЙТ маршрутизации (офенс→Заточка / оборона→Закалка) поднят в runner,
        где доступны обе политики (forge для FP, economy для золота)."""
        _ensure_state(player)
        threat = incoming_next_act(floor)
        did = False
        while (threat >= _cf.TEMPER_PROACTIVE_RATIO * player.max_hp
               and player.forge_points >= _cf.SHARPEN_FP_COST):
            if not self.sharpen(player):
                break
            did = True
        return did

    # Тонкие делегаторы к core (совместимость с тестами sim-API).
    @staticmethod
    def _level_cost(level: int) -> int:
        """Цена +1 уровня при текущем уровне (core.forge.level_cost)."""
        return _cf.level_cost(level)

    @staticmethod
    def invested_fp(level: int) -> int:
        """Суммарный вложенный FP для уровня 0→level (core.forge.invested_fp)."""
        return _cf.invested_fp(level)

    @staticmethod
    def _record(player, card) -> dict:
        """Запись ковки для карты (по уникальному uid инстанса). uid выдаётся
        лениво — паспорт инстанса в симе (зеркало Card._fuid в живой игре)."""
        if not hasattr(card, "_fuid"):
            card._fuid = player._forge_uid_next
            player._forge_uid_next += 1
        state = player.deck_forge_state
        if card._fuid not in state:
            state[card._fuid] = {"level": 0, "slots": []}
        return state[card._fuid]
