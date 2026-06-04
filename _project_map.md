# _project_map.md
_Последнее обновление: Сессия 32, Jun 4, 2026_
_История изменений по версиям — в `PATCHNOTES.md`._

## Архитектура
- `core/` — вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py, Summon.py)
- `ui/` — вся отрисовка. Пакеты: `cards/` (CardRenderer), `combat/` (CombatInterface+HUD, targeting), `hub/` (HubView), `shop/` (Shop), `victory/` (VictoryScreen), `library/` (CardLibraryView), `chest/`, `events/`; модули: GameView.py (+`draw_dispatchers.py`, `hover_state.py`), MainMenu.py, MapView.py, LeaderboardView.py, Campfire.py.
- `managers/` — CombatManager, DeckManager, GameManager, MapGenerator, network_manager, EnemySpawner, RewardManager
- Разрешение: строго 1920×1080 Full HD
- **Ветка разработки: dev** (main — стабильная, dev — активная работа)

## Железные ГОСТы
- **Логика (`core/`, `managers/`): жёсткий лимит 150 строк.** Хороший прокси «файл не делает
  лишнего». Разрастается — выносим ответственность в модуль (см. Сессию 29: god-object → модули).
- **UI (`ui/`): делим ПО СМЫСЛУ, а не по строкам.** Эталон — `ui/chest/`:
  `data` (константы/пулы, без pygame) · `rendering`/`shared` (функции `draw_*`) ·
  `handlers` (клики) · `base`/`__init__` (оркестратор + реэкспорт). 150 строк — *триггер
  посмотреть*, не жёсткий гейт; у файла-оркестратора/рендера мягкий потолок ~200–220.
  Резать только по реальному шву (данные ↔ отрисовка ↔ клики), НИКОГДА — ради цифры.
- Модульность и логичные зависимости — главный принцип. Никаких «божественных объектов».
- Публичные точки входа сохраняем через реэкспорт в `__init__.py` (импортёры не трогаем).

## Навигация по проекту
- Читать этот файл ПЕРВЫМ в каждой сессии — он даёт карту систем и «грабли».
- Файлы читаются напрямую из локальной рабочей копии (репозиторий склонирован, ветка `dev`). Поиск по коду — grep/glob, а не выкачка из GitHub.
- Перед изменением логики свериться с разделами «Ключевые системы» и «Важные детали и грабли» ниже.
- Для добавления нового контента — раздел «Как добавить контент».

## Игровой цикл и машина состояний (САМОЕ ВАЖНОЕ для навигации)
Точка входа: `main.py` → `GameView().run()`.

`GameView.run()` — главный цикл (60 FPS):
```
while is_running:
    handle_events()   # pygame-события: QUIT, клики (→ InputHandler), скролл
    update()          # пересчёт hover-состояния (HoverState), анимации хаба
    draw()            # отрисовка текущего экрана + pygame.display.flip() (ОДИН раз в конце)
```

Всё ветвление экранов идёт через `gm.current_state` (строка) и два словаря-диспетчера:
- **Отрисовка**: `DRAW_HANDLERS` в `ui/draw_dispatchers.py` — `state → функция отрисовки`.
- **Клики**: `STATE_HANDLERS` в `ui/InputHandler.py` — `state → обработчик клика`.

Добавить новый экран = одна запись в каждый словарь + функция отрисовки/обработчик.
Боевой hover-расчёт — `ui/combat/hover.py` (`update_combat_hover(view)`), зовётся из `GameView.update`.

**Состояния** (`gm.current_state`):
`MAIN_MENU`, `HUB`, `MAP`, `COMBAT`, `CAMPFIRE`, `SHOP`, `CHEST`, `EVENT`, `VICTORY`, `LEADERBOARD`, `CARD_LIBRARY`.

**Типовые переходы:**
`MAIN_MENU → HUB → MAP → (COMBAT/SHOP/CHEST/EVENT/CAMPFIRE)` → после боя `COMBAT → VICTORY → MAP` (через `distribute_combat_rewards()` → `pending_rewards`). Смерть игрока → `LEADERBOARD`. Босс пройден → следующий акт (`setup_next_floor`).

`GameManager` — «глобальный мозг»: хранит `current_state`, `player`, `relics`, `current_deck`, прогрессию этажей/карты, `active_combat` (текущий `CombatManager`).

## Полный список файлов (актуально на Jun 3, 2026 — после Сессии 28)
main.py, server.py, _project_map.md, PATCHNOTES.md, requirements.txt, .github/workflows/ci.yml

