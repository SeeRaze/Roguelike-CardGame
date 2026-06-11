# tests/test_card_classifier.py
# G2 (С58): PAYLOAD-карты стихий красятся по своей стихии (рамка-цвет из реестра).
import pytest

from core.StatusRegistry import STATUSES
from core.cards.legacy import create_legacy_patch, create_tech_debt
from core.cards.coffee import create_coffee_spill, create_coffee_flood
from core.cards.shortcircuit import create_voltage_spike, create_mass_short
from core.cards.tox import create_micromanage, create_overtime
from core.cards.leak import create_memory_leak, create_infinite_loop
from core.cards.decomp import create_disassembler, create_reverse_engineer
from ui.cards.classifier import classify_card
from ui.cards.data import card_palette, _ELEMENTAL_CARD_KEYS


@pytest.mark.parametrize("factory,expected", [
    (create_legacy_patch,    "legacy"),
    (create_tech_debt,       "legacy"),
    (create_coffee_spill,    "coffee"),
    (create_coffee_flood,    "coffee"),       # AoEStatusEffect тоже ловится
    (create_voltage_spike,   "shortcircuit"),
    (create_mass_short,      "shortcircuit"),
    (create_micromanage,     "tox"),
    (create_overtime,        "tox"),
    (create_memory_leak,     "leak"),
    (create_infinite_loop,   "leak"),
    (create_disassembler,    "decomp"),       # DecompEffect → "decomp"
    (create_reverse_engineer,"decomp"),
])
def test_стихийная_карта_классифицируется_по_стихии(factory, expected):
    assert classify_card(factory()) == expected


@pytest.mark.parametrize("key", _ELEMENTAL_CARD_KEYS)
def test_палитра_стихии_берёт_цвет_рамки_из_реестра(key):
    # Единый источник правды цвета: рамка = badge_bg статуса, фон = его затемнение.
    bg, border = card_palette(key)
    assert border == STATUSES[key]["badge_bg"]
    assert all(b <= f for b, f in zip(bg, border))   # фон темнее рамки


def test_палитра_неизвестного_ключа_фолбэк_default():
    assert card_palette("нет_такого") == card_palette("default")
