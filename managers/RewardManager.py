# managers/RewardManager.py
# Расчёт списка наград за победу: золото, реликвия (бросок редкости), ключ.
# Чистая логика — читает состояние gm, возвращает список наград-словарей.
import random
from core.relics import RELIC_POOL, ALL_RELICS
from core.rarity import Rarity
from core.progression import is_relic_unlocked, relic_id_for


def _roll_relic_rarity(is_boss: bool, is_elite: bool, floor: int = 0) -> Rarity:
    """Редкость выпадающей реликвии по типу боя.

    Боссы — единственный источник EPIC/LEGENDARY (раньше они вообще не выпадали:
    дроп упирался в RARE, и флагманы `Корона Вознесения`/`Проклятая Корона` были
    недостижимы вне симулятора). Лестница привязана к этажу босса (20/40/60/80/100):
      floor < 40  → RARE                       (босс акта 1)
      floor ≥ 40  → EPIC (шанс) / иначе RARE    (акт 2+)
      floor ≥ 60  → LEGENDARY (шанс) / EPIC / RARE (акт 3+)
    Проценты ниже — тюнинг-ручки (старт-калибровка)."""
    if is_boss:
        roll = random.random()
        if floor >= 60 and roll < 0.40:
            return Rarity.LEGENDARY
        if floor >= 40 and roll < 0.50:
            return Rarity.EPIC
        return Rarity.RARE
    if is_elite:
        return Rarity.RARE if random.random() < 0.25 else Rarity.UNCOMMON
    roll = random.random()
    if roll < 0.60:
        return Rarity.COMMON
    if roll < 0.90:
        return Rarity.UNCOMMON
    return Rarity.RARE


def _pick_relic(gm, rarity: Rarity):
    """Выбрать новую (ещё не имеющуюся) реликвию заданной редкости.

    Узкий стартовый пул (С57): locked-артефакты (не в meta['unlocks']) НЕ выпадают —
    открываются за достижения ([[capstone-reorder-content-first]]). meta берём с gm
    (getattr-страховка: нет меты → None → is_relic_unlocked отдаёт только стартовые)."""
    # meta=None → без фильтра (как get_pool_for_class: обр. совместимость для тестов/
    # путей без меты). Live gm всегда несёт meta → стартовый пул реально сужается.
    meta = getattr(gm, "meta", None)

    def _ok(r):
        if r().name in current_names:
            return False
        return meta is None or is_relic_unlocked(meta, relic_id_for(r))

    # Берём пул под нужную редкость; если пуст — смотрим все реликвии этой редкости
    pool = RELIC_POOL.get(rarity, [])
    if not pool:
        pool = [r for r in ALL_RELICS if r().rarity == rarity]

    current_names    = {r.name for r in gm.relics}
    available_relics = [r for r in pool if _ok(r)]

    # Фоллбэк: если в пуле нужной редкости ничего не осталось — ищем среди ВСЕХ
    if not available_relics:
        available_relics = [r for r in ALL_RELICS if _ok(r)]

    if not available_relics:
        return None
    return random.choice(available_relics)()


def pick_shop_relic(gm):
    """Реликвия для витрины магазина: редкость как у обычного боя (средние/слабые,
    см. _roll_relic_rarity), фильтр уже имеющихся. Возвращает инстанс или None
    (если все реликвии уже собраны). Логика реликвий — единым источником здесь."""
    rarity = _roll_relic_rarity(is_boss=False, is_elite=False)
    return _pick_relic(gm, rarity)


def build_rewards(gm, is_boss: bool, is_elite: bool) -> list:
    """Сформировать список наград за победу.

    Состав:
      - золото (исчезает при «Проклятой Короне»), элита x1.5;
      - реликвия: 100% за элиту/босса, иначе 50%, редкость по типу боя;
      - ключ от сундука: только за босса.
    """
    rewards = []

    # --- Золото ---
    has_crown = any(r.name == "Проклятая Корона" for r in gm.relics)
    if not has_crown:
        gold_drop = random.randint(20, 35) + (gm.current_floor * 3)
        if is_elite:
            gold_drop = int(gold_drop * 1.5)
        rewards.append({
            "type": "gold", "label": f"+{gold_drop} монет",
            "value": gold_drop, "applied": False,
        })

    # --- Реликвия ---
    relic_chance = True if (is_boss or is_elite) else random.randint(1, 2) == 1
    if relic_chance:
        rarity    = _roll_relic_rarity(is_boss, is_elite, gm.current_floor)
        new_relic = _pick_relic(gm, rarity)
        if new_relic is not None:
            rewards.append({
                "type": "relic",
                "label": f"Артефакт [{rarity.value}]: {new_relic.name}",
                "value": new_relic, "applied": False,
            })

    # --- Ключ от сундука (только босс) ---
    if is_boss:
        rewards.append({
            "type": "key", "label": "Ключ от сундука",
            "value": 1, "applied": False,
        })

    return rewards
