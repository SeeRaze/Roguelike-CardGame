# tests/conftest.py
# Общая настройка для всех тестов + переиспользуемые «заготовки» (фикстуры).
#
# Что здесь происходит:
#  1) Включаем headless-режим pygame ДО его импорта — окно не открывается, тесты идут в CI.
#  2) Даём фикстуры: создать существо, создать «ненастоящий бой» (замену CombatManager),
#     чтобы тестировать боевую логику без запуска целого боя.
import os

# Pygame не должен открывать настоящее окно/звук во время тестов.
# setdefault — не перетираем, если переменная уже задана снаружи.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYTHONUTF8", "1")

import pytest
from core.Creature import Creature


class FakeGM:
    """Очень простая замена GameManager: хранит только то, к чему обращается боевая логика."""
    def __init__(self, relics=None):
        self.relics = relics if relics is not None else []
        self.stats = {"max_damage_dealt": 0}


class FakeCombat:
    """Лёгкая замена CombatManager для юнит-тестов статусов/реликвий.

    Содержит ровно те поля, которые читает код в Creature/реликвиях:
    player, enemy, gm (с relics/stats), флаги боя и метод записи в лог.
    Реальный бой запускать не нужно — это быстрее и проще для проверки одной механики.
    """
    def __init__(self, player, enemy, relics=None):
        self.player = player
        self.enemy = enemy          # compat (старые тесты читают .enemy)
        self.enemies = [enemy]      # новый код проверяет self in cm.enemies
        self.gm = FakeGM(relics)
        self._elemental_blocked = False
        self._combo_triggered = False
        self.log = []          # сюда складываются сообщения боевого лога

    def add_log_message(self, message):
        self.log.append(message)

    def get_target_enemy(self):
        """Первый живой враг (как в CombatManager) — для авто-таргетинга."""
        for e in self.enemies:
            if e.hp > 0:
                return e
        return None


@pytest.fixture
def make_creature():
    """Фикстура-фабрика: создать существо с нужными HP.
    Пример в тесте: c = make_creature(hp=30)"""
    def _make(name="Цель", hp=50, max_hp=50):
        return Creature(name, hp, max_hp)
    return _make


@pytest.fixture
def make_combat(make_creature):
    """Фикстура-фабрика: создать «ненастоящий бой» (FakeCombat).
    Можно передать своих player/enemy/relics, иначе создаются базовые существа.
    Пример: cm = make_combat(relics=[ФлаконСЖелчью()])"""
    def _make(player=None, enemy=None, relics=None):
        player = player if player is not None else make_creature("Игрок", 50, 50)
        enemy  = enemy  if enemy  is not None else make_creature("Враг", 50, 50)
        return FakeCombat(player, enemy, relics)
    return _make
