# managers/balance/events.py
# СЕССИЯ 39.3 — %-СОБЫТИЯ = «скачки» триединства экономики (Бои=база,
# %-Ивенты=скачки, Артефакты=масштабираторы; см. _upgrade_design.md, память
# economy-trinity-survival-engine). До этого сим-раннер НЕ видел EVENT-узлы
# вообще (только бои/костры/экономику) → %-события нельзя было крутить как рычаг.
#
# МОДЕЛЬ (решения юзера, С39.3):
#   • Каденция — ДЕТЕРМИНИРОВАННАЯ (как живой MapGenerator): EVENTS_PER_ACT нод на
#     акт, на фикс. этажах (не бой-1/2, не костёр, не босс). Частоту крутит свип.
#   • Внутри события — СТОХАСТИКА (хардкор-рогалик): азартный размен с дисперсией
#     (сжёг ресурс → супер-рычаг ИЛИ ушёл ни с чем). Берётся из сидированного
#     random ⇒ при фикс. seed воспроизводимо (baseline детерминирован), но по N
#     прогонам даёт настоящий свинг живучести.
#   • Масштаб — АКТ-СКЕЙЛ без капов (капы душат фарт): Акт1 5-15% · Акт2 15-30% ·
#     Акт3 30-50% от текущего стейта игрока.
#   • Приток — в MaxHP (стохастическая экспонента выживаемости) и FP (глубина
#     ковки). Реюз заглушек артефактов (forge.ARTIFACT_*) ⇒ триединство едино.
#
# Подключается в runner ОПЦИОНАЛЬНО (events=None по умолчанию → регресс-нейтрально,
# baseline-гард зелёный). По образцу EconomyPolicy/ForgePolicy.
import random

from managers.MapGenerator import FLOORS_PER_ACT
from managers.balance import forge
from core import forge as core_forge   # источник правды заглушек артефактов (свип крутит core)

# ─── РУЧКИ (калибровка 39.3 — свип крутит в связке с Закалкой) ─────────────────
# Сколько EVENT-нод за акт. Главный рычаг частоты скачков. КАЛИБР. 39.3 = 2.
EVENTS_PER_ACT = 2
# Акт-скейл % от стейта игрока: (low, high). БЕЗ КАПОВ — фарт/безумие рогалика.
# Ключ — номер акта (1+); за пределами таблицы берётся последний (лейт-безумие).
ACT_PCT_RANGE = {1: (0.05, 0.15), 2: (0.15, 0.30), 3: (0.30, 0.50)}
# Шанс выигрыша гамбита (стохастика; ниже 0.5 = злее рогалик). КАЛИБР. 39.3 = 0.5.
EVENT_WIN_CHANCE = 0.5
# Множитель отдачи к ставке при выигрыше (рычаг «супер-рычага»). КАЛИБР. 39.3 = 2.0
# (УМЕРЕННАЯ точка, решение юзера): база Бои+События флипает HP-классы в акт 3, но
# НЕ закрывает эт.100 в одиночку — зазор оставлен под артефактный компаунд (третья
# нога триединства = поздний катализатор эт.85-100).
EVENT_REWARD_MULT = 2.0
# Курс конвертации сожжённого золота в FP при выигрыше FP-гамбита (золото за 1 FP).
EVENT_GOLD_PER_FP = 10
# С какого акта алтарь может ставить ТЕКУЩЕЕ HP вместо золота («ва-банк», §3:
# «сжигание половины золота/HP»). До него ставка — только золото (широта билда),
# чтобы стохастика не превращалась в death-рулетку на хрупких классах ранних актов.
HP_STAKE_FROM_ACT = 3


def _act_of(floor: int) -> int:
    """Номер акта (1+) для этажа."""
    return (floor - 1) // FLOORS_PER_ACT + 1


def _act_pct_range(floor: int) -> tuple:
    """Диапазон % от стейта для акта этого этажа (последний акт = лейт-безумие)."""
    act = _act_of(floor)
    last = max(ACT_PCT_RANGE)
    return ACT_PCT_RANGE[min(act, last)]


