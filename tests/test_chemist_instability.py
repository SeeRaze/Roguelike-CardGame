# tests/test_chemist_instability.py
# Card Fusion этап 3 (С51), ПАССИВ «Нестабильность»: +1 за каждый фьюжн за бой,
# стак даёт +N к урону ТОЛЬКО Глитч-карт (is_fused), сброс между боями.

from core.EffectCalculator import EffectCalculator
from core.players import Chemist, Warrior
from core.enemies.cultist import Cultist
from core.cards import create_strike, create_ignite, create_defend
from managers.CombatManager import CombatManager


def _cm(player, deck=None):
    d = deck if deck is not None else [create_strike(), create_strike(), create_defend()]
    return CombatManager(player, Cultist("K", 80, 80), d)


class _Fused:
    is_fused = True


class _Plain:
    is_fused = False


# ── накопление статуса ─────────────────────────────────────────────────────────────

def test_фьюжн_растит_нестабильность():
    cm = _cm(Chemist(), deck=[create_strike(), create_ignite(), create_defend()])
    cm.player.reagent = 9
    assert cm.player.instability == 0
    cm.fuse_hand_cards(0, 1)
    assert cm.player.instability == 1


def test_нестабильность_сбрасывается_между_боями():
    c = Chemist()
    c.add_status("instability", 4)
    c.reagent = 3
    assert c.instability == 4
    c.reset_combat_statuses()
    assert c.instability == 0
    assert c.reagent == 0   # внутрибоевой ресурс тоже обнуляется


# ── математика бонуса (через EffectCalculator) ─────────────────────────────────────

def test_бонус_только_глитч_картам():
    cm = _cm(Chemist())
    e = cm.enemies[0]
    cm.player.statuses["instability"] = 3
    fused = EffectCalculator.calculate_damage(
        cm.player, e, 6, combat_manager=cm, card_override=_Fused(), dry_run=True)
    plain = EffectCalculator.calculate_damage(
        cm.player, e, 6, combat_manager=cm, card_override=_Plain(), dry_run=True)
    assert fused == 9      # 6 + 3 нестабильности
    assert plain == 6      # обычной карте бонуса нет


def test_нестабильность_ноль_инертна():
    cm = _cm(Chemist())
    e = cm.enemies[0]
    cm.player.statuses["instability"] = 0
    dmg = EffectCalculator.calculate_damage(
        cm.player, e, 6, combat_manager=cm, card_override=_Fused(), dry_run=True)
    assert dmg == 6


def test_бонус_не_у_не_химика():
    # Нестабильность — статус; у Воина его 0 → шаг инертен (никто не растит).
    cm = _cm(Warrior())
    e = cm.enemies[0]
    assert cm.player.instability == 0
    dmg = EffectCalculator.calculate_damage(
        cm.player, e, 6, combat_manager=cm, card_override=_Fused(), dry_run=True)
    assert dmg == 6


def test_бонус_масштабируется_со_стаком():
    cm = _cm(Chemist())
    e = cm.enemies[0]
    cm.player.statuses["instability"] = 5
    dmg = EffectCalculator.calculate_damage(
        cm.player, e, 10, combat_manager=cm, card_override=_Fused(), dry_run=True)
    assert dmg == 15   # 10 + 5


# ── интеграция: фьюжн → розыгрыш Глитча с бонусом ──────────────────────────────────

def test_сыгранный_глитч_получает_бонус_нестабильности():
    cm = _cm(Chemist(), deck=[create_strike(), create_strike(), create_defend()])
    cm.player.reagent = 9
    # Сливаем ДВА Удара детерминированно (рука тасуется) → Глитч с одним DamageEffect
    # на каждый Удар. Находим их индексы по имени.
    hand = cm.deck_manager.hand
    strike_idxs = [i for i, c in enumerate(hand) if c.name == "Удар"]
    assert len(strike_idxs) >= 2
    cm.fuse_hand_cards(strike_idxs[0], strike_idxs[1])
    assert cm.player.instability == 1
    glitch = next(c for c in cm.deck_manager.hand if getattr(c, "is_fused", False))
    cm.enemies[0].shield = 0   # снести щит врага, чтобы урон шёл в HP без шума
    hp0 = cm.enemies[0].hp
    cm.play_card_by_index(cm.deck_manager.hand.index(glitch))
    dealt = hp0 - cm.enemies[0].hp
    # Глитч из двух Ударов = два DamageEffect (6 каждый), нестабильность +1 на КАЖДЫЙ
    # удар игрока → 2×(6+1) = 14.
    assert dealt == 2 * (6 + 1)