core/rarity.py, core/Creature.py, core/EffectCalculator.py, core/StatusRegistry.py

core/cards/init.py, base.py, basic.py, fire.py, poison.py, water.py, heal.py

core/cards/buff/init.py, strength.py, thorns.py, regen.py, vampirism.py

core/cards/debuff/init.py, vulnerable.py, weak.py, bleed.py

core/enemies/init.py, base.py, cultist.py, slime.py, boss.py

core/players/init.py, base.py, mage.py, rogue.py, warrior.py, druid.py, berserker.py, summoner.py

core/players/ability.py (базовый ClassAbility)

core/players/abilities/init.py, warrior.py, rogue.py, mage.py, druid.py, berserker.py, summoner.py (один файл на способность)

core/relics/init.py, base.py, starter.py, elemental.py

core/relics/advanced/init.py, bleed_poison.py, shield.py, healing.py, damage.py, utility.py (по теме)

managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py,

     MapGenerator.py, network_manager.py, EnemySpawner.py, RewardManager.py

managers/balance/init.py, bot.py, runner.py, report.py (симуляция баланса — Сессия 32)
ui/chest/init.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py

ui/combat/init.py, interface.py, panels.py, bottom.py, layout.py, hover.py, relic_panel.py, hud.py

ui/cards/init.py, renderer.py, classifier.py, description.py, keywords.py, data.py

ui/hub/init.py, base.py, selectors.py, deck.py, data.py

ui/shop/init.py, base.py, main_view.py, remove_view.py, data.py

ui/victory/init.py, base.py, rewards_view.py, modal.py, data.py

ui/library/init.py, base.py, data.py

ui/events/init.py, event_data.py, event_effects.py, positive.py, negative.py,

      neutral.py, special.py
ui/Campfire.py, EventView.py, GameView.py, draw_dispatchers.py, hover_state.py,

InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, map_icons.py


## Ключевые системы

### Creature.py
Базовый класс (hp, shield, self.statuses={} через __getattr__/__setattr__).
- `take_damage(amount, attacker=None, combat_manager=None)`
- `heal(amount, combat_manager=None)`
- `gain_shield(amount, combat_manager=None)` — с хуком on_shield_gained
- `_ELEMENTAL_KEYS = frozenset(("ignited", "wet", "poison"))` — блокируется при `_elemental_blocked`

### StatusRegistry.py
Единый реестр всех 10 статусов:
vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire

### EffectCalculator.py
Единая точка боевой математики. `dry_run=True` для превью.
- Обновляет `gm.stats["max_damage_dealt"]`
- Определяет `is_player_attack`, передаёт в `on_damage_calculated`
- Пассив Берсерка: бонус = `int((1 - hp/max_hp) * 10)`, применяется между шагом 2 (ярость) и шагом 3 (слабость), только `is_player_attack` и `type(attacker).__name__ == "Berserker"`

### Карты и эффекты (core/cards/)
Карта = `Card(name, cost, card_type, description, effects, rarity, exile)`, где `effects` — список «кирпичей»-эффектов. `Card.apply(player, enemy, cm)` вызывает `effect.execute(...)` по очереди.
- **Кирпичи-эффекты** (`core/cards/base.py`): `DamageEffect`, `ShieldEffect`, `StatusEffect`, `HealEffect`, `RegenEffect`, `PoisonEffect` (+ `VampireDamageEffect` — DEPRECATED). Каждый: `execute(player, enemy, combat_manager, is_upgraded)`, берёт `base_val`/`upgrade_val`.
- **Фабрики карт** — функции `create_*()`, сгруппированы по модулям: `basic.py` (strike/defend/heavy_blade/iron_wall), `fire.py`, `water.py`, `poison.py`, `heal.py`, `buff/` (strength/thorns/regen/vampirism), `debuff/` (vulnerable/weak/bleed). Все реэкспортируются из `core/cards/__init__.py`.
- `card_type` ∈ `"attack"`/`"defend"`/… — используется реликвиями (напр. СвинцовыйНабалдашник ловит первую `attack`).
- `exile=True` — карта уходит в `exile_pile` после розыгрыша (до конца боя).
- Превью урона на карте — `EffectCalculator.calculate_damage(..., dry_run=True)` (состояние не меняется).

