# tests/test_shop.py
# Тесты магазина (Этап C, C2): данные витрины (data.py) + логика покупок (base.py).
# UI-рендер не запускаем — проверяем чистую логику с лёгким фейк-view.
import random

import pygame
import pytest

from core.rarity import Rarity
from managers.GameManager import GameManager
from ui.shop import data
from ui.shop.base import Shop


# ═══════════════════════════════════════════════════════════════════
# data.py — генерация витрины и цены
# ═══════════════════════════════════════════════════════════════════
def test_pick_cards_возвращает_n_разных_карт():
    random.seed(1)
    cards = data.pick_cards(5, "Warrior")
    assert len(cards) == 5
    # random.sample берёт без повторов фабрик → экземпляры разные объекты
    assert len({id(c) for c in cards}) == 5


def test_pick_cards_клампится_к_размеру_пула():
    cards = data.pick_cards(9999, "Warrior")
    pool_size = len(data.get_pool_for_class("Warrior"))
    assert len(cards) == pool_size


def test_цена_карты_и_ключа():
    assert data.get_card_price(5) == 35 + 5 * 3
    assert data.get_key_price() == 30


def test_цена_реликвии_по_редкости_плюс_этаж():
    class _R:
        rarity = Rarity.COMMON
    # COMMON база 70 + floor 5 * 2 = 80
    assert data.get_relic_price(_R(), 5) == 80


def test_pick_relic_не_выдаёт_уже_имеющуюся():
    random.seed(3)
    gm = GameManager()
    relic = data.pick_relic(gm)
    assert relic is not None
    owned = {r.name for r in gm.relics}
    assert relic.name not in owned


# ═══════════════════════════════════════════════════════════════════
# base.py — логика покупок (фейк-view с готовыми rect-ами)
# ═══════════════════════════════════════════════════════════════════
class _FakeView:
    """Минимальный view: gm + rect-ы, как их выставляет main_view."""
    def __init__(self, gm):
        self.gm = gm
        self.scroll_y = 0


@pytest.fixture
def shop_setup():
    gm = GameManager()
    gm.current_floor = 5
    gm.player_gold = 500
    view = _FakeView(gm)
    Shop.reset()
    Shop.generate_showcase(gm)
    # rect-ы, которые обычно рисует main_view
    view.shop_card_rects   = [(pygame.Rect(i * 200, 0, 180, 250), i)
                              for i in range(len(Shop.items))]
    view.shop_relic_rect   = pygame.Rect(0, 300, 450, 120)
    view.btn_shop_key_rect = pygame.Rect(500, 300, 450, 120)
    view.btn_shop_remove_rect = pygame.Rect(0, 500, 640, 70)
    view.btn_shop_leave_rect  = pygame.Rect(0, 600, 640, 70)
    return gm, view


def test_покупка_карты_списывает_золото_и_кладёт_в_колоду(shop_setup):
    gm, view = shop_setup
    g0, deck0 = gm.player_gold, len(gm.current_deck)
    Shop._handle_main(view, view.shop_card_rects[0][0].center)
    assert gm.player_gold == g0 - data.get_card_price(gm.current_floor)
    assert len(gm.current_deck) == deck0 + 1
    assert Shop.items[0] is None        # слот опустел


def test_покупка_карты_без_золота_ничего_не_делает(shop_setup):
    gm, view = shop_setup
    gm.player_gold = 0
    deck0 = len(gm.current_deck)
    Shop._handle_main(view, view.shop_card_rects[0][0].center)
    assert gm.player_gold == 0
    assert len(gm.current_deck) == deck0
    assert Shop.items[0] is not None    # карта на месте


def test_покупка_реликвии_списывает_и_добавляет(shop_setup):
    gm, view = shop_setup
    if Shop.relic_item is None:
        pytest.skip("в этом сиде реликвия не сгенерилась")
    relic = Shop.relic_item
    price = data.get_relic_price(relic, gm.current_floor)
    g0, n0 = gm.player_gold, len(gm.relics)
    Shop._handle_main(view, view.shop_relic_rect.center)
    assert gm.player_gold == g0 - price
    assert len(gm.relics) == n0 + 1
    assert gm.relics[-1] is relic
    assert Shop.relic_item is None


def test_покупка_ключа_списывает_и_растит_счётчик(shop_setup):
    gm, view = shop_setup
    g0, k0 = gm.player_gold, gm.player_keys
    Shop._handle_main(view, view.btn_shop_key_rect.center)
    assert gm.player_gold == g0 - data.get_key_price()
    assert gm.player_keys == k0 + 1


