# tests/test_stakes.py
# Ставки/Анте поверх RuleStack — первый контент слома (опт-ин сложность).
# Проверяем: активация пушит моды + одноразовый DECKBUILD; награда-урон идёт через
# сквозную DAMAGE-врезку EffectCalculator. Чистая логика, без pygame.
from types import SimpleNamespace

from core.rules import RuleStack, STAKES, Stake
from core.Creature import Creature
from core.EffectCalculator import EffectCalculator


def _gm(deck=None, player=None):
    """Минимальный gm для активации Ставки + расчёта урона."""
    return SimpleNamespace(
        rulestack=RuleStack(),
        current_deck=deck if deck is not None else [],
        player=player if player is not None else Creature("Игрок", 50, 50),
        relics=[], stats={},
    )


def _hit(gm, base=10):
    """Урон игрока по болванке через сквозной расчёт (учитывает DAMAGE-моды стека)."""
    target = Creature("Враг", 100, 100)
    cm = SimpleNamespace(player=gm.player, gm=gm, add_log_message=lambda _: None)
    return EffectCalculator.calculate_damage(gm.player, target, base,
                                             game_manager=gm, combat_manager=cm)


def test_реестр_содержит_аскета_и_хрупкость():
    assert "ascetic" in STAKES and "fragile" in STAKES
    assert all(isinstance(s, Stake) for s in STAKES.values())


def test_кровавый_кредит_открывает_долг_ресурсов():
    """Живая активация долга (§4): Ставка ставит флаги овердрафта на игрока →
    энергия и HP могут уходить в минус в реальном бою."""
    player = Creature("Игрок", 50, 50)
    gm = _gm(player=player)
    assert getattr(player, "energy_overdraft", False) is False   # до Ставки — выкл
    STAKES["blood_credit"].activate(gm)
    assert player.energy_overdraft is True
    assert player.hp_overdraft is True
    assert _hit(gm, 10) == 10                     # сам по себе урон не усилен (без минуса)


def test_кровавый_кредит_без_награды_урона_в_плюсе():
    """Кредит — ТОЛ, не бафф: в плюсе по ресурсам урон не меняется (множит лишь долг)."""
    player = Creature("Игрок", 50, 50)
    gm = _gm(player=player)
    STAKES["blood_credit"].activate(gm)
    player.hp = -2                                # ушёл в долг HP → теперь множитель
    assert _hit(gm, 10) == 12                     # ×1.20 от глубины долга, не от Ставки


def test_аскет_обрезает_колоду_без_урон_награды():
    """Калибровка С46: Аскет = чистая обрезка ≤6, БЕЗ урон-награды (true ascension)."""
    deck = list(range(15))                       # 15 «карт»
    gm = _gm(deck=deck)
    STAKES["ascetic"].activate(gm)
    assert len(gm.current_deck) == 6             # DECKBUILD-обрезка ≤6
    assert _hit(gm, 10) == 10                     # урон НЕ усилен (награда = Энтропия позже)


def test_аскет_не_трогает_короткую_колоду():
    deck = list(range(5))
    gm = _gm(deck=deck)
    STAKES["ascetic"].activate(gm)
    assert len(gm.current_deck) == 5             # уже ≤6 — без обрезки


def test_хрупкость_режет_хп_и_частично_бустит_урон():
    player = Creature("Игрок", 80, 80)
    gm = _gm(player=player)
    STAKES["fragile"].activate(gm)
    assert player.max_hp == 24                     # 30% макс. HP
    assert player.hp == 24                         # текущее клампится
    assert _hit(gm, 10) == 12                      # DAMAGE ×1.25 (int(12.5))


def test_активация_пушит_моды_в_стек():
    gm = _gm(deck=list(range(12)))
    STAKES["ascetic"].activate(gm)
    ids = [m.id for m in gm.rulestack.active()]
    assert "ascetic:trim" in ids              # Аскет = только обрезка (без :dmg)
    assert "ascetic:dmg" not in ids


def test_две_ставки_не_дублируют_одноразовый_run_setup():
    """Регресс: активация второй Ставки НЕ должна повторно прогонять одноразовый
    DECKBUILD-мод первой (раньше Хрупкость урезала HP дважды → 90→27→8)."""
    player = Creature("Игрок", 90, 90)
    gm = _gm(deck=list(range(15)), player=player)
    STAKES["fragile"].activate(gm)            # 90 -> 27 (30%)
    STAKES["ascetic"].activate(gm)            # не должна тронуть HP ещё раз
    assert player.max_hp == 27                # ровно 30%, не повторно
    assert len(gm.current_deck) == 6          # Аскет обрезал один раз ≤6


def test_награда_урона_только_для_атак_игрока():
    """DAMAGE-мод Ставки не множит урон врага по игроку (predicate is_player_attack)."""
    player = Creature("Игрок", 80, 80)
    enemy  = Creature("Враг", 50, 50)
    gm = _gm(player=player)
    STAKES["fragile"].activate(gm)
    cm = SimpleNamespace(player=player, gm=gm, add_log_message=lambda _: None)
    dmg = EffectCalculator.calculate_damage(enemy, player, 10,
                                            game_manager=gm, combat_manager=cm)
    assert dmg == 10                              # удар врага не усилен Ставкой
