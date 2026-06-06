# Индекс рычагов баланса — Roguelike CardGame

Единая справочная карта **всех тюнинг-констант** игры. Для точечной балансировки:
нашёл строку → повернул ручку → прогнал гард (`python -m managers.balance.baseline
--check` или `pytest -m balance`). Константы живут НА МЕСТЕ (рядом с логикой —
локальность важнее god-конфига); здесь только указатель и смысл.

Парадигма, в которой эти числа имеют смысл, — [[balance-curve-framework]]:
враг растёт по `E₀·g^f`, игрок аддитивно, потолок пробивают компаундящие движки
(кат.4). Замер сдвигов — `managers/balance/` (две метрики wall/ceiling).

> Колонка «Рычаг» = что произойдёт при УВЕЛИЧЕНИИ значения.

---

## 1. Кривая сложности врага — `managers/EnemySpawner.py`

Главный регулятор «стены». Чистая экспонента `stat = BASE · GROWTH^floor`.

| Константа | Значение | Рычаг (↑) |
|---|---|---|
| `HP_BASE`, `HP_GROWTH` | 45, 1.028 | Толще враги / круче кривая HP |
| `DMG_BASE`, `DMG_GROWTH` | 5.5, 1.026 | Больнее враги / круче кривая урона |
| `SHLD_BASE`, `SHLD_GROWTH` | 3.5, 1.008 | Больше брони (контр-DPS) |
| `GROUP_2_FROM`, `GROUP_3_FROM` | 7, 26 | Позже появляются группы 2/3 врагов |
| `GROUP_HP_MULT`, `GROUP_DMG_MULT` | {2:.55,3:.40}, {2:.60,3:.50} | Сила каждого врага в группе |
| элита (inline `build_enemy`) | hp×1.5, dmg×1.4, shld×1.5 | Опасность элиток |
| босс (inline `build_enemy`) | hp×2.2, dmg×1.3, shld×1.8 | Стена босс-этажей |

Структура забега: `FLOORS_PER_ACT = 20` (`managers/MapGenerator.py`) — длина акта,
период босса (этажи 20/40/60/80/100).

### 1-bis. Элитные архетипы-контры (Этап B) — `core/enemies/elites/`

Уникальные элитки наказывают конкретный билд. Механики на хуках
`on_card_played`/`on_turn_start`. Стат-множители — общие (см. строку «элита» выше).

| Константа | Значение | Рычаг (↑) | Файл |
|---|---|---|---|
| `SpellEater.SHIELD_PER_CARD` | 4 | Жёстче контра пулемётам | `spell_eater.py` |
| `PlaguePustule.PLAGUE_POISON` | 3 (×2 при щите) | Жёстче контра обороне | `plague.py` |
| `ButcherTorturer.BUTCHER_THORNS` | 3 | Сильнее налог на хил | `butcher.py` |
| `CorruptionDevourer.DEVOUR_CAP` | 8 | Жёстче контра DoT | `devourer.py` |
| `_ELITE_ROOM_CHANCE` | 0.10 | Чаще элитные бои (sim) | `managers/balance/runner.py` |
| `_ELITE_FROM_FLOOR` | 8 | Раньше появляются элитки (sim) | `managers/balance/runner.py` |

NB: `_ELITE_ROOM_CHANCE`/`_ELITE_FROM_FLOOR` — только модель sim-раннера; в живой
игре частота элиток задаётся весом `ELITE` в `MapGenerator.NODE_WEIGHTS`.

## 2. Статусы-множители — `core/EffectCalculator.py`, `core/StatusRegistry.py`

Конвейер урона (порядок шагов важен; см. комментарии в `calculate_damage`).

| Рычаг | Значение | Где |
|---|---|---|
| Уязвимость (входящий ×) | ×1.5 | `EffectCalculator.py` (inline, шаг 5) |
| Слабость (исходящий ×) | ×0.75 | `EffectCalculator.py` (inline, шаг 1) |
| `SHATTER_MULT` (Раскол, пока есть щит) | 3.0 | `EffectCalculator.py:7` |
| `SHOCK_DAMAGE_PER_STACK` (флат за удар) | 3 | `EffectCalculator.py:4` |
| ПАР (steam `multiplier`) | 3.0 | `core/ComboRegistry.py` `COMBOS["steam"]` |

## 3. Детонации (burst-комбо) — `core/DetonationRegistry.py`

| Константа | Значение | Комбо |
|---|---|---|
| `ELECTRO_DAMAGE_PER_SHOCK` | 6 | Электро-взрыв (wet+shock, AoE) |
| `LAVA_DAMAGE_PER_IGNITE` | 4 | Лава (shatter+ignited) |
| `THERMO_DAMAGE_MULT` | 3 | Термовзрыв (ignited+shock) |

