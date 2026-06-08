# tests/test_bot_berserker_policy.py
# Бот-политика Берсерка (managers/balance/policy.py): «Безумие» = ставка ДИСПЕРСИИ.
# Компетентный пилот ныряет в минус ТОЛЬКО когда сошлись оба условия: полный буфер HP
# (пережить нырок) И добиваемый залп (нырок окупится киллом). Слепой газ@0.6 был
# суицидом-ловушкой и занижал класс (см. balance-findings-berserker-glasscannon).
from core.players import Berserker
from managers.balance.policy import (
    BerserkerPolicy, _BERSERK_HP_FRACTION, _BERSERK_KILLABLE_RATIO,
)


def _setup(make_combat, make_creature, hp, enemy_hp):
    """Берсерк с заданным HP против врага с заданным HP. madness_active сброшен."""
    p = Berserker()
    p.hp = hp
    p.madness_active = False
    enemy = make_creature("Враг", enemy_hp, enemy_hp)
    return p, make_combat(player=p, enemy=enemy)


def test_газ_жмётся_полный_буфер_и_добиваемый_залп(make_combat, make_creature):
    # HP ≥ 0.9·max И суммарный HP врагов ≤ 0.6·max → ныряем (ставка окупаема).
    p, cm = _setup(make_combat, make_creature,
                   hp=60, enemy_hp=int(60 * _BERSERK_KILLABLE_RATIO) - 1)
    BerserkerPolicy().on_turn_begin(cm)
    assert p.madness_active is True


def test_газ_не_жмётся_буфер_низкий(make_combat, make_creature):
    # HP ниже порога буфера → нырок не пережить → НЕ ныряем (хотя залп добиваем).
    low = int(60 * _BERSERK_HP_FRACTION) - 1
    p, cm = _setup(make_combat, make_creature, hp=low, enemy_hp=10)
    BerserkerPolicy().on_turn_begin(cm)
    assert p.madness_active is False


def test_газ_не_жмётся_залп_слишком_толстый(make_combat, make_creature):
    # Полный буфер, но суммарный HP врагов > 0.6·max → нырок не окупится → НЕ ныряем.
    p, cm = _setup(make_combat, make_creature,
                   hp=60, enemy_hp=int(60 * _BERSERK_KILLABLE_RATIO) + 5)
    BerserkerPolicy().on_turn_begin(cm)
    assert p.madness_active is False


def test_газ_не_жмётся_враги_мертвы(make_combat, make_creature):
    # Все враги мертвы (enemy_hp==0) → нырять незачем → НЕ ныряем (нет цели окупить).
    p, cm = _setup(make_combat, make_creature, hp=60, enemy_hp=10)
    for e in cm.enemies:
        e.hp = 0
    BerserkerPolicy().on_turn_begin(cm)
    assert p.madness_active is False
