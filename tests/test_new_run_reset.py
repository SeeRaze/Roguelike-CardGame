# tests/test_new_run_reset.py
# Фикс бага «перенос состояния между забегами»: новый забег = с нуля.
# GameManager.reset_for_new_run пересоздаёт игрока выбранного класса + стартовую
# колоду, обнуляет экономику/статы забега, чистит RuleStack и per-run баны.
# Тестируем метод на лёгком стенде (без полного GameManager → без чтения меты с диска).

from types import SimpleNamespace

from managers.GameManager import GameManager
from core.players import Warrior, Mage
from core.rules import RuleStack
from core.rules.RuleStack import RuleMod, Scope


def _dirty_gm(cls=Warrior):
    """gm-стенд, загрязнённый «как после прошлого забега»."""
    player = cls()
    player.max_hp = 999
    player.forge_points = 77
    rs = RuleStack()
    rs.push(RuleMod("stale", "осталось", Scope.DAMAGE))
    return SimpleNamespace(
        player=player, player_name="Тестер",
        current_deck=[], player_gold=3, player_keys=9,
        removal_count=5, temper_count=4,
        relics=["накопленная_реликвия"], run_banned_tags=["x"],
        rulestack=rs, active_combat="stale_combat", current_floor=42,
        stats={"name": "Тестер", "max_floor": 42, "monsters_killed": 99,
               "bosses_killed": 7, "max_damage_dealt": 500},
    )


def test_economy_and_counts_reset():
    gm = _dirty_gm()
    GameManager.reset_for_new_run(gm)
    assert gm.player_gold == 100
    assert gm.player_keys == 0
    assert gm.removal_count == 0
    assert gm.temper_count == 0
    assert gm.relics == []
    assert gm.run_banned_tags == []
    assert gm.current_floor == 1
    assert gm.active_combat is None


def test_player_recreated_fresh_same_class():
    gm = _dirty_gm(Warrior)
    GameManager.reset_for_new_run(gm)
    assert isinstance(gm.player, Warrior)          # класс сохранён
    assert gm.player.max_hp != 999                 # свежий max_hp класса
    assert gm.player.forge_points == 0             # forge сброшен
    assert gm.player.hp == gm.player.max_hp or gm.player.hp > 0


def test_class_preserved_for_mage():
    gm = _dirty_gm(Mage)
    GameManager.reset_for_new_run(gm)
    assert isinstance(gm.player, Mage)


def test_starter_deck_rebuilt_with_uids():
    gm = _dirty_gm()
    GameManager.reset_for_new_run(gm)
    assert len(gm.current_deck) > 0                # стартовая колода восстановлена
    # Каждой карте проставлен паспорт ковки (uid).
    assert all(getattr(c, "_fuid", None) is not None for c in gm.current_deck)


def test_rulestack_and_stats_cleared():
    gm = _dirty_gm()
    GameManager.reset_for_new_run(gm)
    assert gm.rulestack.active() == []
    assert gm.stats["max_floor"] == 1
    assert gm.stats["monsters_killed"] == 0
    assert gm.stats["bosses_killed"] == 0
    assert gm.stats["max_damage_dealt"] == 0
    assert gm.stats["name"] == "Тестер"            # имя сохранено