Добавить детонацию = 1 запись в `DETONATIONS` (порядок = приоритет при общих статусах).

## 4. Движки классов (кат.4 — компаунд)

| Класс | Рычаг | Значение | Где |
|---|---|---|---|
| Призыватель | `PACK_DAMAGE_PER_ALLY` (Свора, N²) | 5 | `core/Summon.py:15` |
| Призыватель | `MAX_PERSISTENT_ALLIES` (перенос стаи) | 6 | `managers/CombatManager.py:17` |
| Друид | `POISON_FRACTION` (хил→яд) | 0.3 | `core/players/druid.py:25` |
| Берсерк | базовый HP (HP-как-ресурс) | 60 | `core/players/berserker.py` |
| Реликвия-флагман | `GROWTH_PER_BOSS` (Корона Вознесения, ×урон/босс) | 1.25 | `core/relics/advanced/persistent.py:25` |

Барьер Воина / Мастерство Мага / Эхо / Кровожадность Разбойника — внутрибоевые
движки (сбрасываются `Player.reset_combat_statuses`); их числа — в карте/статусе.

## 5. Экономика (шаг №6 фреймворка) — регулятор скорости сборки

| Рычаг | Значение | Где |
|---|---|---|
| Золото за бой | `randint(20,35)+floor·3`, элита ×1.5, Корона→0 | `RewardManager.build_rewards` / зеркало `managers/balance/economy.py` |
| Цена удаления карты | `(15+floor·2)+removal·25`, Корона ×2 | `GameManager.get_removal_price` |
| `_KEY_PRICE` (ключ сундука) | 30 | `ui/shop/data.py:26` |
| `_RELIC_PRICE` (по редкости) + `floor·2` | словарь | `ui/shop/data.py:27` |
| `ROB_SUCCESS_CHANCE` (ограбление) | 0.30 | `ui/shop/data.py:25` |
| `REST_HEAL_PCT` (отдых у костра) | 0.30 | `core/Creature.py:15` |
| `_BLOOD_RITUAL_COST` (удаление за HP) | 10 | `ui/Campfire.py:14` |

## 6. Симулятор / замер — `managers/balance/`

НЕ влияют на игру — управляют ИЗМЕРЕНИЕМ баланса.

| Рычаг | Значение | Где |
|---|---|---|
| `_CAMPFIRE_HEAL` (хил между актами в симе) | 0.30 | `runner.py:20` |
| `_CARD_REWARD_CHANCE` (шанс карты-награды) | 0.6 | `runner.py:23` |
| `_DRAFT_SAMPLE` (best-of для greedy ceiling) | 5 | `builds.py:41` |
| `_THEME_BONUS` (надбавка за тему колоды) | 3.0 | `builds.py:45` |
| `EconomyPolicy.MAX_REMOVALS_PER_ACT` | 1 | `economy.py` |
| Регресс-гард: `BASELINE_N` / `SEED` / `MAX_DROP` / `MAX_RISE` | 40 / 99 / 6 / 12 | `baseline.py` |

**Эталон гарда** (`BASELINE` в `baseline.py`) — медианы этажа смерти wall/ceiling по
6 классам. Сдвинул баланс осознанно → переблагослови: `python -m managers.balance.baseline`.

## 7. Прокачка карт (движок кат.4) — `core/forge.py` + `core/ForgeRegistry.py`

Движок ковки (`_upgrade_design.md`). ✅ 39.4: потолок ФЛИПАЕТ — связка тегов +
Заточки (DPS) + Закалки/событий (оборона) по тема-гейту колоды (7-ter ниже).
✅ 39.5: раскатан в живую игру. **ИСТОЧНИК ПРАВДЫ ручок — `core/forge.py`**
(константы+математика; и живая игра, и сим тянут оттуда). `managers/balance/forge.py`
теперь только бот-политика (ForgePolicy) и ре-экспорт. Свип мутирует `core.forge`.
NB: пометки «`forge.py`» в колонке «Где» ниже = `core/forge.py`.

| Рычаг | Значение | Где |
|---|---|---|
| `FORGE_POINTS_PER_ACT` (приток FP/бой по актам) | (2, 3, 4) | `forge.py` (39.4) |
| `FORGE_POINTS_PER_BOSS` (бонус за босса) | 3 | `forge.py` |
| `LINEAR_BONUS_PER_LEVEL` (δ, слой стены) | 1 | `forge.py` |
| `LEVEL_COST_BASE` / `LEVEL_COST_STEP` (цена ур., сброс по тиру) | 1 / 1 | `forge.py` |
| `MILESTONE_STEP` (шаг майлстоунов `s`) | 5 | `forge.py` |
| `BOSS_LEVEL_CAPS` (босс-этаж → кап уровня) | 20:5 40:10 60:15 | `forge.py` |
| `EARLY_ADD` (ранний тег +mult) | 0.5 | `ForgeRegistry.py` |
| `LEG_*` (легендарные ×mult-масштабы) | см. файл | `ForgeRegistry.py` |
| `MAX_TRIGGER_DEPTH` (гард-рейл §10.2) | 5 | `forge.py` |

