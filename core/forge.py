# core/forge.py
# ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ экономики и уровней ковки карт (Сессия 39.5).
# Чистые константы + хелперы движка прокачки (см. _upgrade_design.md §3-6,10).
# Их используют ОБА слоя — живая игра (GameManager/Campfire/CombatManager) и
# симулятор (managers/balance/forge.py: ForgePolicy + бот-решения). Здесь НЕТ
# бот-политики и НЕТ зависимости от sim-пакета — только калиброванные числа и
# детерминированная математика.
#
# Реестр условных ТЕГОВ (предикаты, каналы, гипер-заряд) живёт отдельно в
# core/ForgeRegistry.py; здесь — экономика (FP, цена уровня, босс-капы), линейный
# слой стены (δ), Закалка/Заточка и предохранитель глубины триггеров.
#
# Калибровка ручек — _balance_knobs.md (раздел «Прокачка»). Изменяемые в свипе
# константы (TEMPER_*/ARTIFACT_*) мутируются ИМЕННО в этом модуле (managers/balance
# /sweep.py пишет в core.forge), поэтому функции, читающие их, читают globals
# этого модуля в рантайме → свип влияет на поведение без рассинхрона копий.

from managers.MapGenerator import FLOORS_PER_ACT
from core.cards.base import (
    DamageEffect, ShieldEffect, BarrierEffect, HealEffect, RegenEffect,
    StatusEffect,
)

# ─── ЭКОНОМИКА FP (ручка скорости c, _upgrade_design.md §3,6) ──────────────────
# Приток FP за выжитый бой растёт по акту (этаж//20+1), кап на последнем элементе.
# Калибровка 39.4 (свип флипа DPS-трио Заточкой): акт 1→2, акт 2→3, акт 3+→4 FP.
FORGE_POINTS_PER_ACT  = (2, 3, 4)   # FP за бой в актах 1 / 2 / 3+
FORGE_POINTS_PER_BOSS = 3           # бонус FP за босса (поверх боевого притока)

# Линейный слой СТЕНЫ (кат.1): +δ к числовым эффектам карты за уровень.
LINEAR_BONUS_PER_LEVEL = 1          # δ

# Растущая цена уровня СО СБРОСОМ ВНУТРИ ТИРА: cost = BASE + (level mod s)·STEP.
# Тир 0→5 / 5→10 / 10→15 каждый стоит 1+2+3+4+5 = 15 FP ⇒ 45 FP до легендарного.
LEVEL_COST_BASE = 1
LEVEL_COST_STEP = 1

# Кап уровня карты до первого босса (ниже первого майлстоуна 5 → теги недоступны).
INITIAL_LEVEL_CAP = 4
# Босс-этаж → новый кап уровня карты (увязка шкал §3): 20→5 (слот-1), 40→10
# (слот-2), 60→15 (слот-3, ×mult), 80→20 / 100→25 (круги Гипер-заряда; слотов 3).
BOSS_LEVEL_CAPS = {20: 5, 40: 10, 60: 15, 80: 20, 100: 25}

# Уровни-майлстоуны (открывают теговые слоты) и тир тега по майлстоуну.
MILESTONES     = (5, 10, 15)
MILESTONE_STEP = 5                  # шаг майлстоунов `s` (цена тира сбрасывается каждые s)
MILESTONE_TIER = {5: "early", 10: "early", 15: "legendary"}
# Уровни >15, кратные s (20/25/…), не открывают слот, а гипер-заряжают тег (§4-bis).
OVERCHARGE_FROM_LEVEL = 15

