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
from managers.MapGenerator import FLOORS_PER_ACT
from core.ForgeRegistry import pick_tag
from core.cards.base import (
    DamageEffect, ShieldEffect, BarrierEffect, HealEffect, RegenEffect,
)

# ─── РУЧКИ (калибровка 39.3 — _balance_knobs.md раздел «Прокачка») ────────────
# Экономика FP — ДИНАМИЧЕСКИЙ приток по актам (ручка скорости c, _upgrade_design
# §3,6). FP начисляется ЗА БОЙ; величина растёт по акту (этаж//20+1), кап на 3.
# Калибровка (выбор юзера, 39.3): акт 1→1, акт 2→2, акт 3+→3 FP за бой ⇒ ~120 FP
# за забег (этажи 1-60) ≈ кумулятивная цена 15-го уровня → потолок флипает к сер.
# Акта 3, но не раньше (ранняя стена защищена).
FORGE_POINTS_PER_ACT = (1, 2, 3)   # FP за бой в актах 1 / 2 / 3+
FORGE_POINTS_PER_BOSS = 3          # бонус FP за босса (поверх боевого притока)
# Линейный слой стены.
LINEAR_BONUS_PER_LEVEL  = 1     # δ: +N к числовым эффектам карты за уровень
# Растущая цена уровня СО СБРОСОМ ВНУТРИ ТИРА: cost = BASE + (level mod s)·STEP.
# Крутизна сбрасывается на каждом майлстоуне (§3): тир 0→5, 5→10, 10→15 каждый
# стоит 1+2+3+4+5 = 15 FP ⇒ 45 FP до легендарного ×mult. Тактический прессинг
# внутри тира (добить майлстоун дорого), но новый тир не наследует абсолют.
LEVEL_COST_BASE = 1
LEVEL_COST_STEP = 1


def fp_per_combat(floor: int) -> int:
    """Динамический приток FP за выжитый бой на этаже `floor` (ручка `c`).
    Растёт по акту, кап = последний элемент FORGE_POINTS_PER_ACT."""
    act_idx = (floor - 1) // FLOORS_PER_ACT      # 0-based: акт 1 → 0
    if act_idx < 0:
        act_idx = 0
    return FORGE_POINTS_PER_ACT[min(act_idx, len(FORGE_POINTS_PER_ACT) - 1)]
# Кап уровня карты до первого босса (act 1). Ниже первого майлстоуна (5) →
# теги недоступны на ранних этажах (железная защита стены).
INITIAL_LEVEL_CAP = 4
# Босс-этаж → новый кап уровня карты (увязка шкал, _upgrade_design.md §3):
# босс-20 открывает майлстоун-5 (слот-1), 40 → 10 (слот-2), 60 → 15 (слот-3, ×mult).
# С босса-80 (кап 20) слоты больше НЕ открываются (заперты на 3) — уровни идут в
# Гипер-заряд существующих тегов (§4-bis).
BOSS_LEVEL_CAPS = {20: 5, 40: 10, 60: 15, 80: 20, 100: 25}
# Уровни-майлстоуны (открывают теговые слоты). Тир тега по майлстоуну
# (_upgrade_design.md §4): 5/10 → ранний (+mult), 15 → легендарный (×mult).
MILESTONES = (5, 10, 15)
MILESTONE_STEP = 5              # шаг майлстоунов `s` (цена тира сбрасывается каждые s)
MILESTONE_TIER = {5: "early", 10: "early", 15: "legendary"}
# Слотов на карте ВСЕГДА 3 (5/10/15). Уровень, с которого ковка переходит в
# Гипер-заряд вместо открытия слота (§4-bis): 20, 25, 30… (кратные шагу, ≥ порога).
OVERCHARGE_FROM_LEVEL = 15     # уровни >15, кратные s, гипер-заряжают (20/25/…)

