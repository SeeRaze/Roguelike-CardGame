# tests/test_detonations.py
# Фундамент детонационных комбо: DetonationRegistry + DetonateEffect.
# Детонации — мгновенный эффект (бурст/AoE), в отличие от множительных комбо.
from core.DetonationRegistry import (
    DETONATIONS, all_detonations, ELECTRO_DAMAGE_PER_SHOCK, _electro_blast,
)
from core.cards.base import DetonateEffect
from core.Creature import Creature


# ═══════════════════════════════════════════════════════════
# Реестр
# ═══════════════════════════════════════════════════════════

def test_реестр_содержит_электро_взрыв():
    det = DETONATIONS.get("electro_blast")
    assert det is not None
    assert det["requires"] == ("wet", "shock")
    assert callable(det["handler"])
    assert "ЭЛЕКТРО-ВЗРЫВ" in det["name"]


def test_all_detonations_возвращает_тот_же_словарь():
    assert all_detonations() is DETONATIONS


# ═══════════════════════════════════════════════════════════
# Хендлер Электро-взрыва
# ═══════════════════════════════════════════════════════════

def test_электро_взрыв_бьёт_по_шоку_и_снимает_статусы(make_combat):
    target = Creature("Цель", 50, 50)
    target.wet = 2
    target.shock = 3
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    burst = _electro_blast(target, cm)
    assert burst == 3 * ELECTRO_DAMAGE_PER_SHOCK     # 18
    assert target.hp == 32                           # 50 - 18
    assert target.wet == 0 and target.shock == 0     # статусы потрачены


def test_электро_взрыв_aoe_по_всем_врагам(make_combat):
    target = Creature("Цель", 50, 50)
    other  = Creature("Враг2", 50, 50)
    target.wet = 1
    target.shock = 2
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    cm.enemies = [target, other]
    _electro_blast(target, cm)
    burst = 2 * ELECTRO_DAMAGE_PER_SHOCK             # 12
    assert target.hp == 50 - burst
    assert other.hp == 50 - burst                    # AoE задел второго


# ═══════════════════════════════════════════════════════════
# DetonateEffect — триггер
# ═══════════════════════════════════════════════════════════

def test_детонатор_срабатывает_при_мокром_и_шоке(make_combat):
    target = Creature("Цель", 50, 50)
    target.wet = 1
    target.shock = 2
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    DetonateEffect().execute(cm.player, target, cm, is_upgraded=False)
    assert target.hp == 50 - 2 * ELECTRO_DAMAGE_PER_SHOCK
    assert target.wet == 0 and target.shock == 0


def test_детонатор_молчит_без_полного_набора(make_combat):
    # Только Шок, без Мокрого → детонация не срабатывает.
    target = Creature("Цель", 50, 50)
    target.shock = 3
    cm = make_combat(player=Creature("Игрок", 50, 50), enemy=target)
    DetonateEffect().execute(cm.player, target, cm, is_upgraded=False)
    assert target.hp == 50                           # урона нет
    assert target.shock == 3                          # статус на месте


def test_детонатор_без_боя_не_падает():
    target = Creature("Цель", 50, 50)
    target.wet = 1
    target.shock = 1
    DetonateEffect().execute(None, target, None, is_upgraded=False)   # не бросает
    assert target.hp == 50