# ─── ЗАКАЛКА (Магазин) — сток ЗОЛОТА в Max HP ([[economy-axis-trinity]]) ───────
# С57: Закалка переведена с FP на ЗОЛОТО — развести валюты по осям (золото =
# выживаемость, FP = чистый оффенс). Цена в золоте — ЗАГЛУШКА, калибруется свипом
# против притока золота (см. _balance_knobs «Прокачка», шаг 1d дуги economy-arc-plan).
TEMPER_HP_PCT          = 0.20       # +20% к текущему max_hp за одну Закалку (КАЛИБР. 39.3)
TEMPER_GOLD_COST       = 60         # цена Закалки в ЗОЛОТЕ (ЗАГЛУШКА — свип 1d)
TEMPER_PROACTIVE_RATIO = 0.6        # порог «гонки кривых» бота (решение о Закалке)
INCOMING_FIGHT_TURNS   = 5          # длина боя для перевода урона-за-ход в давление

# ─── ЗАТОЧКА (Sharpen) — DPS-аналог Закалки, сток FP в множитель урона (С39.4) ─
SHARPEN_FP_COST = 5                 # цена одной Заточки в FP (дешевле Закалки)
SHARPEN_ATK_PCT = 0.30             # +30% к player.atk_mult за одну Заточку (компаунд)

# ─── ТРИЕДИНСТВО ЭКОНОМИКИ: PLACEHOLDER-ЗАГЛУШКИ АРТЕФАКТОВ (С39.3) ────────────
# Нейтральны по умолчанию (baseline зелёный); свип/будущие артефакты крутят вверх.
ARTIFACT_FP_MULT    = 1.0           # ×множитель к притоку FP за бой/босса
ARTIFACT_MAX_HP_ADD = 0            # +флэт к Max HP за одну Закалку (глобальный катализатор)

# ─── ПРЕДОХРАНИТЕЛЬ ГЛУБИНЫ ТРИГГЕРОВ (гард-рейл §10.2) ───────────────────────
MAX_TRIGGER_DEPTH = 5               # жёсткий потолок вложенных триггеров за действие


# ─── ЭКОНОМИКА: чистые функции ────────────────────────────────────────────────
def fp_per_combat(floor: int) -> int:
    """Динамический приток FP за выжитый бой на этаже `floor` (ручка `c`).
    Растёт по акту, кап = последний элемент FORGE_POINTS_PER_ACT."""
    act_idx = (floor - 1) // FLOORS_PER_ACT      # 0-based: акт 1 → 0
    if act_idx < 0:
        act_idx = 0
    return FORGE_POINTS_PER_ACT[min(act_idx, len(FORGE_POINTS_PER_ACT) - 1)]


def combat_fp_gain(floor: int, is_boss: bool = False) -> int:
    """Полный приток FP за бой: боевой приток (+бонус босса) ×ARTIFACT_FP_MULT.
    Единая формула для живой игры (GameManager) и сима (ForgePolicy.on_combat_won)."""
    gain = fp_per_combat(floor)
    if is_boss:
        gain += FORGE_POINTS_PER_BOSS
    return int(round(gain * ARTIFACT_FP_MULT))


def level_cost(level: int) -> int:
    """Цена +1 уровня при текущем уровне. Крутизна СБРАСЫВАЕТСЯ на каждом
    майлстоуне (§3): внутри тира base+(level mod s)·step, новый тир — заново с base."""
    return LEVEL_COST_BASE + (level % MILESTONE_STEP) * LEVEL_COST_STEP


def invested_fp(level: int) -> int:
    """Сколько FP суммарно вложено, чтобы поднять карту с 0 до `level` (основа
    Переплавки: сжигание карты возвращает 100% этой суммы в банк)."""
    return sum(level_cost(lvl) for lvl in range(level))


def reward_level_for_floor(floor: int) -> int:
    """Минимальный уровень карты в награде на этаже `floor` (§10.5). Привязан к
    пройденным босс-гейтам: до первого босса — 0, после 20 → 5, 40 → 10, 60 → 15."""
    level = 0
    for boss_floor, milestone in sorted(BOSS_LEVEL_CAPS.items()):
        if floor > boss_floor:
            level = milestone
    return level