### Каталог карт и классовые пулы (core/cards/catalog.py) — НОВОЕ (Сессия 32)
ЕДИНЫЙ источник правды о том, какие карты существуют и кому доступны:
- `GENERIC_FACTORIES` — нейтральные карты (доступны всем классам).
- `CLASS_FACTORIES = {"Summoner": [wolf, golem]}` — классовые карты, выдаются в забеге
  ТОЛЬКО своему классу. Добавить классовую карту = одна строка сюда.
- `get_pool_for_class(class_name)` — generic + классовые класса (для пулов выдачи).
- `get_class_cards(class_name)` — только классовые (для вкладки библиотеки).
- Атрибут `Card.card_class` (None=generic) проставляется централизованно обёрткой
  `_tagged` в каталоге — фабрики карт остаются чистыми.
- **Пулы выдачи берут карты по классу игрока**: `ui/shop/data.py::pick_two_cards`,
  `ui/chest/data.py::generate_chest_cards`, `ui/events/event_effects.py` (gain_random_card)
  → `get_pool_for_class(type(gm.player).__name__)`. Дублирование пулов устранено.

### Бой: цикл хода (CombatManager)
`CombatManager.__init__(player, enemies, starting_deck, game_manager=None)` — принимает список врагов (или одного, автоматически оборачивается). Хранит `self.enemies: list`, `self.allies: list`. Compat-свойство `self.enemy` → первый враг (для старого кода).
- **`start_turn_phase`**: цикл по всем живым врагам → `choose_intent()` → пассив игрока считает carry щита → `_iron_will_shield = shield`; сброс щита до carry → `energy = max_energy` → добор `5 + bonus_draw` → (Разбойник: случайной карте `temp_cost -= 1`) → хуки реликвий `on_turn_start` → `ability.on_turn_start` (штрафы).
- **`play_card_by_index(idx, target=None)`**: проверка энергии → если цель не передана: `get_target_enemy()` (первый живой враг) → `card.apply(player, target, self)` → пассив `on_card_played_passive` → реликвии `on_card_played` → карта в `discard_pile`/`exile_pile`.
- **`end_turn_phase`**: сброс руки → цикл по живым врагам: `shield=0`, `execute_intent()`, `tick_statuses()`, `_check_enemy_death()` (вызывает `on_kill` на реликвиях + стата) → игрок `tick_statuses()` → цикл по союзникам: `choose_action()`, `execute_action()`, `tick_statuses()`, `_check_ally_death()` → проверка победы: `all(e.hp <= 0)` → `check_player_defeat()`.
- **Мульти-враги**: этажи 1–4: 1 враг, 5–8: 2 врага, 9+: 3 врага. HP каждого уменьшен пропорционально. Босс всегда один.
- **Таргетинг**: клик по вражеской панели меняет `_target_index`. Жёлтая рамка вокруг выбранной цели. `play_card_by_index` получает цель из `TargetingSystem.get_current_target()`.
- **Союзники**: карты призыва (`create_summon_wolf`/`golem`) создают `Summon` в `combat.allies`. В конце хода союзники атакуют случайного живого врага. Панели союзников — в центральной зоне (x=590..1330).
- **Пассив «Свора»** (`Summon._pack_bonus`): каждый призыв бьёт сильнее на `PACK_DAMAGE_PER_ALLY` (=2) за КАЖДОГО другого живого союзника → урон стаи растёт нелинейно (масштаб Призывателя на поздних этажах). Лог показывает бонус `(+N Свора)`.

### Колода (DeckManager)
Пайлы: `draw_pile` ← `hand` → `discard_pile`; `exile_pile` отдельно. `draw_cards(n)` — при пустом доборе перемешивает сброс обратно. `discard_hand()` — сброс руки + чистка `temp_cost`. `reset_deck()` (новый бой) — возвращает изгнанные карты в пул и перемешивает.

### Враги: система намерений (core/enemies/)
Класс намерения на враге: `enemy.intent` ∈ `IntentAttack/IntentDefend/IntentDebuff/IntentNone` (есть `set_intent(type, value)` + св-ва-совместимости `intent_type`/`intent_value`).
- `choose_intent()` — переопределяется в подклассах (`cultist.py`, `slime.py`, `boss.py`), задаёт намерение на ход.
- `execute_intent(player, cm)` — исполняет: attack → `calculate_damage` + `take_damage`; defend → `gain_shield`; debuff → `player.weak += value`.
- `base_test_damage`/`base_test_shield` — базовые значения, проставляются в `EnemySpawner.build_enemy` (статы/имя/класс врага). `GameManager.spawn_procedural_enemy` — тонкий фасад: зовёт `build_enemy`, создаёт `CombatManager`.

