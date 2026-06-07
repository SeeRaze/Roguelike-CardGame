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


def test_аскет_обрезает_колоду_и_бустит_урон():
    deck = list(range(15))                       # 15 «карт»
    gm = _gm(deck=deck)
    STAKES["ascetic"].activate(gm)
    assert len(gm.current_deck) == 10            # DECKBUILD-обрезка ≤10
    assert _hit(gm, 10) == 15                     # DAMAGE ×1.5


def test_аскет_не_трогает_короткую_колоду():
    deck = list(range(8))
    gm = _gm(deck=deck)
    STAKES["ascetic"].activate(gm)
    assert len(gm.current_deck) == 8             # уже ≤10 — без обрезки


def test_хрупкость_делит_макс_хп_и_бустит_урон():
    player = Creature("Игрок", 80, 80)
    gm = _gm(player=player)
    STAKES["fragile"].activate(gm)
    assert player.max_hp == 40                    # ½ макс. HP
    assert player.hp == 40                        # текущее клампится
    assert _hit(gm, 10) == 20                      # DAMAGE ×2


def test_активация_пушит_моды_в_стек():
    gm = _gm(deck=list(range(12)))
    STAKES["ascetic"].activate(gm)
    ids = [m.id for m in gm.rulestack.active()]
    assert "ascetic:trim" in ids and "ascetic:dmg" in ids


def test_две_ставки_не_дублируют_одноразовый_run_setup():
    """Регресс: активация второй Ставки НЕ должна повторно прогонять одноразовый
    DECKBUILD-мод первой (раньше Хрупкость урезала HP дважды → 90→45→22)."""
    player = Creature("Игрок", 90, 90)
    gm = _gm(deck=list(range(15)), player=player)
    STAKES["fragile"].activate(gm)            # 90 -> 45
    STAKES["ascetic"].activate(gm)            # не должна тронуть HP ещё раз
    assert player.max_hp == 45                # ровно ½, не ¼
    assert len(gm.current_deck) == 10         # Аскет обрезал один раз


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