def assign_forge_uid(player, card):
    """Выдать карте СТАБИЛЬНЫЙ uid инстанса для паспорта ковки, если его ещё нет
    (§2: тег живёт на конкретном экземпляре). Зеркало ForgePolicy._record в симе.
    Зовётся при входе карты в колоду забега (старт-колода + добор). Паспорт
    (запись в deck_forge_state) создаётся лениво при первой ковке."""
    if getattr(card, "_fuid", None) is None:
        card._fuid = player._forge_uid_next
        player._forge_uid_next += 1
    return card._fuid


def forge_level(player, card) -> int:
    """Текущий уровень ковки карты (0, если паспорта ещё нет)."""
    uid = getattr(card, "_fuid", None)
    if uid is None:
        return 0
    rec = player.deck_forge_state.get(uid)
    return rec["level"] if rec else 0


def can_forge(player, card) -> bool:
    """Можно ли поднять карту ещё на +1 уровень: не упёрлись в кап И хватает FP."""
    level = forge_level(player, card)
    return level < player.forge_level_cap and player.forge_points >= level_cost(level)


def next_forge_milestone_tier(player, card):
    """Тир тега, который ОТКРОЕТ следующая ковка карты (если +1 уровень = майлстоун
    5/10/15). None, если следующий уровень не майлстоун (линейный слой / Гипер-заряд)
    или карта уже на капе. Канал для драфта берётся отдельно (card_forge_channel).
    Используется живым UI (костёр), чтобы перед ковкой решить: показать драфт 1-из-3?"""
    level = forge_level(player, card)
    if level >= player.forge_level_cap:
        return None
    return milestone_tier(level + 1)


def forge_card_one_level(player, card, class_name: str = "", forced_tag=None) -> bool:
    """ЖИВАЯ ковка карты на +1 уровень за FP (костёр, 39.5). Возвращает True при
    успехе. Миграция линейного слоя: уровень 1 = бережно ручной «+» карты
    (card.upgrade), уровни ≥2 = +δ (apply_linear_level). На майлстоуне (5/10/15)
    открывает слот: `forced_tag` (выбор игрока в драфте 1-из-3, B3) ИЛИ, если не
    задан, АВТО-лучший pick_tag по каналу карты (sim/baseline); уровень >15,
    кратный s, — Гипер-заряд существующего тега.

    NB: sim использует свой forge_between_acts (δ-only, без ручного «+») —
    расхождение линейного слоя принято (_upgrade_design.md §2)."""
    # Ленивая штамповка uid (зеркало sim ForgePolicy._record): карта могла попасть
    # в колоду минуя GameManager.__init__ (напр. пересоздание колоды при выборе
    # класса в HUB) — без этого ковка молча отваливалась. Обойти невозможно.
    uid = assign_forge_uid(player, card)
    rec = player.deck_forge_state.get(uid) or {"level": 0, "slots": []}
    level = rec["level"]
    if level >= player.forge_level_cap:
        return False
    cost = level_cost(level)
    if player.forge_points < cost:
        return False

    player.forge_points -= cost
    player.deck_forge_state[uid] = rec          # закрепить паспорт (первая ковка)
    rec["level"] = new_level = level + 1

    # Линейный слой стены (миграция одноступенчатого upgrade).
    if new_level == 1:
        if hasattr(card, "upgrade"):
            card.upgrade()                      # level 1 = текущий ручной «+»
    else:
        apply_linear_level(card, LINEAR_BONUS_PER_LEVEL)

    # Слой потолка: майлстоун → слот+тег; >15 кратный s → Гипер-заряд.
    tier = milestone_tier(new_level)
    if tier is not None:
        channel = card_forge_channel(card)
        if forced_tag is not None:
            tag_id = forced_tag                 # выбор игрока в драфте (B3)
        else:
            from core.ForgeRegistry import pick_tag
            tag_id = pick_tag(class_name, tier, channel)   # авто (sim/baseline)
        rec["slots"].append({"tag_id": tag_id, "grade": 0})
    elif is_overcharge_level(new_level):
        overcharge_slot(rec)
    return True