### Реликвии — хуки
`on_combat_start`, `on_turn_start`, `on_damage_calculated(base_dmg, is_player_attack=True)`,
`on_tick_ignited`, `on_wet_applied`, `on_card_played`, `on_shield_gained(amount, creature, combat_manager=None)`,
`on_kill` (заглушка), `on_combat_end`, `on_bleed_tick`, `on_heal`, `on_chest_opened`

`on_turn_start` вызывается в `CombatManager.start_turn_phase` ПОСЛЕ сброса щита.

### Реликвии — UI в бою (инвентарь)
- Полоса сверху (`ui/combat/panels.py::draw_relic_bar`): компактные **бейджи** (квадрат с рамкой
  по редкости + 2-буквенная аббревиатура; золотая точка = активная). Рисует `CombatHUD.draw_relics`
  (`ui/combat/hud.py`) → возвращает `(view.relic_rects=[(rect,relic)...], hidden)`. При нехватке
  ширины — слот «+N» (`view.relic_overflow_rect`).
- Метка «АРТЕФАКТЫ:» (`view.relic_panel_btn_rect`) и «+N» открывают **панель** `RelicPanel`
  (`ui/combat/relic_panel.py`) — модальный оверлей со всеми реликвиями (бейдж+название+описание,
  2 колонки). Состояние `RelicPanel._open` привязано к `id(active_combat)` → авто-сброс между боями.
- Ховер по бейджу → `CombatHUD.draw_relic_tooltip` (гасится при открытой панели). Клик по активной
  реликвии (бейдж или ячейка панели) → `relic.activate(active_combat)`. Маршрутизация —
  `InputHandler._handle_combat` (панель перехватывает клики первой).

### Активные способности классов
Файлы: `core/players/ability.py` (базовый класс `ClassAbility`), пакет `core/players/abilities/` — по одному файлу на способность (`warrior.py`/`rogue.py`/`mage.py`/`druid.py`/`berserker.py`), реэкспорт через `abilities/__init__.py`.
- **WarriorAbility «Щитовой удар»**: урон врагу = 50% текущего щита. Один раз за бой.
- **RogueAbility «Вскрытие»**: удвоить кровотечение на враге, -1 энергия в следующем ходу. Один раз за бой. Флаг `_penalty_pending`, хук `on_turn_start`.
- **MageAbility «Стихийный барьер»**: блок стихий на врага на 1 ход (`_elemental_blocked` на CombatManager), щит = сумма стихийных стаков × 3. Один раз за бой.
- **DruidAbility «Токсичный взрыв»**: снять весь яд с врага, нанести разом, Регенерация = яд // 2. Один раз за бой.
- **BerserkerAbility «Кровавая ярость»**: -10% макс HP себе сквозь щит, +Ярость = урон × 2. Один раз за бой.
- **SummonerAbility «Подкрепление»** (Сессия 32, каркас): призвать Волка (HP 12, Атака 4) в `allies`. Один раз за бой. Пассив класса — «Свора» (см. раздел «Союзники»).

UI: `draw_ability_slot` в `hud.py` → `view.ability_rect` (пересчитывается каждый кадр).
Тултип: `CombatHUD.draw_ability_tooltip(screen, font, ability, mouse_pos)` — вызывается в конце `draw_combat_screen` при наведении.

### Пассивы классов (хуки в `core/players/base.py`, переопределяются в подклассах)
- **Warrior** «Железный задел» (`on_turn_start_passive`, warrior.py:25): переносит 30% текущего щита на новый ход через `_passive_shield_carry`. Считается ДО сброса щита в `start_turn_phase`.
- **Mage** «Стихийный резонанс» (`on_card_played_passive`, mage.py:26): если разыгранная карта вызвала комбо ПАР (флаг `_steam_combo_triggered`), +1 карта из колоды.
- **Druid** «Токсичный круговорот» (`on_heal_passive`, druid.py:34): при любом хиле игрока враг получает яд = размеру хила.
- **Rogue / Berserker**: классовых пассивов НЕТ (только активные способности + спец-логика в `start_turn_phase`/EffectCalculator).
- Хуки пассивок: `on_turn_start_passive`, `on_card_played_passive`, `on_heal_passive` (база — заглушки).

### Балансер (managers/balance/ + BalanceSimulator.py) — ПЕРЕПИСАН (Сессия 32)
Модель **сквозного забега**: бот идёт этаж за этажом ОДНОЙ колодой, HP переносится,
костёр лечит 30% на предбоссовом этаже. Использует РЕАЛЬНЫЕ формулы врагов
(`build_enemy_group`), а не захардкоженные статы.
- `bot.py::BotCombatManager` — жадный ИИ (случайные доступные карты), глушит
  сеть/UI (`check_player_defeat` без `send_run_record`/LeaderboardView).
