# tests/test_relic_tech_debt.py
# «Технический Долг» — классовый КАТ.4-компаунд Берсерка: добил в HP-долге → +1% урона
# навсегда (перенос между боями). + классовый резонанс выдачи (только Берсерку).
from types import SimpleNamespace

from core.rarity import Rarity
from core.relics import ТехническийДолг, RELIC_POOL


class _StubCM:
    def __init__(self, player):
        self.player = player
        self.logs = []

    def add_log_message(self, m):
        self.logs.append(m)


# ── механика компаунда ────────────────────────────────────────────────────────
def test_в_пуле_uncommon_и_резонанс_берсерка():
    assert ТехническийДолг in RELIC_POOL[Rarity.UNCOMMON]
    assert ТехническийДолг().relic_class == "Berserker"


def test_добивание_в_долге_копит_стак():
    r = ТехническийДолг()
    cm = _StubCM(SimpleNamespace(hp=-5))       # в долге
    r.on_kill(None, cm)
    r.on_kill(None, cm)
    assert r.stacks == 2                        # перманентно копится за килл-в-долге


def test_добивание_не_в_долге_не_копит():
    r = ТехническийДолг()
    cm = _StubCM(SimpleNamespace(hp=10))        # не в долге
    r.on_kill(None, cm)
    assert r.stacks == 0


def test_стаки_множат_исходящий_урон():
    r = ТехническийДолг()
    r.stacks = 50                               # +50% (50 × 1%)
    assert r.on_damage_calculated(100, is_player_attack=True) == 150
    assert r.on_damage_calculated(100, is_player_attack=False) == 100  # не на входящий
    assert ТехническийДолг().on_damage_calculated(100) == 100          # 0 стаков → инертно


def test_стаки_переносятся_между_боями():
    r = ТехническийДолг()
    r.stacks = 7
    r.on_combat_start(None)                     # НЕ сбрасывает (кат.4-перенос по забегу)
    assert r.stacks == 7


# ── классовый резонанс выдачи (RewardManager._pick_relic) ─────────────────────
def _gm(player_cls, owned_names):
    return SimpleNamespace(
        player=player_cls(),
        relics=[SimpleNamespace(name=n) for n in owned_names],
        meta=None,                              # без анлок-фильтра
    )


def test_резонанс_выдачи_только_берсерку():
    from managers.RewardManager import _pick_relic
    from core.players import Berserker, Warrior
    # Все прочие UNCOMMON помечаем как уже имеющиеся → в этой редкости кандидат один:
    # Технический Долг (если резонанс пускает).
    others = [r().name for r in RELIC_POOL[Rarity.UNCOMMON]
              if r().name != "Технический Долг"]
    bers = _pick_relic(_gm(Berserker, others), Rarity.UNCOMMON)
    assert bers is not None and bers.name == "Технический Долг"   # Берсерку — выпадает
    war = _pick_relic(_gm(Warrior, others), Rarity.UNCOMMON)
    assert war is None or war.name != "Технический Долг"          # Воину — никогда