def forge_card_to_level(player, card, target_level: int, class_name: str = "") -> int:
    """Сразу выковать карту до `target_level` БЕЗ траты FP (товар магазина, §10.5,
    шаг 3 эконом-дуги). Применяет ОБА слоя ковки шаг-за-шагом (как накопленный
    forge_card_one_level), чтобы линейные числа И майлстоун-теги совпали с тем, что
    дала бы ручная прокачка: уровень 1 = card.upgrade(), ≥2 = +δ; майлстоуны 5/10/15
    открывают слот (авто pick_tag по каналу), >15 кратные s — Гипер-заряд.

    Паспорт пишется в player.deck_forge_state по uid карты (как у купленной карты в
    колоде). Возвращает достигнутый уровень. НЕ ограничен forge_level_cap (товар уже
    выкован продавцом; кап — про ЖИВУЮ ковку игроком за FP)."""
    if target_level <= 0:
        return forge_level(player, card)
    uid = assign_forge_uid(player, card)
    rec = player.deck_forge_state.get(uid) or {"level": 0, "slots": []}
    player.deck_forge_state[uid] = rec
    while rec["level"] < target_level:
        new_level = rec["level"] + 1
        if new_level == 1:
            if hasattr(card, "upgrade"):
                card.upgrade()
        else:
            apply_linear_level(card, LINEAR_BONUS_PER_LEVEL)
        tier = milestone_tier(new_level)
        if tier is not None:
            from core.ForgeRegistry import pick_tag
            channel = card_forge_channel(card)
            rec["slots"].append({"tag_id": pick_tag(class_name, tier, channel),
                                 "grade": 0})
        elif is_overcharge_level(new_level):
            overcharge_slot(rec)
        rec["level"] = new_level
    return rec["level"]


def discard_forge_record(player, card) -> None:
    """Снять паспорт ковки карты с игрока (товар магазина не куплен → не засоряем
    deck_forge_state). Безопасно, если паспорта нет."""
    uid = getattr(card, "_fuid", None)
    if uid is not None and uid in getattr(player, "deck_forge_state", {}):
        del player.deck_forge_state[uid]


def next_cap_for_boss(floor: int):
    """Новый кап уровня карты, открываемый победой над боссом этажа `floor`
    (увязка шкал §3). None, если этаж — не босс-чекпойнт."""
    return BOSS_LEVEL_CAPS.get(floor)


def milestone_tier(level: int):
    """Тир тега, открываемого уровнем-майлстоуном (5/10 → early, 15 → legendary).
    None, если уровень — не майлстоун."""
    return MILESTONE_TIER.get(level)


def is_overcharge_level(level: int) -> bool:
    """Уровень переводит ковку в Гипер-заряд (§4-bis): >15 и кратен шагу s (20/25/…)."""
    return level > OVERCHARGE_FROM_LEVEL and level % MILESTONE_STEP == 0


# ─── ЛИНЕЙНЫЙ СЛОЙ И КЛАССИФИКАЦИЯ КАРТ ───────────────────────────────────────
def apply_linear_level(card, delta: int) -> None:
    """Применить ОДИН линейный уровень к карте: +delta ко всем числовым эффектам
    (base_val/upgrade_val). Слой СТЕНЫ — строго линейный, БЕЗ множителей
    (_upgrade_design.md §10.3: компаунд заперт только в условных тегах)."""
    for e in card.effects:
        if hasattr(e, "base_val") and hasattr(e, "upgrade_val"):
            e.base_val    += delta
            e.upgrade_val += delta