def test_утилизация_уводит_в_режим_remove(shop_setup):
    gm, view = shop_setup
    Shop._handle_main(view, view.btn_shop_remove_rect.center)
    assert Shop.sub_state == "REMOVE"


# ═══════════════════════════════════════════════════════════════════
# Ограбление — украсть реликвию (monkeypatch random.random)
# ═══════════════════════════════════════════════════════════════════
def test_ограбление_успех_забирает_реликвию_и_закрывает(shop_setup, monkeypatch):
    gm, view = shop_setup
    if Shop.relic_item is None:
        pytest.skip("в этом сиде реликвия не сгенерилась")
    relic = Shop.relic_item
    n0, floor0 = len(gm.relics), gm.current_floor
    monkeypatch.setattr("ui.shop.base.random.random", lambda: 0.0)  # < 0.30 → успех
    Shop._rob(view)
    assert relic in gm.relics and len(gm.relics) == n0 + 1
    assert gm.current_floor == floor0 + 1     # сбежал на след. этаж
    assert Shop.sub_state == "MAIN" and Shop.relic_item is None


def test_ограбление_провал_зовёт_элитный_бой(shop_setup, monkeypatch):
    gm, view = shop_setup
    if Shop.relic_item is None:
        pytest.skip("в этом сиде реликвия не сгенерилась")
    n0, floor0 = len(gm.relics), gm.current_floor
    monkeypatch.setattr("ui.shop.base.random.random", lambda: 0.99)  # >= 0.30 → провал
    Shop._rob(view)
    assert len(gm.relics) == n0              # реликвию не дали
    assert gm.current_floor == floor0        # этаж не двигается (продвинет победа)
    assert gm.current_state == "COMBAT"
    assert gm.active_combat is not None      # элитный бой запущен


# ═══════════════════════════════════════════════════════════════════
# Прокачанные карты в магазине (С57, шаг 3 эконом-дуги)
# ═══════════════════════════════════════════════════════════════════
def test_pick_cards_до_первого_босса_не_куёт():
    # floor<=20 → reward_level 0 → товары обычные, паспортов нет.
    random.seed(3)
    gm = GameManager()
    cards = data.pick_cards(5, "Warrior", player=gm.player, floor=10)
    assert all(data.forge_mod.forge_level(gm.player, c) == 0 for c in cards)


def test_pick_cards_в_лейте_куёт_часть_слотов():
    # floor>40 → reward_level 10 → при шансе хотя бы один слот выкован за прогон сидов.
    gm = GameManager()
    any_forged = False
    for seed in range(20):
        random.seed(seed)
        gm.player.deck_forge_state.clear()
        cards = data.pick_cards(5, "Warrior", player=gm.player, floor=50)
        if any(data.forge_mod.forge_level(gm.player, c) == 10 for c in cards):
            any_forged = True
            break
    assert any_forged, "ни один слот не выковался за 20 сидов (шанс сломан?)"


def test_цена_выкованной_выше_базовой():
    gm = GameManager()
    from core import forge as f
    card = data.pick_cards(1, "Warrior")[0]
    base = data.get_forged_card_price(card, gm.player, 50)
    f.forge_card_to_level(gm.player, card, 10, "Warrior")
    forged = data.get_forged_card_price(card, gm.player, 50)
    assert forged == base + 10 * data.SHOP_FORGE_PRICE_PER_LEVEL


def test_покупка_выкованной_сохраняет_паспорт(shop_setup):
    gm, view = shop_setup
    from core import forge as f
    # Выковываем первый товар вручную (floor фикстуры=5 → showcase не кует)
    card = Shop.items[0]
    f.forge_card_to_level(gm.player, card, 10, "Warrior")
    uid = card._fuid
    gm.player_gold = 9999
    Shop._handle_main(view, view.shop_card_rects[0][0].center)
    assert Shop.items[0] is None
    assert uid in gm.player.deck_forge_state            # паспорт перешёл в колоду
    assert card in gm.current_deck


def test_выход_снимает_паспорта_некупленных(shop_setup):
    gm, view = shop_setup
    from core import forge as f
    forged = [c for c in Shop.items]
    uids = []
    for c in forged:
        f.forge_card_to_level(gm.player, c, 5, "Warrior")
        uids.append(c._fuid)
    assert all(u in gm.player.deck_forge_state for u in uids)
    Shop._discard_unbought_forged(gm)
    assert all(u not in gm.player.deck_forge_state for u in uids)