- `runner.py::run_single_run` — один забег floor=1..100, `_StubGM` (лёгкий контекст).
- `report.py` — перцентили глубины смерти, win-rate по чекпоинтам [10,25,50,75,100], кривая %HP.
- `BalanceSimulator.py` — тонкий фасад, `python -m managers.BalanceSimulator` (6 классов × 200).
- Бот с прогрессией колоды (добор карт-наград). Замер Сессии 33 (% до эт.100):
  Воин 2 · Маг 2 · Призыватель 0 · Берсерк 4 · Разбойник 31 · Друид 13.
  sustain-классы ребалансированы (вампиризм/реген + пассив Друида), разрыв сжат.
  После пассива «Свора» Призыватель 0→1% (добирается до эт.100), но всё ещё
  слабейший — число `PACK_DAMAGE_PER_ALLY`/выживаемость волков требуют доводки.

### Враги — формулы (актуальные, Сессия 33 — НЕЛИНЕЙНЫЕ)
Числа вынесены в константы вверху `EnemySpawner.py` (тюнятся балансером):

hp  = HP_BASE(30) + floor·HP_PER_FLOOR(4) + tier²·HP_PER_TIER2(12)

dmg = DMG_BASE(4) + tier²·DMG_PER_TIER2(2) + floor//DMG_FLOOR_DIV(4)

shld = SHLD_BASE(3) + tier·SHLD_PER_TIER(1)

Рост tier² → ускорение сложности к поздним актам (цель: 100-й почти непроходим).
Группы: 2 врага с эт.GROUP_2_FROM(7), 3 — с эт.GROUP_3_FROM(26); множители на
бойца в группе — GROUP_HP_MULT/GROUP_DMG_MULT (плавный рост суммарной угрозы).

Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

Элита: hp×1.5, dmg×1.4, shld×1.5, shield=shld (стартует со щитом)


### Элитные враги
- Тип узла `"ELITE"` в MapGenerator (вес 5, не появляется на строках 0 и 1)
- `enemy.is_elite = True` флаг на объекте
- Награды: 100% реликвия (25% RARE / 75% UNCOMMON), золото ×1.5
- `handle_click`: `ELITE` → `room_type = "COMBAT"`

### MapView.py — иконки узлов
`_draw_node_icon(screen, ntype, cx, cy, r, fill, border, bw)` — геометрические символы:
- COMBAT: скрещенные мечи | ELITE: корона | CAMPFIRE: костёр
- SHOP: монета "з" | CHEST: сундук | EVENT: "?" | BOSS: череп
- ⚠️ ВЫПОЛНЕНО (Сессия 28): иконки вынесены в `ui/map_icons.py` (132 стр.). MapView.py сокращён до 167 строк.

## Как добавить контент (cookbook)

**Новая карта:**
1. Написать фабрику `create_<name>()` в подходящем модуле `core/cards/` (по стихии/типу: fire/water/poison/heal/buff/debuff/basic), собрав нужные кирпичи-эффекты в `effects=[...]`.
2. Реэкспортировать её из `core/cards/__init__.py`.
3. Куда попадёт в игру: стартовая колода класса (`get_<class>_deck()` в `core/players/<class>.py`), и/или пулы магазина/наград/событий. `CardLibraryView` показывает карты, привязанные к классам.

**Новая реликвия:**
1. Класс-наследник `Relic` в подходящем по теме модуле `core/relics/advanced/` (`bleed_poison`/`shield`/`healing`/`damage`/`utility`; или starter/elemental), переопределить нужные хуки (см. «Реликвии — хуки»). Передать `rarity`. Реэкспортировать из `core/relics/advanced/__init__.py`.
2. Зарегистрировать в `RELIC_POOL[rarity]` в `core/relics/__init__.py` (попадёт в `ALL_RELICS` автоматически).
3. Активная реликвия → `self.is_active = True` + метод `activate(cm)`; клик ловит `InputHandler._handle_combat`.
4. ВСЕГДА проверять `is_player_attack` в `on_damage_calculated`; передавать `combat_manager` в `add_status`/`gain_shield`.

