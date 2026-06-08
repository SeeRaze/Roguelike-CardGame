# core/ForgeRegistry.py
# СЕССИЯ 39, шаги 39.2-39.3 — условные теги прокачки карт (см. _upgrade_design.md §4-5,10).
# Data-driven реестр предикатов (как DetonationRegistry/ComboRegistry). Тег = слот,
# открытый майлстоуном карты (5/10/15). Ранние теги дают АДДИТИВНЫЙ +mult (мягкий
# старт), легендарные — МУЛЬТИПЛИКАТИВНЫЙ ×mult (истинный компаунд кат.4).
#
# УНИВЕРСАЛЬНАЯ КОВКА (Развилка №1, Вариант 1 — _upgrade_design.md §5): каждый тег
# несёт КАНАЛ `channel ∈ {damage, shield, heal}`. damage → множитель урона
# (EffectCalculator шаг 7); shield → множитель генерации Щита/Барьера; heal →
# множитель исцеления/регена. Оборонные ×mult растят выживаемость `p` (щит в симе
# поглощает урон 1:1 за ход, Барьер компаундит) — закрывают оборонный дефицит, на
# который упёрся атакующий-only движок (см. память balance-findings-forge-flip).
#
# ГИПЕР-ЗАРЯД (§4-bis): слотов на карте всегда 3, но тег может «гипер-заряжаться»
# (grade 0→1→2…) после уровня 20 — его сила ×OVERCHARGE_STEP^grade. Бесконечная
# экспонента живёт в grade, а не в числе слотов (UI заперт на 3 строки).
#
# КЛЮЧЕВОЕ: предикат читает ТОЛЬКО снимок состояния (_play_snapshot, §10.6) —
# замороженный контекст на момент намерения. Это даёт реал-тайм-корректность и
# NULL-SAFETY (§10.7): даже если цель погибла в каскаде, снимок хранит её прежние
# значения, предикат не падает. Все чтения снимка идут через _s() с дефолтом 0.
#
# Линейный слой (δ) строго линеен и живёт в forge.apply_linear_level — здесь ТОЛЬКО
# условный компаунд (§10.3: множители заперты в тегах).

# ─── РУЧКИ силы тегов (гипотезы Шага 0 §6; калибруются в 39.3) ────────────────
EARLY_ADD          = 0.5    # ранний тег: +0.5 к множителю при выполнении условия
LEG_EMPTY_HAND     = 2.0    # легендарный флаг «из пустой руки»: ×2.0
# Легендарные масштабируемые (×(1 + scale·стат)) — компаунд растёт с движком класса.
LEG_PER_MINION     = 0.20   # за миньона (Призыватель, резонанс со Сворой N²)
LEG_PER_POISON     = 0.015  # за стак яда (Друид, Вирулентность)
LEG_PER_BLEED      = 0.04   # за стак кровотечения (Разбойник, Кровожадность)
LEG_PER_SHIELD     = 0.01   # за единицу щита/барьера (Воин, Барьер) — канал damage
LEG_PER_COMBO      = 0.08   # за накопленное Мастерство (Маг, комбо)
LEG_MISSING_HP     = 1.00   # ×(1 + доля недостающего HP) (Берсерк)

# ── ОБОРОННЫЕ / СУСТЕЙН ручки (Развилка №1) ──────────────────────────────────
LEG_PER_BARRIER    = 0.04   # ×ЩИТ за стак Барьера (Воин: барьер растит сам себя)
LEG_LAST_STAND     = 2.0    # ×ЩИТ на грани (HP<порога) — контр-ваншот
LEG_VENOM_WARD     = 0.04   # ×ИСЦЕЛЕНИЕ за стак яда на цели (Друид: яд→сустейн)
LEG_LIFEBLOOM      = 1.00   # ×ИСЦЕЛЕНИЕ по доле недостающего HP (мощнее когда ранен)
LOW_HP_THRESHOLD   = 0.5    # порог «низкого HP» для low_hp / last_stand

