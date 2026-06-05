# tests/test_damage_preview.py
# Аудит механик (Сессия 40): единый расчёт урона для UI. Превью на карте и
# проекция зовут тот же EffectCalculator, что и боевой удар — расхождений нет.
# Решение юзера: «гарантированное» число = детерминир. модификаторы; стихийные
# комбо и forge-теги — условные «реакции», показываются отдельными чипами.
from core.Creature import Creature
from core.cards.base import Card, DamageEffect
from core.EffectCalculator import EffectCalculator


def _atk(name, dmg):
    return Card(name=name, cost=1, card_type="attack",
                description=f"Урон {dmg}.", effects=[DamageEffect(dmg, dmg + 2)])


class _Combat:
    """Минимальный combat_manager для превью: игрок + снимок ковки."""
    def __init__(self, player, snapshot=None):
        self.player = player
        self._snapshot = snapshot
        self._card_being_played = None
        self._play_snapshot = None

    def add_log_message(self, _):
        pass

    def build_preview_snapshot(self, card, target):
        return self._snapshot if self._snapshot is not None else {}


class _GM:
    def __init__(self, relics):
        self.relics = relics
        self.stats = {"max_damage_dealt": 0}


# ─── Гарантированное число: баффы игрока + дебаффы врага входят ────────────────

def test_guaranteed_includes_player_buffs_and_enemy_debuffs():
    player = Creature("Игрок", 50, 50)
    player.mastery = 5          # +5 (Маг)
    player.atk_mult = 1.5       # ×1.5 (Заточка)
    target = Creature("Враг", 100, 100)
    target.vulnerable = 1       # ×1.5
    cm = _Combat(player)
    pv = EffectCalculator.preview(player, target, 10, combat_manager=cm)
    # (10 + 5 маст) ×1.5 уязв = 22 (int), ×1.5 Заточка = 33
    assert pv["guaranteed"] == 33
    assert pv["full"] == 33     # нет комбо/ковки → full == guaranteed
    assert pv["reactions"] == []


# ─── Комбо-реакция: в full входит, в guaranteed — нет, чип присутствует ────────

def test_combo_reaction_is_chip_not_in_guaranteed():
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    target.wet = 2
    target.ignited = 2          # ПАР ×3
    cm = _Combat(player)
    pv = EffectCalculator.preview(player, target, 10, combat_manager=cm)
    assert pv["guaranteed"] == 10          # без комбо
    assert pv["full"] == 30                # 10 ×3 ПАР
    assert pv["reactions"] == [{"name": "ПАР", "mult": 3.0}]
    # Превью НЕ расходует стаки стихий (нет побочек)
    assert target.wet == 2 and target.ignited == 2


# ─── Forge-тег: в full входит, в guaranteed — нет, форж-чип присутствует ───────

def test_forge_tag_is_chip_not_in_guaranteed():
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    card = _atk("Удар", 10)
    card._fuid = 1
    player.deck_forge_state = {1: {"level": 15, "slots": [{"tag_id": "empty_hand"}]}}
    cm = _Combat(player, snapshot={"hand_after": 0})   # пустая рука → ×2
    pv = EffectCalculator.preview(player, target, 10, combat_manager=cm, card=card)
    assert pv["guaranteed"] == 10
    assert pv["full"] == 20
    assert pv["forge_mult"] == 2.0
    assert pv["forge_tags"]            # есть подпись тега


# ─── Разбор (breakdown) для тултипа ───────────────────────────────────────────

def test_breakdown_lists_modifiers():
    player = Creature("Игрок", 50, 50)
    player.mastery = 3
    target = Creature("Враг", 100, 100)
    target.vulnerable = 1
    target.wet = 1
    target.ignited = 1
    cm = _Combat(player)
    pv = EffectCalculator.preview(player, target, 10, combat_manager=cm)
    labels = [label for (label, _kind, _val) in pv["steps"]]
    assert "Мастерство" in labels
    assert "Уязвимость" in labels
    assert "ПАР" in labels


# ─── Реликвия с одноразовым зарядом: превью НЕ тратит его ──────────────────────

def test_relic_one_shot_not_consumed_in_preview():
    from core.relics.advanced.damage import ЗаточенныйОсколок
    relic = ЗаточенныйОсколок()
    player = Creature("Игрок", 50, 50)
    target = Creature("Враг", 100, 100)
    cm = _Combat(player)
    gm = _GM([relic])
    pv = EffectCalculator.preview(player, target, 10, combat_manager=cm, game_manager=gm)
    assert pv["guaranteed"] == 13          # +3 от Осколка показан
    assert relic._used_this_combat is False  # но НЕ израсходован

    # А реальный удар (не dry_run) — расходует.
    dmg = EffectCalculator.calculate_damage(
        player, target, 10, game_manager=gm, combat_manager=cm)
    assert dmg == 13
    assert relic._used_this_combat is True


# ─── Заточка применяется и в превью (костыль в description.py больше не нужен) ──

def test_atk_mult_applies_in_dry_run():
    player = Creature("Игрок", 50, 50)
    player.atk_mult = 2.0
    target = Creature("Враг", 100, 100)
    cm = _Combat(player)
    dmg = EffectCalculator.calculate_damage(
        player, target, 10, combat_manager=cm, dry_run=True)
    assert dmg == 20