**Новый враг:**
1. Класс-наследник `Enemy` в `core/enemies/`, переопределить `choose_intent()` (через `set_intent(type, value)`). Реэкспорт из `core/enemies/__init__.py`.
2. Зарегистрировать в `ENEMY_REGISTRY` в `managers/EnemySpawner.py` (имя → класс; реэкспортируется из `GameManager`). Статы считает `build_enemy` по формулам этажа/яруса.

**Новый класс игрока:**
1. `core/players/<name>.py`: наследник `Player`, задать hp/energy/gold/`starter_deck_factory`, в `__init__` присвоить `self.active_ability`. Переопределить пассив-хуки при необходимости.
2. Активная способность — класс-наследник `ClassAbility` в `core/players/abilities.py`.
3. Реэкспорт из `core/players/__init__.py`.

**Новое событие:** функции в `ui/events/` (positive/negative/neutral/special) + данные в `event_data.py`, эффекты в `event_effects.py`.

**Новый экран/состояние:** функция отрисовки + запись в `DRAW_HANDLERS` (GameView) и обработчик + запись в `STATE_HANDLERS` (InputHandler).

## Реализованные системы (после Сессии 27)
Все 14 пунктов плана масштабируемости (A–N) ВЫПОЛНЕНЫ.

Реликвии — 21 итого:
- COMMON: LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок
- UNCOMMON: ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник, ШипастаяБроня, ТрофейныйКлык
- RARE: ЭнергоЯдро, СердцеТитана, ГнилойКлык, ЖелезнаяВоля, БерсеркМедальон
- LEGENDARY: ПроклятаяКорона

## Важные детали и грабли
- `on_damage_calculated(base_dmg, is_player_attack=True)` — ВСЕГДА проверять флаг в реликвиях
- `Creature.take_damage(amount, attacker=None, combat_manager=None)`
- `gain_shield` без `combat_manager` — `on_shield_gained` не сработает; всегда передавать cm
- `bleed`: триггер в `take_damage` при `amount>0`; сброс =0 (без ГнилогоКлыка) или //=2 (с ним)
- `vampire`: триггер в `take_damage` при `amount>0` и `attacker.vampire>0`; хил `max(1, amount*2//5)` (40%); `vampire //= 3`
- `regen`: тик в `tick_statuses`, лечит `min(stack, Creature.REGEN_HEAL_CAP_PER_TURN=6)`/тик, затем стак −1
- `distribute_combat_rewards()` → `pending_rewards` → VICTORY
- `CardLibraryView`: карты привязаны к классам, NEW_CARDS упразднён
- `ui/chest/shared.py`: `draw_card_row` возвращает `(card, rect)` или `None`
- `CardRenderer` — фасад в `ui/cards/renderer.py` (импорт `from ui.cards import CardRenderer`). Внутренности: `classifier`/`description`/`keywords`/`data`. Сигнатура `draw`: `(surface, card, x, y, font_title, font_desc, is_hovered=False, player=None, enemy=None)` — НЕ Rect!
- `_EXTRA_KEYWORDS` и палитра карт `_C` — в `ui/cards/data.py`, НЕ в StatusRegistry
- `CombatInterface` — фасад в `ui/combat/interface.py` (импорт `from ui.combat import CombatInterface`); панели в `panels.py`, низ экрана в `bottom.py`, константы в `layout.py`, HUD-хелперы в `hud.py`
- `HubView` — в `ui/hub/` (импорт `from ui.hub import HubView`); CLASS_INFO+геометрия в `data.py`
- `draw_pile_rect` и `discard_pile_rect` — атрибуты GameView, не CombatInterface
- `temp_cost` на карте — временный атрибут Разбойника, живёт только в руке
- `ЖелезнаяВоля`: `is_active=True`, `activate()` вызывается из InputHandler при клике
- `end_turn_rect` пересчитывается каждый кадр в `_draw_end_turn_btn`
- Hover кнопки: прямая проверка `pygame.mouse.get_pos()`, НЕ через `view.hover`
- `VictoryScreen` — в `ui/victory/` (импорт `from ui.victory import VictoryScreen`); `_show_modal` — классовая переменная, сбрасывается в `_proceed()`. Награды-рендер в `rewards_view.py`, модалка в `modal.py`
- `Shop` — в `ui/shop/` (импорт `from ui.shop import Shop`); состояние-машина MAIN/REMOVE, пул карт/цены в `data.py`
- `CardLibraryView` — в `ui/library/` (импорт `from ui.library import CardLibraryView`); списки карт по классам в `data.py` (растут с контентом)
- `HoverState` — в `ui/hover_state.py`; `DRAW_HANDLERS` — в `ui/draw_dispatchers.py` (не в GameView)
- `random.shuffle` в тултипе стопки — НЕ вызывать каждый кадр
- `CombatManager.__init__(player, enemy, starting_deck, game_manager=None)`
- `RARITY_COLORS` импортировать из `core.rarity`
- `on_wet_applied` — через `Creature.add_status`, НЕ напрямую
- `bonus_draw` — `getattr` с дефолтом 0
- `ui/chest/` — маленькая c: `from ui.chest import ...`
- `pygame.display.flip()` — один раз в конце `GameView.draw()`
- `EventView.py` — НЕ класс, только функции
- `self.relics` (не `self.player_relics`!) в GameManager
- `tick_statuses` принимает `combat_manager=None` — всегда передавать `self` из CombatManager
- `spawn_procedural_enemy` — МЕТОД GameManager, не импортировать из core.enemies
- `_elemental_blocked` проверяется в `Creature.add_status` только если `self is combat_manager.enemy`
- `RogueAbility._penalty_pending`: `on_turn_start` снимает -1 энергию ПОСЛЕ восстановления
- `BerserkerAbility`: урон себе напрямую в `hp` (сквозь щит), не через `take_damage`
- Смерть игрока централизована в `CombatManager.check_player_defeat()` — вызывать после любого нового источника урона игроку в его ход (не только в `end_turn_phase`)

