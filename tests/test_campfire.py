# tests/test_campfire.py
# Юнит-тесты core-хелперов Костра (Creature.lose_hp / rest_heal_amount).
# Сам UI костра (ui/Campfire.py) — pygame-слой, логику держим в core и тестируем тут.
from core.Creature import Creature


# ═══════════════════════════════════════════════════════════════════
# lose_hp -- прямой урон СКВОЗЬ ЩИТ (Ритуал крови, Проклятый сундук)
# ═══════════════════════════════════════════════════════════════════
def test_lose_hp_бьёт_сквозь_щит_не_трогая_броню():
    c = Creature("Цель", 50, 50)
    c.shield = 20
    lost = c.lose_hp(10)
    assert lost == 10
    assert c.hp == 40        # урон ушёл прямо в HP
    assert c.shield == 20    # щит не тронут


def test_lose_hp_клампится_в_ноль_не_уходит_в_минус():
    c = Creature("Цель", 5, 50)
    lost = c.lose_hp(10)
    assert lost == 5         # списали лишь сколько было
    assert c.hp == 0


def test_lose_hp_ноль_и_отрицательное_безопасны():
    c = Creature("Цель", 30, 50)
    assert c.lose_hp(0) == 0
    assert c.lose_hp(-7) == 0
    assert c.hp == 30        # HP не изменилось


# ═══════════════════════════════════════════════════════════════════
# rest_heal_amount -- «Отдых»: 30% от НЕДОСТАЮЩЕГО HP
# ═══════════════════════════════════════════════════════════════════
def test_rest_heal_30_процентов_недостающего():
    # недостаёт 60 → 30% = 18
    assert Creature.rest_heal_amount(40, 100) == 18


def test_rest_heal_при_полном_хп_ноль():
    assert Creature.rest_heal_amount(100, 100) == 0


def test_rest_heal_округление_вниз():
    # недостаёт 5 → 1.5 → int() усечёт до 1
    assert Creature.rest_heal_amount(95, 100) == 1


# ═══════════════════════════════════════════════════════════════════
# Драфт майлстоунов 1-из-3 (B3) — стейт-машина Костра (без дисплея)
# ═══════════════════════════════════════════════════════════════════
import pygame  # noqa: E402

from core import forge as f  # noqa: E402
from core.cards.base import Card, DamageEffect  # noqa: E402
from core.players import Warrior  # noqa: E402
from ui.Campfire import Campfire  # noqa: E402


def _atk(name="Удар", dmg=6):
    return Card(name=name, cost=1, card_type="attack", description="",
                effects=[DamageEffect(dmg, dmg + 2)])


class _View:
    def __init__(self, player, deck):
        self.gm = type("GM", (), {})()
        self.gm.player = player
        self.gm.current_deck = deck


def _warrior_at_level(level, cap=15):
    """Воин с картой, уже прокачанной до `level` (готова к следующей ковке)."""
    p = Warrior()
    p.forge_points = 999
    p.forge_level_cap = cap
    c = _atk()
    f.assign_forge_uid(p, c)
    p.deck_forge_state[c._fuid] = {"level": level, "slots": []}
    return p, c


def test_draft_открывается_на_майлстоуне():
    Campfire.reset()
    p, c = _warrior_at_level(4)               # следующий уровень 5 = майлстоун
    Campfire._open_draft(p, c, 0, "early")
    assert Campfire.sub_state == "DRAFT"
    assert len(Campfire._draft_choices) == 3
    assert Campfire._draft_card_index == 0
    Campfire.reset()


def test_draft_выбор_вешает_выбранный_тег_и_возврат_в_кузницу():
    Campfire.reset()
    p, c = _warrior_at_level(4)
    Campfire._open_draft(p, c, 0, "early")
    chosen = Campfire._draft_choices[1]
    view = _View(p, [c])
    view.draft_choice_rects = [
        (pygame.Rect(0, 0, 10, 10), Campfire._draft_choices[0]),
        (pygame.Rect(20, 0, 10, 10), chosen),
    ]
    Campfire._handle_draft(view, (25, 5))     # клик во второй вариант
    rec = p.deck_forge_state[c._fuid]
    assert rec["level"] == 5
    assert [s["tag_id"] for s in rec["slots"]] == [chosen]   # выбранный, не авто
    assert Campfire.sub_state == "FORGE"
    assert Campfire._draft_card_index is None                # состояние очищено
    Campfire.reset()