# ─── ГИПЕР-ЗАРЯД (§4-bis) ─────────────────────────────────────────────────────
# Сила тега ×OVERCHARGE_STEP^grade. grade растёт при ковке уровня ≥20 каждые +5
# (ForgePolicy). Для add-тегов масштабируется добавка, для mult — «излишек над 1»
# (т.е. 1+(v−1)·step^grade) ⇒ grade усиливает именно компаунд, не базовую 1.0.
OVERCHARGE_STEP    = 1.2


def _s(snapshot, key, default=0):
    """Null-safe чтение снимка (§10.7): нет снимка/ключа → дефолт."""
    if not snapshot:
        return default
    return snapshot.get(key, default)


# ─── РЕЕСТР ТЕГОВ ─────────────────────────────────────────────────────────────
# Каждый тег: kind ('add'|'mult'), tier ('early'|'legendary'), channel
# ('damage'|'shield'|'heal'), klass (резонанс), label (UI/глоссарий),
# fn(snapshot) -> вклад:
#   add  → аддитивная добавка к множителю (0.0, если условие не выполнено);
#   mult → множитель ≥1.0 (1.0, если условие не выполнено).
# channel по умолчанию 'damage' (атакующие теги). Оборонные/сустейн помечены явно.
TAGS = {
    # ── Ранние АТАКУЮЩИЕ (+mult, аддитивные, channel=damage) ──────────────────
    "shielded":   {"kind": "add", "tier": "early", "channel": "damage", "klass": "Warrior",
                   "label": "Под щитом: +урон",
                   "fn": lambda s: EARLY_ADD if (_s(s, "shield") + _s(s, "barrier")) > 0 else 0.0},
    "poisoned":   {"kind": "add", "tier": "early", "channel": "damage", "klass": "Druid",
                   "label": "По отравленной цели: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "tgt_poison") > 0 else 0.0},
    "low_hp":     {"kind": "add", "tier": "early", "channel": "damage", "klass": "Berserker",
                   "label": "На низком HP: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "hp_frac", 1.0) < LOW_HP_THRESHOLD else 0.0},
    "minions":    {"kind": "add", "tier": "early", "channel": "damage", "klass": "Summoner",
                   "label": "При миньонах: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "minions") > 0 else 0.0},
    "bleed":      {"kind": "add", "tier": "early", "channel": "damage", "klass": "Rogue",
                   "label": "По кровоточащей цели: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "tgt_bleed") > 0 else 0.0},
    "combo":      {"kind": "add", "tier": "early", "channel": "damage", "klass": "Mage",
                   "label": "После комбо: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "mastery") > 0 else 0.0},
    "first_card": {"kind": "add", "tier": "early", "channel": "damage", "klass": None,
                   "label": "Первой картой за ход: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "play_index") == 0 else 0.0},

    # ── Ранние ОБОРОННЫЕ/СУСТЕЙН (+mult, аддитивные) ──────────────────────────
    "bulwark":    {"kind": "add", "tier": "early", "channel": "shield", "klass": None,
                   "label": "Оборонная рука: +щит",
                   "fn": lambda s: EARLY_ADD if _s(s, "hand_attack") == 0 else 0.0},
    "mending":    {"kind": "add", "tier": "early", "channel": "heal", "klass": None,
                   "label": "Когда ранен: +исцеление",
                   "fn": lambda s: EARLY_ADD if _s(s, "hp_frac", 1.0) < 1.0 else 0.0},

    # ── Легендарные АТАКУЮЩИЕ (×mult, истинный компаунд, channel=damage) ───────
    "per_minion": {"kind": "mult", "tier": "legendary", "channel": "damage", "klass": "Summoner",
                   "label": "×урон за каждого миньона",
                   "fn": lambda s: 1.0 + LEG_PER_MINION * _s(s, "minions")},
    "per_poison": {"kind": "mult", "tier": "legendary", "channel": "damage", "klass": "Druid",
                   "label": "×урон по стакам яда",
                   "fn": lambda s: 1.0 + LEG_PER_POISON * _s(s, "tgt_poison")},
    "per_bleed":  {"kind": "mult", "tier": "legendary", "channel": "damage", "klass": "Rogue",
                   "label": "×урон по стакам кровотечения",
                   "fn": lambda s: 1.0 + LEG_PER_BLEED * _s(s, "tgt_bleed")},
    "per_shield": {"kind": "mult", "tier": "legendary", "channel": "damage", "klass": "Warrior",
                   "label": "×урон по щиту/барьеру",
                   "fn": lambda s: 1.0 + LEG_PER_SHIELD * (_s(s, "shield") + _s(s, "barrier"))},
    "per_combo":  {"kind": "mult", "tier": "legendary", "channel": "damage", "klass": "Mage",
                   "label": "×урон по Мастерству",
                   "fn": lambda s: 1.0 + LEG_PER_COMBO * _s(s, "mastery")},
    "missing_hp": {"kind": "mult", "tier": "legendary", "channel": "damage", "klass": "Berserker",
                   "label": "×урон по недостающему HP",
                   "fn": lambda s: 1.0 + LEG_MISSING_HP * (1.0 - _s(s, "hp_frac", 1.0))},
    "empty_hand": {"kind": "mult", "tier": "legendary", "channel": "damage", "klass": None,
                   "label": "Из пустой руки: ×урон",
                   "fn": lambda s: LEG_EMPTY_HAND if _s(s, "hand_after") == 0 else 1.0},

    # ── Легендарные ОБОРОННЫЕ/СУСТЕЙН (×mult — экспонента выживаемости `p`) ────
    "per_barrier": {"kind": "mult", "tier": "legendary", "channel": "shield", "klass": "Warrior",
                    "label": "×щит за стак Барьера",
                    "fn": lambda s: 1.0 + LEG_PER_BARRIER * _s(s, "barrier")},
    "last_stand":  {"kind": "mult", "tier": "legendary", "channel": "shield", "klass": "Berserker",
                    "label": "На грани: ×щит",
                    "fn": lambda s: LEG_LAST_STAND if _s(s, "hp_frac", 1.0) < LOW_HP_THRESHOLD else 1.0},
    "venomous_ward": {"kind": "mult", "tier": "legendary", "channel": "heal", "klass": "Druid",
                      "label": "×исцеление по стакам яда",
                      "fn": lambda s: 1.0 + LEG_VENOM_WARD * _s(s, "tgt_poison")},
    "lifebloom":   {"kind": "mult", "tier": "legendary", "channel": "heal", "klass": None,
                    "label": "×исцеление по недостающему HP",
                    "fn": lambda s: 1.0 + LEG_LIFEBLOOM * (1.0 - _s(s, "hp_frac", 1.0))},
}

# ─── ВЫБОР ТЕГА: класс × КАНАЛ КАРТЫ × тир (Smart Weighting §10.1) ─────────────
# Канал определяется ПРИРОДОЙ карты (атакующая → damage, щитовая → shield,
# лечащая → heal) — игрок строит ОБЕ оси, прокачивая разные карты. damage-теги
# класс-резонансны (идентичность); оборонные/сустейн — УНИВЕРСАЛЬНЫ (общая нужда
# выживаемости = ПОЛ потолка для всех, _upgrade_design.md §5).
CLASS_TAGS = {
    "Warrior":   {"early": "shielded", "legendary": "per_shield"},
    "Druid":     {"early": "poisoned", "legendary": "per_poison"},
    "Berserker": {"early": "low_hp",   "legendary": "missing_hp"},
    "Summoner":  {"early": "minions",  "legendary": "per_minion"},
    "Rogue":     {"early": "bleed",    "legendary": "per_bleed"},
    "Mage":      {"early": "combo",    "legendary": "per_combo"},
}
_GENERIC_TAGS = {"early": "first_card", "legendary": "empty_hand"}
# Универсальные оборонные/сустейн теги по каналу (не зависят от класса).
_SHIELD_TAGS = {"early": "bulwark",   "legendary": "per_barrier"}
_HEAL_TAGS   = {"early": "mending",   "legendary": "lifebloom"}
# Класс-специфичные оборонные легендарки (резонанс там, где он усиливает движок).
_CLASS_DEFENSE_LEG = {
    "Berserker": "last_stand",       # щит на грани крови
    "Druid":     "venomous_ward",    # сустейн от яда
}


def pick_tag(class_name: str, tier: str, channel: str = "damage") -> str:
    """Smart-weighted выбор тега для слота: тег данного тира и КАНАЛА. damage —
    резонансный классу (идентичность); shield/heal — универсальный оборонный,
    с класс-резонансной легендаркой там, где она усиливает движок (Берсерк/Друид).
    Детерминированно — модель «нужный тег всплыл в драфте из 3, бот его взял»."""
    if channel == "shield":
        if tier == "legendary" and class_name in _CLASS_DEFENSE_LEG \
                and TAGS[_CLASS_DEFENSE_LEG[class_name]]["channel"] == "shield":
            return _CLASS_DEFENSE_LEG[class_name]
        return _SHIELD_TAGS[tier]
    if channel == "heal":
        if tier == "legendary" and class_name in _CLASS_DEFENSE_LEG \
                and TAGS[_CLASS_DEFENSE_LEG[class_name]]["channel"] == "heal":
            return _CLASS_DEFENSE_LEG[class_name]
        return _HEAL_TAGS[tier]
    return CLASS_TAGS.get(class_name, _GENERIC_TAGS)[tier]


# ─── ДРАФТ ТЕГА: 1-из-3, вариант B3 (живая игра) ─────────────────────────────
# Юзер С54: на майлстоуне игрок ВЫБИРАЕТ тег из 3 (а не авто pick_tag). Пул —
# КРОСС-класс/условие в рамках КАНАЛА карты (мёртвые-по-каналу теги не лезут).
# B3: «чужие» условные теги (резонанс другого класса) НЕ вырезаются, а идут с
# НИЗКИМ весом — обманка возможна как осознанный риск рулетки, но и джекпот
# кросс-билда тоже (доктрина replayability-doctrine: рандом обязан кусаться).
# СИМ/baseline НЕ зовут draft_tag_choices (идут через pick_tag) → эталон не сдвинут.
DRAFT_WEIGHT_SELF      = 5    # тег-резонанс СВОЕГО класса — самый частый
DRAFT_WEIGHT_UNIVERSAL = 3    # универсальный тег (klass=None) — всегда уместен
DRAFT_WEIGHT_FOREIGN   = 1    # резонанс ЧУЖОГО класса — редкий риск/джекпот


def _draft_weight(spec, class_name: str) -> int:
    """Вес тега в драфте (B3): свой класс > универсальный > чужой класс."""
    klass = spec.get("klass")
    if klass == class_name:
        return DRAFT_WEIGHT_SELF
    if klass is None:
        return DRAFT_WEIGHT_UNIVERSAL
    return DRAFT_WEIGHT_FOREIGN


def _weighted_sample(items, weights, k, rng):
    """k уникальных элементов взвешенной выборкой БЕЗ повторов (чистая, тестируемая
    с seeded rng). Меньше k кандидатов → вернёт сколько есть."""
    pool = list(zip(items, weights))
    chosen = []
    for _ in range(min(k, len(pool))):
        total = sum(w for _, w in pool)
        r = rng.uniform(0, total)
        acc = 0.0
        for i, (it, w) in enumerate(pool):
            acc += w
            if r <= acc:
                chosen.append(it)
                pool.pop(i)
                break
    return chosen


def draft_tag_choices(class_name: str, tier: str, channel: str = "damage",
                      k: int = 3, rng=None) -> list:
    """Сгенерировать `k` тегов-кандидатов для драфта майлстоуна (B3). Кандидаты —
    теги данного ТИРА и КАНАЛА (живые на карте), кросс-класс; веса по _draft_weight
    (свой/универсальный/чужой). Без повторов. Если тегов канала < k — вернёт сколько
    есть (бедные каналы shield/heal — сигнал долить контент, не баг)."""
    if rng is None:
        import random
        rng = random
    pool = [(tag_id, spec) for tag_id, spec in TAGS.items()
            if spec["tier"] == tier and spec.get("channel", "damage") == channel]
    if not pool:
        return []
    items   = [tag_id for tag_id, _ in pool]
    weights = [_draft_weight(spec, class_name) for _, spec in pool]
    return _weighted_sample(items, weights, k, rng)


def _slot_value(spec, snapshot, grade):
    """Вклад одного слота с учётом Гипер-заряда (§4-bis). Возвращает ('add'|'mult',
    значение). grade масштабирует СИЛУ: add → добавка ×step^grade; mult → излишек
    над 1 ×step^grade (база 1.0 неприкосновенна, растёт только компаунд)."""
    raw  = spec["fn"](snapshot)
    step = OVERCHARGE_STEP ** grade if grade else 1.0
    if spec["kind"] == "add":
        return "add", raw * step
    return "mult", 1.0 + (raw - 1.0) * step


def forge_output_multiplier(slots, snapshot, channel: str = "damage") -> float:
    """Итоговый множитель ВЫХОДА данного канала от тегов карты: (1 + Σ add) × Π mult.
    Учитываются ТОЛЬКО слоты этого канала (damage/shield/heal). Аддитивные
    складываются (мягкий старт), мультипликативные перемножаются (компаунд),
    Гипер-заряд усиливает каждый (grade). Пустые/иноканальные слоты → 1.0."""
    if not slots:
        return 1.0
    add_sum   = 0.0
    mult_prod = 1.0
    for slot in slots:
        spec = TAGS.get(slot.get("tag_id"))
        if spec is None or spec.get("channel", "damage") != channel:
            continue
        kind, val = _slot_value(spec, snapshot, slot.get("grade", 0))
        if kind == "add":
            add_sum += val
        else:
            mult_prod *= val
    return (1.0 + add_sum) * mult_prod


def forge_damage_multiplier(slots, snapshot) -> float:
    """Совместимость: множитель канала УРОНА (см. forge_output_multiplier)."""
    return forge_output_multiplier(slots, snapshot, "damage")


def forge_effect_multiplier(combat_manager, player, channel: str) -> float:
    """Множитель тегов прокачки для НЕ-урон каналов (shield/heal), читаемый из
    эффектов карт (ShieldEffect/HealEffect/…). Берёт разыгрываемую карту + снимок
    с combat_manager (как damage-хук в EffectCalculator). Без ковки/карты/снимка →
    1.0 (инертно, регресс-нейтрально)."""
    if combat_manager is None or player is None:
        return 1.0
    card     = getattr(combat_manager, "_card_being_played", None)
    snapshot = getattr(combat_manager, "_play_snapshot", None)
    if card is None or snapshot is None:
        return 1.0
    rec = resolve_forge_record(card, player)
    if rec is None or not rec.get("slots"):
        return 1.0
    return forge_output_multiplier(rec["slots"], snapshot, channel)


def resolve_forge_record(card, player):
    """Паспорт ковки карты (§10.4). uid инстанса → запись в deck_forge_state.
    Временная копия (маска `{parent}_temp_{id}`) читает запись РОДИТЕЛЯ. Любая
    неопределённость → None (нет тегов, безопасно)."""
    state = getattr(player, "deck_forge_state", None)
    if not state:
        return None
    uid = getattr(card, "_fuid", None)
    if uid is None:
        return None
    rec = state.get(uid)
    if rec is None and isinstance(uid, str) and "_temp_" in uid:
        parent = uid.split("_temp_")[0]
        try:
            parent = int(parent)
        except (ValueError, TypeError):
            pass
        rec = state.get(parent)
    return rec