## Правила работы
- Файлы проекта читаются и правятся напрямую в локальной рабочей копии (ветка `dev`).
- При изменении логики/контента — синхронно обновлять этот файл (`_project_map.md`): затронутые «Ключевые системы» и «грабли».
- Заметные изменения (контент, фиксы, фичи) фиксировать записью в `PATCHNOTES.md`.
- Коммитить/пушить — только по явной просьбе пользователя.

## Аудит Сессии 28 (Jun 3, 2026) — находки

### Баги (по приоритету) — ✅ ИСПРАВЛЕНЫ в Сессии 28
1. ✅ **СРЕДН — Берсерк «зомби-ход».** Логика смерти игрока вынесена в `CombatManager.check_player_defeat()` (вызывается в `end_turn_phase` И в `InputHandler._handle_combat` после `ability.activate()`). Теперь смерть от собственной способности сразу переводит в `LEADERBOARD`. (Побочно: CombatManager.py разросся до 159 строк — кандидат на разбивку.)
2. ✅ **НИЗК — `Друид.on_heal_passive`.** Теперь `add_status('poison', healed_amount, combat_manager)` (druid.py:39).
3. ✅ **НИЗК — мёртвый флаг `_intercepted` в ГнилойКлык.** Удалён флаг и лишние оверрайды `on_bleed_tick`/`on_turn_start` (база возвращает то же); логика уполовинивания осталась в `Creature.tick_statuses`.

### Дизайн-вопросы (не баги)
- Комбо ПАР не срабатывает, если урон и `wet` в ОДНОЙ карте (эффекты применяются по порядку: DamageEffect считает урон до того, как StatusEffect наложит wet). Возможно намеренно.
- `Заплатка._applied` — +5 max_hp применяется один раз за объект реликвии (на первом `on_combat_start`), сохраняется между боями. Корректно, но проверить, что реликвия не дублируется в пуле.

### Мёртвый код — ✅ УДАЛЕНО в Сессии 28
Легаси корня `core/` (`Card.py`, `Relic.py`, `enemy.py`, `player.py`, `items.py`) удалены — заменены модульными `core/cards/`, `core/relics/`, `core/enemies/`, `core/players/`. Рабочие файлы корня `core/`: `Creature.py`, `EffectCalculator.py`, `StatusRegistry.py`, `rarity.py`.

### Проверено и ОК
Битых импортов нет. Сигнатуры всех 13 хуков реликвий/способностей совпадают (определение vs вызов). Циклов нет (отложенные импорты в ui/ обоснованы). Динамические атрибуты (`_iron_will_shield`, `temp_cost`, `bonus_draw`, `_elemental_blocked` и пр.) читаются через `getattr` с дефолтом — AttributeError не грозит. Порядок хода, шипы/вампиризм/bleed, dry_run в EffectCalculator — корректны.

### Инфраструктура (Сессия 28)
- Добавлен `.github/workflows/ci.yml` — CI на GitHub Actions (lint ruff + compileall + import-проверка + BalanceSimulator). Запуск на push/PR в dev/main. Pygame в CI НЕ ставится (ui/ проверяется компиляцией).
- Добавлен `requirements.txt` (pygame, pillow, requests).
- Исправлен мёртвый недостижимый код в `VampireDamageEffect.execute` (core/cards/base.py) — ловился линтером CI.