Цена тира = `1+2+3+4+5 = 15 FP`; до 15-го уровня = 45 FP. Приток ~190 FP/забег (39.4).

### 7-bis. Триединство экономики (С39.3) — `forge.py` + `events.py` + `economy.py`

Оборонный движок выживаемости: **Бои=база, %-Ивенты=скачки, Артефакты=масштаб.**
Калибровано свипом (`managers/balance/sweep.py`) против врага `g=1.026`. Флипает
HP-классы в акт 3 (Маг 86 / Призыв. 82 / Воин 64); Разбойник/Друид глухи (горлышко
= DPS/оборона, лечится атак.тегами 39.4). Память: `economy-trinity-survival-engine`.

| Рычаг | Значение | Смысл / где |
|---|---|---|
| `TEMPER_HP_PCT` (сила Закалки) | **0.20** | +20% к max_hp за Закалку; `forge.py` |
| `TEMPER_FP_COST` (цена Закалки) | **10** | FP за одну Закалку; `forge.py` |
| `TEMPER_PROACTIVE_RATIO` (порог гонки) | **0.6** | <1.0=проактив; закаляется пока давление≥0.6·бак; `forge.py` |
| `INCOMING_FIGHT_TURNS` (давление боя) | 5 | урон-за-ход → давление клира; `forge.py` |
| `EVENTS_PER_ACT` (частота скачков) | **2** | EVENT-нод за акт; `events.py` |
| `ACT_PCT_RANGE` (акт-скейл, БЕЗ капов) | 5-15 / 15-30 / 30-50% | % от стейта по актам; `events.py` |
| `EVENT_WIN_CHANCE` (стохастика) | 0.5 | шанс выигрыша гамбита; `events.py` |
| `EVENT_REWARD_MULT` (сила супер-рычага) | **2.0** | умеренная: зазор под артефакты; `events.py` |
| `HP_STAKE_FROM_ACT` (ва-банк HP) | 3 | с акта 3 алтарь ставит HP, не золото; `events.py` |
| `ARTIFACT_FP_MULT` / `ARTIFACT_MAX_HP_ADD` | 1.0 / 0 | ⚙️ заглушки реликвий (нейтрально); `forge.py` |
| `ARTIFACT_GOLD_MULT` | 1.0 | ⚙️ заглушка реликвий (нейтрально); `economy.py` |

Дефолт артефактных заглушек НЕЙТРАЛЕН ⇒ baseline зелёный (триединство = opt-in
в `run_single_run`, как `economy`/`forge`). Артефакты — поздний катализатор
эт.85-100 (база Бои+События намеренно НЕ закрывает эт.100 в одиночку).

### 7-ter. Заточка (Sharpen) — DPS-сток выживаемости (С39.4) — `forge.py`

Разрешение тупика 39.3: DPS-классы (Разбойник/Друид/Берсерк) мрут от нехватки
УРОНА, не HP — Закалка их не лечила. **Заточка** = player-level компаунд-множитель
урона `player.atk_mult` (сток FP, параллельный Закалке; читается `EffectCalculator`
шаг 8, инертен при `atk_mult=1.0`). На костре **тема-гейт колоды** (`deck_prefers_sharpen`)
маршрутизирует FP: офенс-колода точит урон (Заточка), оборонная копит Max HP
(Закалка) — `invest_if_threatened`. Память: `balance-findings-dps-bound`.

| Рычаг | Значение | Смысл / где |
|---|---|---|
| `SHARPEN_FP_COST` (цена Заточки) | **5** | FP за +30% урона; дешевле Закалки (компаунд); `forge.py` |
| `SHARPEN_ATK_PCT` (сила Заточки) | **0.30** | ×(1+0.30) к `atk_mult` за ковку; `forge.py` |

📊 Флип 39.4 (ceiling, forge OFF→ON, N=40 seed=99, med/wr60/wr100): Warrior 56→97,
Rogue 26→72, Mage 62→101, Druid 29→67, Berserker 25→40, Summoner 73→101. wr100>0
у 4/6. baseline-гард зелёный (forge OFF в wall ⇒ ранняя стена цела).
