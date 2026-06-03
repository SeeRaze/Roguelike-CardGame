# managers/RewardManager.py
# Расчёт списка наград за победу: золото, реликвия (бросок редкости), ключ.
# Чистая логика — читает состояние gm, возвращает список наград-словарей.
import random
from core.relics import RELIC_POOL, ALL_RELICS
from core.rarity import Rarity


def _roll_relic_rarity(is_boss: bool, is_elite: bool) -> Rarity:
    """Редкость выпадающей реликвии по типу боя."""
    if is_boss:
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
    """Выбрать новую (ещё не имеющуюся) реликвию заданной редкости."""
    # Берём пул под нужную редкость; если пуст — смотрим все реликвии этой редкости
    pool = RELIC_POOL.get(rarity, [])
    if not pool:
        pool = [r for r in ALL_RELICS if r().rarity == rarity]

    current_names    = {r.name for r in gm.relics}
    available_relics = [r for r in pool if r().name not in current_names]

    # Фоллбэк: если в пуле нужной редкости ничего не осталось — ищем среди ВСЕХ
    if not available_relics:
        available_relics = [r for r in ALL_RELICS if r().name not in current_names]

    if not available_relics:
        return None
    return random.choice(available_relics)()


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
        rarity    = _roll_relic_rarity(is_boss, is_elite)
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