## Задачи для будущих сессий

### Приоритет 1 — ✅ ВЫПОЛНЕНО в Сессии 30
1. ✅ **Инвентарь реликвий в бою** — реликвии-чипы уезжали за край экрана. Сделаны компактные
   бейджи (помещаются 19+) + панель-оверлей `RelicPanel` по клику на «АРТЕФАКТЫ»/«+N»
   (см. «Реликвии — UI в бою»). Скролл панели при очень большом пуле — возможный follow-up.

### Приоритет 2 (рефакторинг) — ✅ ВЫПОЛНЕНО в Сессии 29
Все три стадии плана рефакторинга крупных файлов завершены:
- ✅ **Stage 1** (контент-ядро): abilities.py→пакет, relics/advanced.py→пакет (по теме), GameManager god-object разобран (EnemySpawner + RewardManager, 266→145).
- ✅ **Stage 2** (крупный UI): HubView→`ui/hub/`, CombatInterface→`ui/combat/` (+мёртвый дубль `draw_ability_slot` удалён), CardRenderer→`ui/cards/`.
- ✅ **Stage 3** (остальной UI): Shop→`ui/shop/`, GameView разнесён (`draw_dispatchers`/`hover_state`/`combat/hover`, 271→140, мёртвый `_draw_placeholder` удалён), VictoryScreen→`ui/victory/`, CardLibraryView→`ui/library/`.

Оставлено намеренно (UI-render под мягким потолком 220 / цельные оркестраторы): `MapView.py` (167, цельный render, делегирует в `map_icons.py`), `core/Creature.py` (184), `ui/combat/hud.py` (252), `managers/CombatManager.py` (159), `ui/combat/panels.py` (157).

🧹 Остаточный долг: ~64 предсуществующих неиспользуемых импорта (ruff F401) по проекту — не в CI-наборе; разово почистить `ruff --select F401 --fix`.

### Выполнено (было отложено; Сессия 31)
- ✅ Мульти-враги: группы 1–3 врагов по этажу, компактные панели, on_kill хук
- ✅ Союзники: Summon (Creature), карты призыва, авто-атака, центральная зона
- ✅ Таргетинг: клик-выбор цели, жёлтая рамка
- ✅ `on_kill`-реликвии: ТрофейныйКлык (UNCOMMON, +1 Сила), БерсеркМедальон (RARE, +1 Энергия)

## Статус
Сессия 27 завершена (Jun 3, 2026).
Сессия 28: настроен GitHub CLI + CI, проведён аудит зависимостей/логики.
Сессия 29 (Jun 4, 2026): рефакторинг крупных файлов (Stage 1–3).
Сессия 30 (Jun 4, 2026): инвентарь реликвий в бою (бейджи + панель).
Сессия 31 (Jun 4, 2026): **мульти-юниты (враги + союзники) в 4 фазы.**
- Фаза 1: `self.enemies: list` + compat-свойство `enemy` + `on_kill` в `_check_enemy_death`
- Фаза 2: `build_enemy_group` (1–3 врага), компактные вражеские панели
- Фаза 3: `Summon(Creature)` + `SummonEffect` + карты призыва, панели союзников в центре
- Фаза 4: `TargetingSystem` (клик по врагу = выбор цели) + ТрофейныйКлык + БерсеркМедальон
- Новые файлы: `core/Summon.py`, `core/cards/summon.py`, `ui/combat/targeting.py`
- Тесты: 128 (было 56). ALL_RELICS: 19 → 21.

Сессия 32 (Jun 4, 2026): **классовые пулы карт + класс Призыватель (каркас) + балансер.**
- Каталог карт `core/cards/catalog.py` (generic ↔ классовые), `Card.card_class`
- Пулы выдачи (магазин/сундук/события) по классу игрока через `get_pool_for_class`
- Класс Summoner (HP60/эн3) + способность «Подкрепление»; 6 классов в хабе (250px)
- Балансер переписан: сквозной забег (`managers/balance/`), отчёт по кривой сложности
- Коммиты: `403dcb1`, `81149a3`. Тесты 128/128.
- ⚠️ TODO Сессии 33 (по находкам балансера): фикс пассива Друида (хил→яд ∞),
  прогрессия бота в балансере, перезамер, тюнинг формул врага под «скейл к 100».