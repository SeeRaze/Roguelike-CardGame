# tests/test_game_manager.py
# Проверяем «мозг» игры (GameManager): цена сжигания карты, добавление карты,
# спавн боя и раздача наград-фасады (делегируют в EnemySpawner/RewardManager).
from managers.GameManager import GameManager
from core.cards import create_strike
from core.relics import ПроклятаяКорона


def test_цена_сжигания_по_формуле():
    gm = GameManager()
    gm.current_floor = 1
    gm.removal_count = 0
    # (15 + floor*2) + removal_count*25 = 17
    assert gm.get_removal_price() == 17


def test_проклятая_корона_удваивает_цену_сжигания():
    gm = GameManager()
    gm.current_floor = 1
    gm.removal_count = 0
    gm.relics.append(ПроклятаяКорона())
    assert gm.get_removal_price() == 34


def test_добавление_карты_в_колоду():
    gm = GameManager()
    было = len(gm.current_deck)
    gm.add_card(create_strike())
    assert len(gm.current_deck) == было + 1


def test_спавн_создаёт_активный_бой():
    gm = GameManager()
    gm.current_floor = 2
    gm.spawn_procedural_enemy()
    assert gm.active_combat is not None
    assert gm.active_combat.enemy is not None


def test_раздача_наград_переводит_в_экран_победы():
    gm = GameManager()
    gm.current_floor = 2
    gm.spawn_procedural_enemy()
    gm.current_state = "COMBAT"
    gm.distribute_combat_rewards()
    assert isinstance(gm.pending_rewards, list)
    assert gm.current_state == "VICTORY"