def rebuild_card_linear_to(card, level: int) -> None:
    """Восстановить ЛИНЕЙНЫЙ слой ковки карты до `level` БЕЗ траты FP (загрузка сейва
    забега, С57). Воспроизводит мутацию base_val как forge_card_one_level: уровень 1 =
    ручной upgrade, уровни ≥2 = +δ за каждый. Майлстоун-теги (slots) живут в
    deck_forge_state по uid и читаются при расчёте урона — карту не мутируют, поэтому
    их восстанавливать тут не нужно (state восстанавливается отдельно)."""
    if level >= 1 and hasattr(card, "upgrade"):
        card.upgrade()
    for _ in range(max(0, level - 1)):
        apply_linear_level(card, LINEAR_BONUS_PER_LEVEL)


def card_forge_channel(card) -> str:
    """КАНАЛ карты для выбора тега (Развилка №1, §5): природа карты определяет, какой
    тег откроется на её майлстоуне. Щитовая/барьерная → 'shield', чисто лечащая →
    'heal', иначе 'damage' (атака доминирует). ⇒ игрок строит ОБЕ оси."""
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


def card_is_defensive(card) -> bool:
    """Карта ЧИСТО оборонная: даёт щит/барьер/хил/реген И не несёт урона/дотов.
    Карта с уроном (даже вперемешку со щитом) — НЕ оборонная (офенс доминирует)."""
    has_def = has_off = False
    for e in card.effects:
        if isinstance(e, (ShieldEffect, BarrierEffect, HealEffect, RegenEffect)):
            has_def = True
        elif isinstance(e, DamageEffect):
            has_off = True
        elif isinstance(e, StatusEffect) and e.status_type == "legacy":
            has_off = True   # Legacy-код — DoT (офенс), как поглощённые им Яд/Кровь
    return has_def and not has_off


# ─── ГИПЕР-ЗАРЯД (§4-bis) ─────────────────────────────────────────────────────
def overcharge_slot(rec: dict) -> None:
    """Гипер-заряд: уровень >15, кратный s, не открывает слот, а усиливает
    существующий тег (grade +1 → сила ×OVERCHARGE_STEP^grade). Концентрация:
    заряжаем легендарный (×mult) слот, если есть, иначе первый. Нет слотов → no-op."""
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


# ─── ЗАКАЛКА / ЗАТОЧКА (стоки ресурсов; мутируют игрока) ──────────────────────
def temper(player, gold_available: int):
    """Закалка (С57): сток ЗОЛОТА в Max HP. Навсегда +TEMPER_HP_PCT к ТЕКУЩЕМУ
    max_hp (компаунд-%) + флэт-катализатор артефактов + полное исцеление.

    ЧИСТАЯ функция (инвариант core/forge.py — без зависимости от gm): принимает
    доступное золото, возвращает (ok, gold_spent). Списание золота с кошелька
    (gm.player_gold в живой игре / симе) — на вызывающем слое. Зеркало sharpen.
    Предполагает, что max_hp/hp у игрока уже инициализированы."""
    if gold_available < TEMPER_GOLD_COST:
        return False, 0
    gain = int(player.max_hp * TEMPER_HP_PCT) + ARTIFACT_MAX_HP_ADD
    player.max_hp += gain
    player.hp = player.max_hp        # полное исцеление
    return True, TEMPER_GOLD_COST


def sharpen(player) -> bool:
    """Заточка (С39.4): тратит SHARPEN_FP_COST FP, навсегда ×(1+SHARPEN_ATK_PCT)
    к player.atk_mult (компаунд-множитель урона на ВСЕ атаки, EffectCalculator шаг 8).
    Возвращает True, если хватило FP. Предполагает созданное ковочное состояние."""
    if player.forge_points < SHARPEN_FP_COST:
        return False
    player.forge_points -= SHARPEN_FP_COST
    player.atk_mult = getattr(player, "atk_mult", 1.0) * (1 + SHARPEN_ATK_PCT)
    return True


# ─── ПРЕДОХРАНИТЕЛЬ ГЛУБИНЫ ТРИГГЕРОВ (гард-рейл §10.2) ───────────────────────
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
