# tests/test_reward_manager.py
# Проверяем формирование наград после боя: золото / реликвия / ключ.
from types import SimpleNamespace
from managers.RewardManager import build_rewards
from core.rarity import Rarity
from core.relics import ALL_RELICS, ПроклятаяКорона


def _gm(relics=None, floor=5):
    """Минимальная заглушка GameManager для наград."""
    return SimpleNamespace(relics=relics if relics is not None else [], current_floor=floor)


def test_босс_даёт_редкую_реликвию_и_ключ():
    rewards = build_rewards(_gm(), is_boss=True, is_elite=False)
    types = [r["type"] for r in rewards]
    assert "key" in types
    assert "gold" in types       # короны нет -> золото есть
    relic = next(r for r in rewards if r["type"] == "relic")
    assert relic["value"].rarity == Rarity.RARE


def test_проклятая_корона_убирает_золото():
    rewards = build_rewards(_gm(relics=[ПроклятаяКорона()]), is_boss=True, is_elite=False)
    types = [r["type"] for r in rewards]
    assert "gold" not in types


def test_не_выпадает_уже_имеющаяся_реликвия():
    # У игрока уже все реликвии -> новой выпасть неоткуда.
    gm = _gm(relics=[r() for r in ALL_RELICS])
    rewards = build_rewards(gm, is_boss=True, is_elite=False)
    types = [r["type"] for r in rewards]
    assert "relic" not in types
    assert "key" in types        # ключ за босса всё равно есть


def test_золото_элиты_в_ожидаемом_диапазоне():
    # floor=5: база randint(20,35)+15, затем ×1.5 -> диапазон [52, 75].
    rewards = build_rewards(_gm(floor=5), is_boss=False, is_elite=True)
    gold = next(r for r in rewards if r["type"] == "gold")
    assert 52 <= gold["value"] <= 75
