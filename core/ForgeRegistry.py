# core/ForgeRegistry.py
# СЕССИЯ 39, шаг 39.2 — условные теги прокачки карт (см. _upgrade_design.md §4-5,10).
# Data-driven реестр предикатов (как DetonationRegistry/ComboRegistry). Тег = слот,
# открытый майлстоуном карты (5/10/15). Ранние теги дают АДДИТИВНЫЙ +mult (мягкий
# старт), легендарные — МУЛЬТИПЛИКАТИВНЫЙ ×mult (истинный компаунд кат.4).
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
LEG_PER_SHIELD     = 0.01   # за единицу щита/барьера (Воин, Барьер)
LEG_PER_COMBO      = 0.08   # за накопленное Мастерство (Маг, комбо)
LEG_MISSING_HP     = 1.00   # ×(1 + доля недостающего HP) (Берсерк)


def _s(snapshot, key, default=0):
    """Null-safe чтение снимка (§10.7): нет снимка/ключа → дефолт."""
    if not snapshot:
        return default
    return snapshot.get(key, default)


# ─── РЕЕСТР ТЕГОВ ─────────────────────────────────────────────────────────────
# Каждый тег: kind ('add'|'mult'), tier ('early'|'legendary'), klass (резонанс),
# label (для UI/глоссария), fn(snapshot) -> вклад:
#   add  → аддитивная добавка к множителю (0.0, если условие не выполнено);
#   mult → множитель ≥1.0 (1.0, если условие не выполнено).
TAGS = {
    # ── Ранние (+mult, аддитивные) ──────────────────────────────────────────
    "shielded":   {"kind": "add", "tier": "early", "klass": "Warrior",
                   "label": "Под щитом: +урон",
                   "fn": lambda s: EARLY_ADD if (_s(s, "shield") + _s(s, "barrier")) > 0 else 0.0},
    "poisoned":   {"kind": "add", "tier": "early", "klass": "Druid",
                   "label": "По отравленной цели: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "tgt_poison") > 0 else 0.0},
    "low_hp":     {"kind": "add", "tier": "early", "klass": "Berserker",
                   "label": "На низком HP: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "hp_frac", 1.0) < 0.5 else 0.0},
    "minions":    {"kind": "add", "tier": "early", "klass": "Summoner",
                   "label": "При миньонах: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "minions") > 0 else 0.0},
    "bleed":      {"kind": "add", "tier": "early", "klass": "Rogue",
                   "label": "По кровоточащей цели: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "tgt_bleed") > 0 else 0.0},
    "combo":      {"kind": "add", "tier": "early", "klass": "Mage",
                   "label": "После комбо: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "mastery") > 0 else 0.0},
    "first_card": {"kind": "add", "tier": "early", "klass": None,
                   "label": "Первой картой за ход: +урон",
                   "fn": lambda s: EARLY_ADD if _s(s, "play_index") == 0 else 0.0},

    # ── Легендарные (×mult, истинный компаунд) ────────────────────────────────
    "per_minion": {"kind": "mult", "tier": "legendary", "klass": "Summoner",
                   "label": "×урон за каждого миньона",
                   "fn": lambda s: 1.0 + LEG_PER_MINION * _s(s, "minions")},
    "per_poison": {"kind": "mult", "tier": "legendary", "klass": "Druid",
                   "label": "×урон по стакам яда",
                   "fn": lambda s: 1.0 + LEG_PER_POISON * _s(s, "tgt_poison")},
    "per_bleed":  {"kind": "mult", "tier": "legendary", "klass": "Rogue",
                   "label": "×урон по стакам кровотечения",
                   "fn": lambda s: 1.0 + LEG_PER_BLEED * _s(s, "tgt_bleed")},
    "per_shield": {"kind": "mult", "tier": "legendary", "klass": "Warrior",
                   "label": "×урон по щиту/барьеру",
                   "fn": lambda s: 1.0 + LEG_PER_SHIELD * (_s(s, "shield") + _s(s, "barrier"))},
    "per_combo":  {"kind": "mult", "tier": "legendary", "klass": "Mage",
                   "label": "×урон по Мастерству",
                   "fn": lambda s: 1.0 + LEG_PER_COMBO * _s(s, "mastery")},
    "missing_hp": {"kind": "mult", "tier": "legendary", "klass": "Berserker",
                   "label": "×урон по недостающему HP",
                   "fn": lambda s: 1.0 + LEG_MISSING_HP * (1.0 - _s(s, "hp_frac", 1.0))},
    "empty_hand": {"kind": "mult", "tier": "legendary", "klass": None,
                   "label": "Из пустой руки: ×урон",
                   "fn": lambda s: LEG_EMPTY_HAND if _s(s, "hand_after") == 0 else 1.0},
}

# Класс → резонансный тег по тиру (Smart Weighting §10.1: «родственный билду»
# всплывает в драфте, бот его берёт). Фолбэк — generic (None-класс).
CLASS_TAGS = {
    "Warrior":   {"early": "shielded", "legendary": "per_shield"},
    "Druid":     {"early": "poisoned", "legendary": "per_poison"},
    "Berserker": {"early": "low_hp",   "legendary": "missing_hp"},
    "Summoner":  {"early": "minions",  "legendary": "per_minion"},
    "Rogue":     {"early": "bleed",    "legendary": "per_bleed"},
    "Mage":      {"early": "combo",    "legendary": "per_combo"},
}
_GENERIC_TAGS = {"early": "first_card", "legendary": "empty_hand"}


def pick_tag(class_name: str, tier: str) -> str:
    """Smart-weighted выбор тега для слота: резонансный классу тег данного тира
    (детерминированно — модель «нужный тег всплыл в драфте из 3, бот его взял»)."""
    return CLASS_TAGS.get(class_name, _GENERIC_TAGS)[tier]


def forge_damage_multiplier(slots, snapshot) -> float:
    """Итоговый множитель урона карты от её тегов: (1 + Σ ранних add) × Π легенд.
    Аддитивные складываются (мягкий старт), мультипликативные перемножаются
    (компаунд). Пустые слоты → 1.0 (регресс-нейтрально)."""
    if not slots:
        return 1.0
    add_sum = 0.0
    mult_prod = 1.0
    for slot in slots:
        spec = TAGS.get(slot.get("tag_id"))
        if spec is None:
            continue
        v = spec["fn"](snapshot)
        if spec["kind"] == "add":
            add_sum += v
        else:
            mult_prod *= v
    return (1.0 + add_sum) * mult_prod


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
