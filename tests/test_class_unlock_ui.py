# tests/test_class_unlock_ui.py
# UI-гейт ярусной блокировки (С50, этап 3): HubView._select_class отказывает в
# выборе залоченного класса яруса 2 и пускает ярус 1 / открытый класс. Логика
# выбора без отрисовки — берём фейковый gm с метой.

from ui.hub.base import HubView
from core.players import Warrior


class _FakeGM:
    """Минимальный gm: текущий игрок + мета с анлоками (как у GameManager)."""
    def __init__(self, unlocks=None):
        self.player = Warrior()
        self.meta = {"unlocks": list(unlocks or [])}
        self.current_deck = []


def test_залоченный_тир2_не_выбирается():
    gm = _FakeGM()                       # пустые анлоки → Druid закрыт
    HubView._select_class(gm, "Druid")
    assert type(gm.player).__name__ == "Warrior"   # игрок не сменился


def test_ярус1_всегда_выбирается():
    gm = _FakeGM()
    HubView._select_class(gm, "Mage")
    assert type(gm.player).__name__ == "Mage"
    HubView._select_class(gm, "Berserker")
    assert type(gm.player).__name__ == "Berserker"


def test_открытый_тир2_выбирается():
    gm = _FakeGM(unlocks=["Rogue"])      # Rogue открыт записью в мете
    HubView._select_class(gm, "Rogue")
    assert type(gm.player).__name__ == "Rogue"


def test_смена_класса_перевыдаёт_колоду():
    gm = _FakeGM()
    HubView._select_class(gm, "Mage")
    assert gm.current_deck                # стартовая колода нового класса непуста


def test_dev_тоггл_переключает_полный_доступ(monkeypatch):
    # DEV-кнопка в Хабе переключает meta['dev_unlock_all'] (персист через SaveManager).
    import pygame
    from managers import SaveManager
    monkeypatch.setattr(SaveManager, "save", lambda: None)   # не писать на диск
    gm = _FakeGM()
    hub = HubView()
    hub.dev_button = pygame.Rect(0, 0, 100, 30)              # минуем отрисовку

    class _V:
        pass
    v = _V(); v.gm = gm

    assert not gm.meta.get("dev_unlock_all", False)
    hub.handle_click(v, (50, 15))
    assert gm.meta["dev_unlock_all"] is True                 # вкл
    hub.handle_click(v, (50, 15))
    assert gm.meta["dev_unlock_all"] is False                # выкл