def event_floors(max_floor: int, events_per_act: int = None) -> set:
    """Детерминированные этажи событий: events_per_act нод РАВНОМЕРНО внутри
    каждого акта, минуя спец-этажи (бой-1/2, костёр FLOORS_PER_ACT-1, босс
    FLOORS_PER_ACT). Зеркалит контролируемую плотность живого MapGenerator —
    каденция жёсткая, стохастика живёт ВНУТРИ узла."""
    if events_per_act is None:
        events_per_act = EVENTS_PER_ACT
    floors = set()
    if events_per_act <= 0:
        return floors
    # Безопасное «окно» внутри акта: после боёв-разогрева (этаж 3) до костра.
    lo, hi = 3, FLOORS_PER_ACT - 2
    span = hi - lo
    n_acts = (max_floor - 1) // FLOORS_PER_ACT + 1
    for act_idx in range(n_acts):
        base = act_idx * FLOORS_PER_ACT
        for k in range(events_per_act):
            # Равномерно распределяем k-ю ноду в окне [lo, hi].
            off = lo + (k + 1) * span // (events_per_act + 1)
            floor = base + off
            if floor <= max_floor:
                floors.add(floor)
    return floors


class EventPolicy:
    """Политика %-событий бота: на фикс. EVENT-этажах предлагает азартный размен
    (масштаб по акту), бот-хардкор ВСЕГДА играет (моделируем свинг живучести).
    Без состояния на политике (всё на player/gm) → один инстанс переиспользуется
    для обеих метрик. ИСПОЛЬЗУЕТ random (стохастика) ⇒ при фикс. seed воспроизводимо.

    Каденцию задаёт events_per_act (передаётся в конструктор для свипа); диапазоны
    % и шанс/отдачу — модульные ручки."""

    def __init__(self, events_per_act: int = None):
        self.events_per_act = (EVENTS_PER_ACT if events_per_act is None
                               else events_per_act)
        self._floors_cache: dict = {}

    def _floors_for(self, max_floor: int) -> set:
        if max_floor not in self._floors_cache:
            self._floors_cache[max_floor] = event_floors(max_floor,
                                                          self.events_per_act)
        return self._floors_cache[max_floor]

    def maybe_event(self, player, gm, floor: int, max_floor: int = 100) -> None:
        """Если `floor` — EVENT-этаж: сыграть один азартный гамбит. Тип гамбита
        выбирается случайно (HP-алтарь / FP-сокровищница)."""
        if floor not in self._floors_for(max_floor):
            return
        low, high = _act_pct_range(floor)
        pct = random.uniform(low, high)
        win = random.random() < EVENT_WIN_CHANCE
        allow_hp = _act_of(floor) >= HP_STAKE_FROM_ACT
        # Выбор архетипа: алтарь (выживаемость) или сокровищница (глубина ковки).
        if random.random() < 0.5:
            self._altar(player, gm, pct, win, allow_hp)
        else:
            self._fp_treasury(player, gm, pct, win)

    # ── Архетипы гамбита ──────────────────────────────────────────────────────
    @staticmethod
    def _altar(player, gm, pct: float, win: bool, allow_hp_stake: bool) -> None:
        """Алтарь (гамбит выживаемости): ставка — pct ЗОЛОТА (широта билда), а с
        акта HP_STAKE_FROM_ACT возможна ставка pct ТЕКУЩЕГО HP («ва-банк»).
        Победа → +pct·REWARD_MULT к ТЕКУЩЕМУ max_hp (компаунд-%, §10.3 —
        стохастическая экспонента выживаемости) + полное исцеление + флэт-
        катализатор артефактов. Поражение → ставка сожжена впустую."""
        gold = getattr(gm, "player_gold", 0)
        stake_gold = int(gold * pct)
        # Ставка HP только в лейте И если золота на ставку не хватает (ва-банк).
        hp_stake = allow_hp_stake and stake_gold <= 0
        if stake_gold <= 0 and not hp_stake:
            return
        if hp_stake:
            player.hp = max(1, player.hp - int(player.hp * pct))
        else:
            gm.player_gold -= stake_gold
        if win:
            gain = int(player.max_hp * pct * EVENT_REWARD_MULT)
            gain += core_forge.ARTIFACT_MAX_HP_ADD
            player.max_hp += gain
            player.hp = player.max_hp

    @staticmethod
    def _fp_treasury(player, gm, pct: float, win: bool) -> None:
        """Сокровищница (FP-гамбит): ставка — pct золота. Победа → золото сгорает,
        взамен пачка FP (ставка/курс · REWARD_MULT · заглушка артефактов).
        Поражение → золото сгорело впустую. Без золота гамбит пропускается."""
        stake = int(getattr(gm, "player_gold", 0) * pct)
        if stake <= 0:
            return
        gm.player_gold -= stake
        if win:
            forge._ensure_state(player)
            fp = int(round(stake / EVENT_GOLD_PER_FP * EVENT_REWARD_MULT
                           * core_forge.ARTIFACT_FP_MULT))
            player.forge_points += fp