# ─── ЗАКАЛКА (Отдых) — альтернативный сток FP в Max HP (_upgrade_design.md §3) ─
# Бот тратит FP не на ковку, а на расширение бака HP. Компаунд-процент (§10.3):
# +TEMPER_HP_PCT к ТЕКУЩЕМУ max_hp + полное исцеление.
TEMPER_HP_PCT  = 0.20          # +20% к текущему max_hp за одну Закалку (КАЛИБР. 39.3)
TEMPER_FP_COST = 10            # цена Закалки в FP (КАЛИБР. 39.3; ориентир был 10-15)
# ПРОАКТИВНЫЙ порог (С39.3, «гонка кривых»): бот закаляется на КАЖДОМ костре, пока
# давление боя следующего акта ≥ RATIO·max_hp. RATIO=1.0 → аварийное поведение
# (только ваншот); RATIO<1.0 → проактивно: бот наращивает бак ЗАРАНЕЕ, гоняясь за
# экспонентой урона врага. КАЛИБР. 39.3 = 0.6 (флипает HP-классы в акт 3; см.
# память economy-trinity-survival-engine). forge OFF в baseline ⇒ регресс-нейтрально.
TEMPER_PROACTIVE_RATIO = 0.6
# Перевод УРОНА-ЗА-ХОД в ДАВЛЕНИЕ БОЯ: одиночный удар (~9 на эт.19) — не угроза,
# но залп ×N ходов экспозиции СОПОСТАВИМ с баком. Бот считает «гонку кривых» по
# накопленному давлению боя = урон_за_ход · INCOMING_FIGHT_TURNS. Репрезентативная
# длина боя (предмет свипа; ~5 ходов клир группы).
INCOMING_FIGHT_TURNS = 5

# ─── ТРИЕДИНСТВО ЭКОНОМИКИ: PLACEHOLDER-ЗАГЛУШКИ АРТЕФАКТОВ (С39.3) ────────────
# Артефакты (реликвии) = третий рычаг притока ресурсов (Бои=база, %-Ивенты=скачки,
# Артефакты=глобальные масштабираторы). Код артефактов ещё не написан → заложены
# нейтральные переменные-модификаторы, чтобы сим-математика УЖЕ учитывала будущий
# лейт-раскорм реликвиями (запас прочности +15-20%). Дефолт нейтрален ⇒ baseline
# зелёный; свип/будущие артефакты крутят их вверх.
ARTIFACT_FP_MULT     = 1.0     # ×множитель к притоку FP за бой/босса
ARTIFACT_MAX_HP_ADD  = 0       # +флэт к Max HP за одну Закалку (глобальный катализатор)

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


