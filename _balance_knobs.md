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