def card_forge_channel(card) -> str:
    """КАНАЛ карты для выбора тега (Развилка №1, _upgrade_design.md §5): природа
    карты определяет, какой тег откроется на её майлстоуне. Щитовая/барьерная →
    'shield', чисто лечащая → 'heal', иначе 'damage'. Атака доминирует (карта с
    уроном И щитом → damage: основной выход — урон). ⇒ игрок строит ОБЕ оси,
    прокачивая разные карты своего ядра."""
    has_attack = has_shield = has_heal = False
    for e in card.effects:
        if isinstance(e, DamageEffect):
            has_attack = True
        elif isinstance(e, (ShieldEffect, BarrierEffect)):
            has_shield = True
        elif isinstance(e, (HealEffect, RegenEffect)):
            has_heal = True
    if has_attack:
        return "damage"
    if has_shield:
        return "shield"
    if has_heal:
        return "heal"
    return "damage"


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
        """Начислить FP за выжитый бой (динамический приток по акту + бонус босса).
        Приток масштабируется ARTIFACT_FP_MULT (заглушка-катализатор артефактов)."""
        _ensure_state(player)
        gain = fp_per_combat(floor)
        if is_boss:
            gain += FORGE_POINTS_PER_BOSS
        player.forge_points += int(round(gain * ARTIFACT_FP_MULT))

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
                # Пересекли уровень-границу (кратный s)? До 15 → открыть слот;
                # >15 (20/25/…) → Гипер-заряд существующего тега (§4-bis: слотов
                # всегда 3). Канал тега = природа карты (Развилка №1).
                lvl = rec["level"]
                if lvl in MILESTONE_TIER:
                    tier = MILESTONE_TIER[lvl]
                    channel = card_forge_channel(card)
                    tag_id = pick_tag(class_name, tier, channel)
                    rec["slots"].append({"tag_id": tag_id, "grade": 0})
                elif lvl > OVERCHARGE_FROM_LEVEL and lvl % MILESTONE_STEP == 0:
                    self._overcharge_slot(rec)
                progressed = True
                break       # переоценить с вершины (концентрация на лучшей)

    # ── внутреннее ───────────────────────────────────────────────────────────
    @staticmethod
    def _overcharge_slot(rec: dict) -> None:
        """Гипер-заряд (§4-bis): уровень >15, кратный s, не открывает слот, а
        усиливает существующий тег (grade +1 → сила ×OVERCHARGE_STEP^grade).
        Концентрация: заряжаем легендарный (×mult) слот, если есть, иначе первый —
        больше всего отдачи от компаунд-тега. Нет слотов → no-op (карта без тегов)."""
        slots = rec.get("slots")
        if not slots:
            return
        from core.ForgeRegistry import TAGS
        # Приоритет — легендарный (mult) слот: grade масштабирует компаунд круче.
        def slot_key(slot):
            spec = TAGS.get(slot.get("tag_id"), {})
            return 0 if spec.get("kind") == "mult" else 1
        target = min(slots, key=slot_key)
        target["grade"] = target.get("grade", 0) + 1

    # ── ЗАКАЛКА (Отдых) ────────────────────────────────────────────────────────
    @staticmethod
    def temper(player) -> bool:
        """Закалка на костре (_upgrade_design.md §3): тратит TEMPER_FP_COST FP,
        навсегда +TEMPER_HP_PCT к ТЕКУЩЕМУ max_hp (компаунд-%) + полное исцеление.
        Возвращает True, если закалка прошла (хватило FP). Сток FP, альтернативный
        ковке: бак HP — фундамент под оборонные теги (хил капается max_hp)."""
        _ensure_state(player)
        if player.forge_points < TEMPER_FP_COST:
            return False
        player.forge_points -= TEMPER_FP_COST
        # Компаунд-% от текущего бака + флэт-катализатор артефактов (заглушка).
        gain = int(player.max_hp * TEMPER_HP_PCT) + ARTIFACT_MAX_HP_ADD
        player.max_hp += gain
        player.hp = player.max_hp        # полное исцеление
        return True

    @staticmethod
    def incoming_next_act(floor: int) -> int:
        """Оценка входящего урона за ход в СЛЕДУЮЩЕМ акте (для решения о Закалке).
        Грубое зеркало EnemySpawner: пиковый этаж следующего акта × формула урона,
        с поправкой на группы. Используется ботом как «угроза ваншота»."""
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

    def temper_if_threatened(self, player, floor: int) -> bool:
        """Решение бота на костре («гонка кривых», С39.3): пока входящий урон
        следующего акта ≥ TEMPER_PROACTIVE_RATIO·max_hp, жертвовать FP на Закалку
        (расширять бак) вместо ковки. RATIO=1.0 → старое аварийное поведение
        (только ваншот); RATIO<1.0 → бот наращивает бак ЗАРАНЕЕ, не дожидаясь
        угрозы ваншота, — истинный per-floor рычаг выживаемости (предмет свипа).
        Может закалиться несколько раз, пока хватает FP и порог держится."""
        _ensure_state(player)
        threat = self.incoming_next_act(floor)
        tempered = False
        while (threat >= TEMPER_PROACTIVE_RATIO * player.max_hp
               and player.forge_points >= TEMPER_FP_COST):
            if not self.temper(player):
                break
            tempered = True
        return tempered

    @staticmethod
    def _level_cost(level: int) -> int:
        """Цена +1 уровня при текущем уровне. Крутизна СБРАСЫВАЕТСЯ на каждом
        майлстоуне (_upgrade_design.md §3): внутри тира растёт base+(level mod s)·step,
        но новый тир начинается заново с base ⇒ каждый тир = фикс. бюджет FP."""
        return LEVEL_COST_BASE + (level % MILESTONE_STEP) * LEVEL_COST_STEP

    @staticmethod
    def invested_fp(level: int) -> int:
        """Сколько FP суммарно вложено, чтобы поднять карту с 0 до `level`
        (сумма _level_cost по всем пройденным уровням). Основа Переплавки:
        сжигание карты возвращает 100% этой суммы в банк."""
        return sum(ForgePolicy._level_cost(lvl) for lvl in range(level))

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
