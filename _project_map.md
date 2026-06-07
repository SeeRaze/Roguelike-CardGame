# _project_map.md
_Последнее обновление: Сессия 36, Jun 4, 2026_
_История изменений по версиям — в `PATCHNOTES.md`._

## Архитектура
- `core/` — вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py, Summon.py)
- `ui/` — вся отрисовка. Пакеты: `cards/` (CardRenderer), `combat/` (CombatInterface+HUD, targeting), `hub/` (HubView), `shop/` (Shop), `victory/` (VictoryScreen), `library/` (CardLibraryView), `chest/`, `events/`; модули: GameView.py (+`draw_dispatchers.py`, `hover_state.py`), MainMenu.py, MapView.py, LeaderboardView.py, Campfire.py.
- `managers/` — CombatManager, DeckManager, GameManager, MapGenerator, network_manager, EnemySpawner, RewardManager, SaveManager
- Разрешение: строго 1920×1080 Full HD
- **Ветка разработки: dev** (main — стабильная, dev — активная работа)

## Железные ГОСТы (ревизия С49 — единая философия для логики и UI)
**Настоящий инвариант — ОДНА ОТВЕТСТВЕННОСТЬ на файл, никаких «божественных объектов».**
Число строк — это ПРОКСИ к нему, а не самоцель. (Старый «жёсткий лимит 150 для логики»
устарел: проект вырос, и здоровые когезивные модули — `EffectCalculator` 270 «вся боевая
математика», `Creature` 241, `forge` 305, `positioning` 281 — нельзя резать без размазывания
единого смысла. Душить ради цифры — анти-цель.)
- **150 строк = триггер ПОСМОТРЕТЬ** (везде, и логика, и UI), НЕ жёсткий гейт. Повод спросить
  «файл всё ещё про одно?», а не повод механически делить.
- **Мягкий потолок когезивного модуля ~250.** Выше — ОБЯЗАТЕЛЬНЫЙ разбор: это ещё одна
  ответственность (→ вынести по реальному шву) или законный единый смысл (→ оставить,
  задокументировать почему). Резать ТОЛЬКО по настоящему шву, НИКОГДА ради цифры.
- **Благословлены как когезивные** (150–250, одна ответственность, не трогать ради размера):
  `EffectCalculator` · `Creature` · `forge`/`ForgeRegistry` · `positioning` · `cards/base` ·
  `GameManager` · `SaveManager` · `StatusRegistry` · `DetonationRegistry`. В balance/ —
  `policy`/`forge`/`runner`/`builds` (симуляция, своя плотность).
- **Реальный флаг = god-object** (делает 6+ вещей), не просто «большой файл». Текущий разбор
  С49: `managers/CombatManager.py` (619) → тонкий оркестратор `managers/CombatManager.py` +
  миксины `managers/combat/` (positioning/cardplay/phases/resolution/defeat).
- **UI делим ПО СМЫСЛУ.** Эталон — `ui/chest/`: `data` (константы/пулы, без pygame) ·
  `rendering`/`shared` (функции `draw_*`) · `handlers` (клики) · `base`/`__init__`
  (оркестратор + реэкспорт). У файла-оркестратора/рендера тот же мягкий потолок.
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

### Экономика (Этап C, Сессия 38+)
- **Костёр** (`ui/Campfire.py`, sub_state MAIN/FORGE/SACRIFICE): 5 опций —
  Отдых (хил = 30% недостающего HP, `Creature.rest_heal_amount`), **Кузница**
  (ковка карт за FP: +1 уровень, растущая цена, авто-тег на майлстоунах 5/10/15,
  Гипер-заряд >15 — `core/forge.forge_card_one_level`; мульти-ковка за визит,
  «← ГОТОВО»), **Закалка** (FP→+20% max_hp+лечение), **Заточка** (FP→×урон),
  **Ритуал крови** (удалить карту за −10 HP сквозь щит, `Creature.lose_hp`; кнопка
  гаснет при HP≤цены / ≤1 карты). Продвижение по этажу — за Отдыхом/Ритуалом
  (`setup_next_floor`); стоки FP (Кузница/Закалка/Заточка) — параллельны.
- **Урон сквозь щит**: `Creature.lose_hp(amount)` — прямо в HP минуя `shield`, без
  боевых хуков. Идиом: `berserker.py`, `DetonationRegistry`, яд. Реюз для будущего
  (Проклятый сундук, карты «Истязания»).
- **Магазин** (`ui/shop/`): витрина = 5 карт (`data.pick_cards`) + слот реликвии
  (`data.pick_relic`→`RewardManager.pick_shop_relic`, фильтр имеющихся, цена по
  редкости+этаж `get_relic_price`) + покупка ключа (`get_key_price` 30, беск. запас)
  + утилизация (`get_removal_price` = `(15+floor·2)+removal·25`, ×2 от «Проклятой
  Короны») + выход. Состояние-машина MAIN/REMOVE. `main_view.draw_main` → хелперы
  `_draw_cards`/`_draw_relic_slot`/`_draw_key_slot`/`_draw_rob_button`. Выход —
  общий `Shop._leave` (reset + след. этаж).
- **Ограбление** (`Shop._rob`, кнопка под слотом реликвии): риск-механика — шанс
  `ROB_SUCCESS_CHANCE`(0.30) забрать реликвию бесплатно и сбежать; провал →
  `current_state="COMBAT"` + `spawn_procedural_enemy(is_elite=True)` (элитный страж,
  этаж продвинет победа).
- **Sim-моделирование экономики** (`managers/balance/economy.py`, шаг №6 фреймворка):
  до C3 симулятор НЕ видел золото/удаление. `EconomyPolicy` — слой между-боевых
  решений (зеркало `BotPolicy`): `on_combat_won` копит золото (`gold_reward` =
  зеркало `RewardManager.build_rewards`: `randint(20,35)+floor·3`, элита ×1.5,
  Корона→0), `between_acts` (у костра) тратит на удаление слабейшей карты
  (`_removal_target` по `_card_score`, тай-брейк — нетематичная). `_StubGM` получил
  поля `player_gold/keys/removal_count` + `get_removal_price` (зеркало GameManager).
  `run_single_run(..., economy=None)` по умолчанию ВЫКЛ (A/B «с/без» чист);
  `BalanceSimulator.run_dual(economy=...)` вливает в обе метрики. **Замер-вывод:**
  прореживание — почти нейтральный рычаг (свип `MAX_REMOVALS_PER_ACT` 1→4 двигает
  медиану на ±1-2 этажа, в шуме): цена удаления растёт быстро + добор 5/ход с
  перемешиванием → потеря 1-3 слабых карт из ~30 не ускоряет сборку компаунда.
  Реальный регулятор скорости сборки — драфт реликвий/карт (уже моделируется), не
  прореживание. → [[balance-findings-economy-thinning]].
- **Регресс-гард баланса** (`managers/balance/baseline.py`): пиннит медианы wall/
  ceiling каждого класса к эталону `BASELINE` (econ OFF, seed=99, N=40). Ловит
  обвал класса при добавлении контента (просадка > `BASELINE_MAX_DROP`=6) и
  баг-всплеск (рост > `BASELINE_MAX_RISE`=12, напр. несброс статусов). Запуск:
  `python -m managers.balance.baseline --check` (CI, plain-python без pytest) или
  `pytest -m balance` (локально; дефолтный `pytest` его пропускает через addopts
  `-m "not balance"`). Переблагословить эталон: `python -m managers.balance.baseline`.
- **Индекс рычагов баланса** — `_balance_knobs.md`: единая справочная карта ВСЕХ
  тюнинг-констант (кривая врага / статусы / детонации / движки классов / экономика /
  параметры сима). Точечная балансировка: правишь константу на месте → гоняешь гард.
- **Сводка аудитов** — `AUDIT.md`: единая точка входа «что не идеально» —
  латентные неточности, приближения симулятора, открытые механики, решённое
  (для истории). Обновляется при новой находке/закрытии пункта.

## Полный список файлов (актуально на Jun 3, 2026 — после Сессии 28)
main.py, server.py, _project_map.md, _balance_knobs.md, PATCHNOTES.md, requirements.txt, .github/workflows/ci.yml

core/rarity.py, core/Creature.py, core/EffectCalculator.py, core/StatusRegistry.py, core/ComboRegistry.py, core/DetonationRegistry.py, core/ForgeRegistry.py, core/forge.py

core/cards/init.py, base.py, basic.py, fire.py, poison.py, water.py, shock.py, earth.py, air.py, heal.py

core/cards/buff/init.py, strength.py, thorns.py, regen.py, vampirism.py

core/cards/debuff/init.py, vulnerable.py, weak.py, bleed.py

core/enemies/init.py, base.py, cultist.py, slime.py, boss.py

core/enemies/bosses/init.py, base.py, guardian.py, archivist.py, elemental.py, keeper.py, architect.py

core/enemies/elites/init.py, base.py, spell_eater.py, plague.py, butcher.py, devourer.py

core/players/init.py, base.py, mage.py, rogue.py, warrior.py, druid.py, berserker.py, summoner.py

core/players/ability.py (базовый ClassAbility)

core/players/abilities/init.py, warrior.py, rogue.py, mage.py, druid.py, berserker.py, summoner.py (один файл на способность)

core/relics/init.py, base.py, starter.py, elemental.py

core/relics/advanced/init.py, bleed_poison.py, shield.py, healing.py, damage.py, utility.py (по теме)

managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py,

     MapGenerator.py, network_manager.py, EnemySpawner.py, RewardManager.py

managers/balance/init.py, bot.py, runner.py, report.py, builds.py, economy.py, baseline.py, forge.py, events.py, sweep.py (симуляция баланса — Сессия 32, метрика ceiling — Сессия 36, экономика+регресс-гард — Сессия 38, прокачка карт+триединство+Заточка — Сессия 39; С39.5: чистый слой ковки поднят в `core/forge.py` = общий источник правды, здесь только бот-политика ForgePolicy)
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
Единый реестр всех 17 статусов:
vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire,
shock, shatter, echo, barrier, mastery, frenzy, virulence
- **echo** (Сессия 37, движок кат.4): is_stack на ИГРОКЕ. Каждая разыгранная карта
  срабатывает повторно за каждый заряд Эха, после чего заряд тратится. Хук —
  в `CombatManager.play_card_by_index`. Чистый множитель: карта с уроном 6 под эхом 2
  наносит 6×3=18. Не в `_ELEMENTAL_KEYS` (не стихия, мета-механика).
- **barrier** (Сессия 37, движок кат.4 для Воина): is_stack на ИГРОКЕ. Несгораемый
  щит — при ежеходном сбросе `shield = carry + barrier`. Каждый стак = +1 щита
  КАЖДЫЙ ход. Хук — в `CombatManager.start_turn_phase`. Синергия: барьер → shield
  floor растёт → Возмездие (щит→урон) бьёт сильнее. Компаунд: защитные скиллы
  усиливают ВСЕ будущие ходы.
- **mastery** (Сессия 37, движок кат.4 для Мага): is_stack на ИГРОКЕ. +N к урону
  всех атак до конца боя (плоско, шаг 2c EffectCalculator, только атаки игрока).
  Растёт от комбо: пассив Мага при `_combo_triggered` даёт +1. Компаунд: комбо →
  +урон → больше комбо. Не в `_ELEMENTAL_KEYS`.
- **frenzy** (Сессия 37, движок кат.4 для Разбойника): is_stack на ИГРОКЕ. +N к
  каждому накладываемому Кровотечению (`BleedEffect` читает `player.frenzy`). Растёт
  +1 за каждую сыгранную атаку (пассив Rogue). Врождённо: bleed Разбойника убывает
  ВДВОЕ (а не в ноль) в `Creature.tick_statuses` → наложения копятся. Компаунд:
  темп атак → растущий dot. Сим-артефакт: бот не пилотирует (как shock-dilution).
- **virulence** (Сессия 37, движок кат.4 для Друида): is_stack на ИГРОКЕ. +N к
  каждому накладываемому Яду (`PoisonEffect` в base.py читает `player.virulence`).
  Растёт +1 за каждый сыгранный СКИЛЛ (пассив Druid). Врождённо: яд Друида ЗАГНИВАЕТ
  — не убывает на враге в `Creature.tick_statuses` (чек класса + `self is not player`,
  чтобы яд на самом Друиде убывал) → наложения копятся. Компаунд: темп скиллов →
  растущий dot → «Токсичный взрыв» детонит огромный стак. Сим-артефакт: бот не
  пилотирует (как frenzy); вдобавок Друид ограничен ВЫЖИВАЕМОСТЬЮ (обрыв HP ~эт.20),
  а не уроном — оффенс-движок не пробивает защитную стену.
- **Все 5 движков** (echo/barrier/mastery/frenzy/virulence) сбрасываются между боями
  через `Player.reset_combat_statuses()` — компаунд ВНУТРИбоевой (персистентность по
  забегу — отдельный слой, шаг 5 framework). Шаг №4 framework закрыт: все 6 классов
  имеют движок кат.4 (+ Свора Призывателя как кат.5).
- **shock** (Сессия 36, стихия «Молния»): is_stack, НЕ тикает в конце хода —
  расходуется при УДАРЕ (+`EffectCalculator.SHOCK_DAMAGE_PER_STACK`=3 урона за удар,
  −1 заряд). Архетип микро-атак: каждый отдельный `DamageEffect` дренит свой заряд.
  НЕ в `_ELEMENTAL_KEYS` (барьер Мага его не трогает).
- **shatter** (Сессия 36, стихия «Земля»): is_duration (тикает в duration-петле
  `tick_statuses` вместе с vulnerable/weak/wet). Пока у цели есть ЩИТ — она получает
  урон ×`EffectCalculator.SHATTER_MULT`=3 (контра броне). Множитель-ЧТЕНИЕ, заряды
  при ударе не тратятся.

### EffectCalculator.py
Единая точка боевой математики — И боевой удар, И превью на карте, И проекция на
HP-баре зовут её (расхождений «показано vs нанесётся» нет, аудит механик С40).
- **`dry_run` гасит ТОЛЬКО побочки** (логи / расход зарядов Шока и стаков комбо /
  запись `max_damage_dealt`). Все ДЕТЕРМИНИРОВАННЫЕ множители считаются всегда → превью
  с реальным контекстом = фактический удар. Флаги `include_reactions`/`include_forge`
  убирают комбо/forge-теги из «гарантированного» числа карты (они идут чипами).
  `card_override`/`snapshot_override` — контекст ковки для превью без живых транзиентов.
  `breakdown` (list) — пошаговый разбор для тултипа.
- **`EffectCalculator.preview(player, target, base, combat_manager, game_manager, card)`**
  — разбор для UI: `guaranteed` (число карты), `full` (проекция), `reactions` (чипы
  комбо), `forge_mult`/`forge_tags` (чип ковки), `steps` (тултип «Расчёт урона»).
- Обновляет `gm.stats["max_damage_dealt"]`
- Определяет `is_player_attack`, передаёт в `on_damage_calculated(base, is_player, dry_run)`
  (реликвии с одноразовым зарядом не тратятся в превью)
- **Шаг 2c — Мастерство** (Маг): если атакует игрок и `attacker.mastery>0`,
  +mastery к базовому урону (плоско, до уязвимости/комбо). Движок кат.4.
- **Шаг 4b — Раскол**: если `target.shatter>0` И `target.shield>0`, урон
  ×`SHATTER_MULT`(3) (после уязвимости, множится с ней и с комбо). Условие на щит
  проверяется в момент удара → при мульти-хите бонус пропадает, как только щит сбит.
  Заряды не тратятся (статус-длительность).
- **Шаг 6 — Шок**: если у цели `shock>0`, +`SHOCK_DAMAGE_PER_STACK`(3) к урону
  ПЛОСКО (после уязвимости/комбо, чтобы не множился), и −1 заряд. `dry_run` бонус
  показывает, но заряд НЕ тратит.
- **Шаг 8 — Заточка** (С39.4, sim-движок прокачки): если атакует игрок,
  урон ×`player.atk_mult` (компаунд-множитель, копится ковкой «Заточка» на костре).
  Считается и в `dry_run` (детерминирован, без побочек) → виден в превью. Живёт весь
  забег как `max_hp`; инертен при `atk_mult=1.0` ⇒ без ковки не влияет.
- **Шаг 8-bis — Долг энергии** (С46, §7 долговой движок): если атакует игрок и
  `player.energy<0` (овердрафт), урон ×`energy_debt_multiplier(-energy)` (`core/debt.py`,
  линейная кривая по умолч., экспонента рубильником `DEBT_CURVE_MODE`). Считается и в
  превью (показывает заём силы); инертен при `energy>=0` ⇒ без овердрафта не влияет.

### UI урона — ясность (аудит механик С40)
- **Число на карте = гарантированное** (`EffectCalculator.preview().guaranteed`): баффы
  игрока + дебаффы врага + Заточка + уровень ковки. Условные комбо/forge — НЕ в числе.
- **Чипы реакций** (`CardRenderer._draw_reaction_chips`): цвет + ×значение (синий=комбо,
  оранж=ковка), только когда сработают против текущей цели. Полный разбор — в ховер-
  тултипе (`keywords.draw_card_keyword_tooltip`, блок «Расчёт урона»).
- **Проекция урона** (`CombatInterface._card_projection` → `draw_enemy_panels`): полный
  урон на HP-барах — цель (одиночные) / все (AoE-Возмездие), с учётом щита.
- **Строка ресурсов** (`ui/resource_hud.py`, рисуется в `GameView.draw` поверх экрана):
  HP/Золото/FP слева-сверху единым видом на ВСЕХ экранах забега (COMBAT/MAP/EVENT/
  CAMPFIRE/SHOP/CHEST). Бейджи реликвий — только ВНЕ боя (в бою реликвии в панели героя
  `draw_player_panel`; верхняя плашка `draw_relic_bar` убрана из боя — определение
  мёртвое). Карта: башня-инфо уведена вправо (`MapView`), верх-лево под строку.

### Комбо — ДВА реестра (два архетипа)
Стихийные синергии живут в двух data-driven реестрах (каждое комбо = одна запись):
- **`core/ComboRegistry.py` — МНОЖИТЕЛЬНЫЕ** (×N к урону ТЕКУЩЕЙ атаки). Запись:
  `{requires, multiplier, consume, log}`. Срабатывает в `EffectCalculator.calculate_damage`
  (шаг 5): если все requires-статусы цели >0 → урон ×multiplier, снять `consume` стаков.
  Пример: ПАР (wet+ignited ×3.0). Поднимает `cm._combo_triggered` (пассив Мага).
- **`core/DetonationRegistry.py` — ДЕТОНАЦИОННЫЕ** (мгновенный эффект: бурст/AoE/
  обнуление щита), Сессия 36. Запись: `{name, requires, handler(target, cm), log}` —
  `handler` сам делает эффект и снимает потраченные статусы. Срабатывает через
  эффект-кирпич **`DetonateEffect`** (карты-детонаторы): подрывает ВСЕ готовые
  детонации на цели. Бурст — RAW `take_damage` через хелпер `_deal_raw` (НЕ через
  EffectCalculator, чтобы не рекурсить Шок/комбо — **инвариант реентерабельности**).
  **Порядок — по явному полю `priority`** записи (electro 10 · thermo 20 · lava 30 ·
  acid 40 · poison 50), обход через `ReactionOrder.order_keyed` (НЕ позиция в dict);
  requires проверяется заново перед каждым handler → потратившая общий статус
  детонация гасит зависимые. 5 детонаций:
  - **Электро-взрыв** (wet+shock): Шок×`ELECTRO_DAMAGE_PER_SHOCK`(6) AoE, снять wet+shock.
  - **Термовзрыв** (ignited+shock): (Горение+Шок)×`THERMO_DAMAGE_MULT`(3) по цели, снять оба.
  - **Лава** (shatter+ignited): Горение×`LAVA_DAMAGE_PER_IGNITE`(4) + намерение атаки //2, снять оба.
  - **Кислота** (wet+poison): щит цели → 0, снять wet (яд ОСТАЁТСЯ тикать).
  - **Ядовзрыв** (poison+ignited): весь Яд уроном СКВОЗЬ щит (в HP), снять Яд, Горение ×2.
  - Карты-детонаторы: «Перегрузка» (shock.py, урон+детонация), «Катализатор»
    (basic.py, нейтральный, чистый триггер). **Новая детонация = одна запись (+ опц. карта).**
- Пассив Берсерка: бонус = `int((1 - hp/max_hp) * 10)`, применяется между шагом 2 (ярость) и шагом 3 (слабость), только `is_player_attack` и `type(attacker).__name__ == "Berserker"`

### Порядок реакций и предохранитель глубины (ревизия ядра, Сессия 43)
Все боевые реакции разрешаются по ЕДИНОМУ порядку и под ЕДИНЫМ предохранителем —
две ортогональные гарантии: порядок = детерминизм, гард = конечность каскада.
- **`core/ReactionOrder.py`** — единый источник правды о ПОРЯДКЕ. `ReactionPriority`
  (IntEnum): COMBO=10 · SHOCK=20 · FORGE_TAG=30 · DETONATION=40 · ECHO=50 ·
  STATUS_TICK=60 · RELIC_HOOK=70 · ENEMY_HOOK=80 (зазоры под вставку). `order_keyed(
  records, priority|func)` — детерминир. сортировка реестра по `(приоритет, ключ)`,
  стабильна независимо от dict-порядка. Комбо и детонации обходятся через неё.
- **`core/forge.TriggerGuard`** (`MAX_TRIGGER_DEPTH=5`) — ПОТОЛОК глубины каскада.
  Розыгрыш карты: `depth=0` перед первичным apply (он «бесплатен»), эхо-ретриггеры
  и детонации тратят бюджет суммарно. Post-хуки (реликвии/враги) — отдельное событие
  (сброс `depth=0`), под `CombatManager._guarded`. Фаза врага (`end_turn_phase`):
  каждое верхнеуровневое действие (намерение/тики/действие союзника) — через
  `_guarded_action` (сброс `depth=0` + `_guarded`). Так ВСЕ реакционные пути
  защищены от взаимной рекурсии будущих хуков (а не только эхо+детонации).
- **Инвариант реентерабельности**: бурст детонаций идёт RAW (`_deal_raw`→`take_damage`),
  НЕ через `EffectCalculator` → детонация не реентерит Шок/комбо. Если в будущем
  понадобится цепная детонация (детонация запускает детонацию), её надо провести
  централизованно через `_guarded`, а не вызывать handler напрямую.

### RuleStack — слой «правок правил» (фундамент «слома игры»)
Полная спека: `_rulestack_design.md` (корень). Обобщение паттерна реестров +
`ReactionOrder` + `TriggerGuard` с уровня боя на ВЕСЬ забег. Базовый забег = пустой
стек (точки врезки вшиты с первого фрейма, при пустом стеке — no-op). Парадокс-режим
(автоматический push хаотичных правил) — СКРЫТЫЙ режим (анлок), эмерджит позже.
- **`core/rules/RuleStack.py`** — `Scope` (IntEnum, КОГДА срабатывает правило:
  DECKBUILD=10 · RUN=20 · ROOM_ENTER=30 · COMBAT_START=40 · TURN_START/END=50/60 ·
  REACTION=70 · DAMAGE=80 · ON_DEATH=90, зазоры под вставку) + `RuleMod` (атом слома:
  id/name/scope/priority/source/cost/predicate/apply, мутирует ctx) + `RuleStack`
  (push/pop/clear/active/total_cost/mods_for/apply). Чистый модуль, без pygame.
- **Точка врезки (срез):** `EffectCalculator.calculate_damage` после Заточки зовёт
  `gm.rulestack.apply(Scope.DAMAGE, ctx)` — внешний слой глобальных правок урона.
  Инертно при пустом стеке / `gm` без `rulestack` (симулятор-стаб). Прочие scope
  врезаются по мере появления потребителя (YAGNI).
- **Ставки/Анте** (`core/rules/stakes.py`) — первый КОНТЕНТ слома, опт-ин сложность
  базовой игры (Balatro/Ascension). Калибровка С46 = **true ascension** (роняют
  выживаемость; награда за риск = Энтропия позже, не урон). `Stake` = именованный
  бандл `RuleMod`. «Аскет» (DECKBUILD ≤6 карт, БЕЗ урон-награды), «Хрупкость»
  (DECKBUILD 30% макс. HP + DAMAGE ×1.25). Находка: ось «лимит карт» структурно не
  штраф (консистентность), универсальна только ось HP. `Stake.activate(gm)`: пушит
  моды + применяет СВОИ одноразовые DECKBUILD-моды напрямую (НЕ `rs.apply` над всем
  стеком). Реестр `STAKES`. Числа: `_balance_knobs.md` §8.
- **Владение/активация:** `GameManager.rulestack` (пустой с `__init__`) +
  `pending_stakes` (выбор в Хабе) → `activate_pending_stakes()` на старте забега (ДО
  хила). Тогглы — `ui/hub/base.py::_draw_stake_toggles`.
- **Сим-нативность** (козырь): `runner.run_single_run(stakes=...)` + `_StubGM.rulestack`
  → бот «надевает» правила, дуал-сим меряет выживаемость сломанного рулсета.
  `stakes=None` регресс-нейтрально (baseline зелёный).

### Долговой движок — овердрафт ресурсов (§7 С46 + §4 С49) — `core/debt.py`
«Power now, pay later»: ресурс уходит в МИНУС при розыгрыше (овердрафт) → глубина долга
даёт множитель урона → расплата. «Вторая экспонента» риск-driven. ДВА ресурса:
- **`core/debt.py`** (чистый модуль) — общая pure `_debt_multiplier(depth, mode, per_point,
  exp_rate)` + обёртки по ресурсу (читают свои ручки живьём → рубильник exp per-resource):
  `energy_debt_multiplier` (ручки `DEBT_*`) и `hp_debt_multiplier` (ручки `HP_DEBT_*`).
  Числа: `_balance_knobs.md` §9.
- **Долг ЭНЕРГИИ (С46):** `Creature.use_energy(allow_debt)` пускает энергию в минус; гейт
  `play_card_by_index` при `player.energy_overdraft` до `DEBT_MAX_OVERDRAFT`. Множитель —
  шаг 8-bis `EffectCalculator`. Гашение — `_settle_energy_debt` в `end_turn_phase`
  (`lose_hp(долг × DEBT_HP_INTEREST)` сквозь щит, под `_guarded_action`).
- **Долг HP (С49, субстрат Берсерка «Отрицание Смерти»):** `Creature._hp_floor()` =
  `-HP_DEBT_MAX_OVERDRAFT` при `player.hp_overdraft` (иначе 0) — клампы `lose_hp`/
  `take_damage`/шипы/кровь пускают HP в МИНУС. Множитель — шаг 8-ter `EffectCalculator`
  (`hp<0`). Смерть `defeat.check_player_defeat` на ДНЕ (`hp<=_hp_floor()`) — игрок ВЫЖИВАЕТ
  в минусе. Хук-сеам `phases._settle_hp_debt` (NO-OP; класс Берсерка переопределит
  `player.on_hp_debt_settle` — грация-ход + |HP|→FP при победе). Всё инертно без флага.
- **Живая активация (§4):** Ставка **«Кровавый Кредит»** (`core/rules/stakes._EnableDebt`,
  DECKBUILD run-setup) ставит `energy_overdraft`+`hp_overdraft` на игрока на забег → долг
  доступен в РЕАЛЬНОМ бою (до этого жил только в симе). Авто-тоггл в Хабе.
- **Сим-нативность** — оси РАЗВЯЗАНЫ: `run_single_run(debt=...)` (энергия) и `hp_debt=...`
  (HP) — чистый A/B по каждой; `bot.py` floor-aware (`_hp_floor()`). Оба False → baseline
  зелёный. Энергия A/B: размен-движок (Воин +16.5 … Призыв −9.5). HP-долг: «стол» на
  глубине (классы со щитом неубиваемы → медиана неинформативна) — механика в юнит-тестах.

### Трупы на сетке (субстрат Некроманта, С49) — `core/corpse.py`
Павшее существо НЕ исчезает бесследно → пассивный ТРУП: помечается тегом `[Corpse]`,
сохраняет 2D-координату (`rank/line`), продолжает занимать клетку (блокирует будущие
свапы), пока его не ПОГЛОТЯТ/ВЗОРВУТ (механики Некроманта/детонаций — придут с классом).
- **`core/corpse.py`** (чистый модуль): `CORPSE_TAG` + pure-ридеры `mark_corpse`/
  `is_corpse`/`corpses_in` + предикат `cell_has_corpse(creatures, rank, line)` (клетка
  занята трупом — под будущие перемещения/свапы).
- **Реализация = ТЕГ на павшем враге**, НЕ отдельный объект: мёртвый враг и так остаётся
  в `self.enemies` (hp<=0), поэтому труп = тот же объект + метка → без дублирования
  состояния (урок бага `cm.enemy` С45). Врезка — `_check_enemy_death` (единая точка
  гибели врага) метит труп один раз. `CombatManager.corpses` — view павших.
- **ИНЕРТНО** (как 2D-субстрат позиционки до §1): трупы помечаются, но потребителей
  (поглощение/взрыв) нет; `victory=all(hp<=0)` и таргетинг (фильтр живых) НЕ тронуты →
  baseline зелёный.

### Позиционка — 2D-сетка РАНГ × ЛИНИЯ (кейстоун, С47 v1 → С48 v2) — `core/positioning.py`
Субстрат Парадокс-режима и class-redesign. **2D-решётка на ОБЕИХ сторонах**: ось РАНГА
(фронт/тыл) × ось ЛИНИЙ (лево/центр/право). МЕХАНИЗМ class-agnostic. Сетка = ИНДЕКС над
`enemies[]`/`allies[]`, НЕ новый источник правды (анти-рассинхрон). Всё аддитивно/инертно
при `rank/line == None`.
- **`core/positioning.py`** (чистый модуль):
  - **Ось РАНГА (v1)** — `Rank` (FRONT/BACK) + раскладки `DEFAULT_LAYOUT`/`MIRRORED_LAYOUT` +
    `front_rank`/`back_rank` + **`intercept_targets`** (полный перехват: жив фронт → одиночный
    урон не в тыл; нет рангов → все живые = старый пул).
  - **Ось ЛИНИЙ (v2, С48)** — `Line` (LEFT/CENTER/RIGHT) + Т-раскладки данными `DEFAULT_GRID`
    (герой ЦЕНТР-фронт + союзники края тыла) / `MIRRORED_GRID` (саммоны края фронта + герой
    ЦЕНТР-тыл) + `party_grid`/`grid_slots`. Пьюр-ридеры под EffectCalculator: **`cell`** (клетка
    (line,rank)), **`neighbors`** («соседняя ячейка» — манхэттен-1, диагональ не сосед),
    **`column`** («вертикальный ряд»), **`same_rank`** (горизонтальный ряд).
  - **Расстановка** — `assign_party_ranks(player, allies, mirrored)` (+line по Т-схеме, overflow
    стаи циклит линии); `assign_enemy_ranks(enemies)` (фронт=(n+1)//2, линии `_LINE_FILL_ORDER`
    ЦЕНТР→ЛЕВО→ПРАВО).
- **`Creature.rank`/`Creature.line`** = None дефолт (инертно). **`Player.mirrored_layout`**
  (класс-флаг; `Summoner` = True → саммоны танкуют фронт, герой тыл).
- **Перехват симметричен (С48)** — враг→игрок: `Enemy._choose_attack_target` через
  `intercept_targets`. Игрок→враг: `CombatManager.get_target_enemy` через
  `intercept_targets(enemies)` (авто-цель карт/реликвий/способностей) +
  `_resolve_attack_target` (клэмп явного клика в прикрытый тыл → снап на фронт). AoE-карты
  бьют `combat_manager.enemies` напрямую → мимо перехвата.
- **Тактический Манёвр `[Tactical_Move]`** (`TacticalMoveEffect`, base.py) — атомарный
  переворот строя; смена строя = ЭФФЕКТ ДЕЙСТВИЯ (карта/реликвия/босс), не кнопка
  (анти-абуз). Рантайм `player.formation_mirrored` (тоггл; сброс к классовому дефолту
  каждый бой). `CombatManager.flip_formation`/`_init_positioning`/`_apply_positioning`
  (гард `positioning_enabled`; `_init_positioning` расставляет и врагов; пере-расстановка
  партии в `end_turn_phase` перед фазой врага). Карта «Перестроение» (basic.py, вне GENERIC).
- **Живое включение** — `GameManager.spawn_procedural_enemy` ставит `positioning_enabled`
  перед боем. Сим — `run_single_run(positioning=...)` opt-in (бот расставляет; перехват врага
  сим-нативен через наследование `BotCombatManager`). Дефолт off → baseline зелёный. A/B:
  v1 зеркало = верный режим Призывателя (дефолт-герой-фронт −28); v2 ON≈OFF (тактич. субстрат).
- **UI** — `panels._draw_rank_chip` (бейдж ФРОНТ/ТЫЛ ·линия на игроке+союзниках+ВРАГАХ) +
  союзники по рядам (фронт/тыл), внутри ряда сортировка по линии Л→Ц→П; одноряд без рангов.
- **Потребители субстрата (С49 §1, ✅ все три оси):** `core/cards/cleave.py` — общая база
  `_PositionalAoEEffect(DamageEffect)` (цель полный + вторичные `splash_ratio` через
  EffectCalculator) + 3 кирпича: `SplashDamageEffect` (`neighbors`, манхэттен-1),
  `ColumnStrikeEffect` (`column` — вертикаль линии, ПРОБИВАЕТ перехват в тыл),
  `RankStrikeEffect` (`same_rank` — вся шеренга). Карты «Рассекающий удар»/«Прокол»/
  «Размах» (generic). Все наследуют DamageEffect → бот/синергия/снимок видят атаку.
  Позиционка off / нет позиции у цели → вторичных целей нет → одиночный удар (fallback).
- **Следующие итерации** (та же data-модель): энфорс капа слотов · полный enemy-grid relayout
  в UI · контент-носители `[Tactical_Move]` (боссы/реликвии) · детонации соседних клеток
  (реюз `neighbors` в DetonationRegistry).

### Карты и эффекты (core/cards/)
Карта = `Card(name, cost, card_type, description, effects, rarity, exile)`, где `effects` — список «кирпичей»-эффектов. `Card.apply(player, enemy, cm)` вызывает `effect.execute(...)` по очереди.
- **Кирпичи-эффекты** (`core/cards/base.py`): `DamageEffect`, `ShieldEffect`, `StatusEffect`, `HealEffect`, `RegenEffect`, `PoisonEffect` (+ `VampireDamageEffect` — DEPRECATED). Каждый: `execute(player, enemy, combat_manager, is_upgraded)`, берёт `base_val`/`upgrade_val`. Фиче-специфичные кирпичи живут в своём модуле: `ShieldDamageEffect` (warrior.py), `BleedEffect` (debuff/bleed.py), `VampireBuffEffect` (buff/vampirism.py), **`FlowEffect`** и **`SpreadEffect`** (air.py — стихия «Воздух», см. ниже). `DetonateEffect` (base.py) — подрывает детонационные комбо на цели (см. «Комбо — два реестра»). **`SplashDamageEffect`/`ColumnStrikeEffect`/`RankStrikeEffect`** (cleave.py — позиционные AoE-наследники `DamageEffect`: цель + вторичные по `neighbors`/`column`/`same_rank`, см. «Позиционка»).
- **Стихия «Воздух» / Поток** (`core/cards/air.py`, Сессия 36): `FlowEffect(count_base, count_upg)` — НЕ статус существа, а эффект-кирпич. При розыгрыше снижает `temp_cost` на 1 у `count` случайных карт в руке (переиспользует систему `temp_cost` Разбойника). «До конца хода» само: `DeckManager.discard_hand` чистит `temp_cost`. Разыгрываемую карту исключает через транзиентный `CombatManager._card_being_played`. Архетип — темпо/энергия.
- **Фабрики карт** — функции `create_*()`, сгруппированы по модулям: `basic.py` (strike/defend/heavy_blade/iron_wall), `fire.py`, `water.py`, `poison.py`, `heal.py`, `buff/` (strength/thorns/regen/vampirism), `debuff/` (vulnerable/weak/bleed). Все реэкспортируются из `core/cards/__init__.py`.
- `card_type` ∈ `"attack"`/`"defend"`/… — используется реликвиями (напр. СвинцовыйНабалдашник ловит первую `attack`).
- `exile=True` — карта уходит в `exile_pile` после розыгрыша (до конца боя).
- Превью урона на карте — `EffectCalculator.calculate_damage(..., dry_run=True)` (состояние не меняется).

### Каталог карт и классовые пулы (core/cards/catalog.py) — НОВОЕ (Сессия 32)
ЕДИНЫЙ источник правды о том, какие карты существуют и кому доступны:
- `GENERIC_FACTORIES` — нейтральные карты (доступны всем классам). Сессия 36:
  +4 карты Шока (`core/cards/shock.py`): «Разряд» (энейблер, Шок 3(4)), «Серия
  молний» (3×2(3) мульти-хит, дренит заряды), «Громовой удар» (урон 6(8)+Шок 2(3)),
  «Перегрузка» (урон 3(4)+детонатор Электро-взрыва);
  +3 карты Земли (`core/cards/earth.py`): «Камнепад» (энейблер, Раскол 2(3)),
  «Дробящий удар» (урон 4(6), эксплойт Раскола по щиту), «Тектонический удар»
  (урон 6(8)+Раскол 2(3));
  +4 карты Воздуха (`core/cards/air.py`): «Порыв ветра» (урон 4(6)+Поток),
  «Восходящий поток» (Поток ×2(3), энейблер темпа), «Вихрь» (урон 7(9)+Поток),
  «Суховей» (`SpreadEffect`+Поток — разносит половину Горения/Яда на всех врагов).
- `CLASS_FACTORIES = {"Summoner": [wolf, golem], "Warrior": [retribution]}` —
  классовые карты, выдаются в забеге ТОЛЬКО своему классу. Добавить классовую
  карту = одна строка сюда.
- **«Возмездие» Воина** (`core/cards/warrior.py`, `ShieldDamageEffect`): урон ПО
  ВСЕМ врагам = текущему щиту (130% улучш.), щит не тратится, cost 1. Идентичность
  «защита = атака» + зачистка мультиврагов. Первая (пока единственная) AoE-карта.
- `get_pool_for_class(class_name)` — generic + классовые класса (для пулов выдачи).
- `get_class_cards(class_name)` — только классовые (для вкладки библиотеки).
- Атрибут `Card.card_class` (None=generic) проставляется централизованно обёрткой
  `_tagged` в каталоге — фабрики карт остаются чистыми.
- **Пулы выдачи берут карты по классу игрока**: `ui/shop/data.py::pick_two_cards`,
  `ui/chest/data.py::generate_chest_cards`, `ui/events/event_effects.py` (gain_random_card)
  → `get_pool_for_class(type(gm.player).__name__)`. Дублирование пулов устранено.

### Бой: цикл хода (CombatManager)
**Структура (С49, разбор god-object):** `managers/CombatManager.py` — тонкий ОРКЕСТРАТОР
(124 стр.: `__init__`, `enemy` property, `add_log_message`, предохранитель
`_guarded`/`_guarded_action`), наследует поведение из миксинов `managers/combat/`:
`positioning.py` (авто-цель/перехват/строй) · `cardplay.py` (`play_card_by_index` +
снимки) · `phases.py` (`start_turn_phase`/`end_turn_phase`/`_settle_energy_debt`) ·
`resolution.py` (смерть/победа/перенос стаи) · `defeat.py` (`check_player_defeat` + I/O).
Путь импорта `from managers.CombatManager import CombatManager` и API — байт-в-байт;
миксины оперируют через `self`, не импортируют CombatManager (без циклов). `BotCombatManager`
наследует как раньше.

`CombatManager.__init__(player, enemies, starting_deck, game_manager=None)` — принимает список врагов (или одного, автоматически оборачивается). Хранит `self.enemies: list`, `self.allies: list`. Compat-свойство `self.enemy` → первый враг (для старого кода).
- **`start_turn_phase`**: цикл по всем живым врагам → `choose_intent()` → пассив игрока считает carry щита → `_iron_will_shield = shield`; сброс щита до carry → `energy = max_energy` → добор `5 + bonus_draw` → (Разбойник: случайной карте `temp_cost -= 1`) → хуки реликвий `on_turn_start` → `ability.on_turn_start` (штрафы).
- **`play_card_by_index(idx, target=None)`**: проверка энергии → если цель не передана: `get_target_enemy()` (первый живой враг) → ставит `self._card_being_played = card` → `card.apply(player, target, self)` → `_card_being_played = None` → пассив `on_card_played_passive` → реликвии `on_card_played` → карта в `discard_pile`/`exile_pile` → `_process_enemy_deaths()` (смерть в момент килла) → `_check_victory()`. `_card_being_played` нужен `FlowEffect` (стихия Воздух), чтобы не удешевлять саму разыгрываемую карту.
- **`_process_enemy_deaths()`**: свип `_check_enemy_death` по ВСЕМ `self.enemies` (AoE-детонации могут добить нескольких) под `_guarded_action`. Зовётся в момент убивающего действия игрока — `play_card_by_index` (перед `_check_victory`) и ветка активной способности (`InputHandler`) — симметрично фазе врага. Чинит регресс С43: до этого `on_kill`/счётчик/перенос стаи жили только в `end_turn_phase`, и победа картой их теряла. Идемпотентно (`_death_processed`).
- **`end_turn_phase`**: сброс руки → гашение долга энергии (если овердрафт) → **хуки реликвий `on_turn_end`** (под `_guarded_action`, ДО действий врагов — Гнилое Сердце банкует щит до удара) → **`_tick_delayed_effects()`** (очередь отложенных, §3 — созревшие «через N ходов» срабатывают здесь, перед фазой врага) → `_apply_positioning()` → цикл по живым врагам: `shield=0`, `execute_intent()`, `tick_statuses()`, `_check_enemy_death()` (вызывает `on_kill` на реликвиях + стата) → игрок `tick_statuses()` → цикл по союзникам: `choose_action()`, `execute_action()`, `tick_statuses()`, `_check_ally_death()` → проверка победы: `all(e.hp <= 0)` → `check_player_defeat()`.
- **Мульти-враги**: этажи 1–4: 1 враг, 5–8: 2 врага, 9+: 3 врага. HP каждого уменьшен пропорционально. Босс всегда один.
- **Таргетинг**: клик по вражеской панели меняет `_target_index`. Жёлтая рамка вокруг выбранной цели. `play_card_by_index` получает цель из `TargetingSystem.get_current_target()`.
- **Союзники**: карты призыва (`create_summon_wolf`/`golem`) создают `Summon` в `combat.allies`. В конце хода союзники атакуют случайного живого врага. Панели союзников — в центральной зоне (x=590..1330).
- **Пассив «Свора»** (`Summon._pack_bonus`): каждый призыв бьёт сильнее на `PACK_DAMAGE_PER_ALLY` (=2) за КАЖДОГО другого живого союзника → урон стаи растёт нелинейно (масштаб Призывателя на поздних этажах). Лог показывает бонус `(+N Свора)`.
- **Персистентность стаи** (Сессия 35, Этап 2): выжившие союзники переносятся между боями через `Player.persistent_allies`. Сохраняются при победе (`CombatManager._check_enemy_death` → `_persist_allies`, когда повержен последний враг — на килле картой/способностью через `_process_enemy_deaths`, в фазе врага/союзника напрямую), восстанавливаются в новом бою (`_restore_persistent_allies`, щит/статусы обнуляются). Потолок переноса `CombatManager.MAX_PERSISTENT_ALLIES` (=6, сильнейшие по HP) — враги союзников не бьют, без потолка стая копилась бы бесконечно. Внутри боя призыв не ограничен. **Потолок — ручка тюнинга баланса Призывателя.**

### Очередь отложенных эффектов (§3, С49) — `core/scheduler.py`
Кросс-каттинг сабсистем **«сработать через N ходов»** под будущие механики-таймеры
(Heat-перегрев Кузнеца: недоковал → урон через ход · тайм-бомбы / Эффект Бабочки
Парадокса · любое «через N ходов сделать X»), чтобы у каждой не было bespoke-кода.
- **`DelayedEffect(turns, action, label="")`** — запись: `turns` (пол 1: «через 0 ходов»
  = «в конце этого хода»), `action(combat_manager)` — вызывается ВЫЗЫВАТЕЛЕМ при
  созревании, `label` — метка для лога. `__slots__`.
- **`DelayedQueue`** — пьюр-тайминг, ничего не исполняет сама: `schedule(turns, action,
  label)` кладёт, `tick()` уменьшает ВСЕ таймеры на 1 и **возвращает** список созревших
  (`turns<=0`), убрав их из очереди. `pending` — копия для UI/инспекции. Разделение
  тайминга и исполнения: (1) тривиально тестируется без боя; (2) действие, запланировавшее
  НОВОЕ отложенное во время исполнения, не теряется (tick переустановил очередь до возврата).
- **Врезка в бой**: `CombatManager.__init__` заводит `self.delayed_queue` (скоуп боя — новый
  CM на каждый бой, не переносится). `phases._tick_delayed_effects()` тикает очередь и
  исполняет созревшие под `_guarded_action` (конечность каскада, инвариант R3), затем свип
  смертей через `_process_enemy_deaths()` (тайм-бомба могла добить врага). Зовётся в
  `end_turn_phase` после `on_turn_end` реликвий, перед фазой врага.
- **ТАЙМИНГ — дизайн-дефолт (пересмотреть при появлении потребителя):** срабатывание в
  КОНЦЕ ХОДА ИГРОКА. Альтернатива (начало следующего хода) — одна строка. Зафиксировано
  как развилка: пока потребителя нет, выбор No-Op.
- **ИНЕРТНА без потребителя** (как 2D-субстрат позиционки до §1): очередь пуста → `tick()`
  отдаёт `[]` → baseline зелёный. `tests/test_scheduler.py` (пьюр-примитив) +
  `tests/test_combat_manager.py` (живая врезка).

### Колода (DeckManager)
Пайлы: `draw_pile` ← `hand` → `discard_pile`; `exile_pile` отдельно. `draw_cards(n)` — при пустом доборе перемешивает сброс обратно. `discard_hand()` — сброс руки + чистка `temp_cost`. `reset_deck()` (новый бой) — возвращает изгнанные карты в пул и перемешивает.

### Враги: система намерений (core/enemies/)
Класс намерения на враге: `enemy.intent` ∈ `IntentAttack/IntentDefend/IntentDebuff/IntentNone` (есть `set_intent(type, value)` + св-ва-совместимости `intent_type`/`intent_value`).
- `choose_intent()` — переопределяется в подклассах (`cultist.py`, `slime.py`, `boss.py`), задаёт намерение на ход.
- `execute_intent(player, cm)` — исполняет: attack → `calculate_damage` + `take_damage` по СЛУЧАЙНОЙ цели; defend → `gain_shield`; debuff → `player.weak += value` (дебафф всегда игроку).
  - **Случайный таргетинг атаки** (`Enemy._choose_attack_target`): цель атаки =
    `random.choice([игрок] + живые союзники)`. Без союзников/боя — игрок (поведение
    классов без стаи не меняется). Стая Призывателя теперь ТАНКует (поглощает часть
    ударов) — структурный фикс «стены эт.50». Фундамент под будущий статус
    «провокация» (форсирует цель) и новые призывные классы/карты.
- `base_test_damage`/`base_test_shield` — базовые значения, проставляются в `EnemySpawner.build_enemy` (статы/имя/класс врага). `GameManager.spawn_procedural_enemy` — тонкий фасад: зовёт `build_enemy`, создаёт `CombatManager`.

### Боссы-фильтры (core/enemies/bosses/) — Сессия 41

Мягкие боссы на этажах 20/40/60/80/100 по геймдиз-пакту [[boss-filter-ladder]].
Каждый = механические ворота (НЕ числовые), с ≥1 обходным путём для каждого класса.
Диспатч через `BOSS_BY_FLOOR: dict[int, type]` в `EnemySpawner.build_enemy()`.
`BossTitan` = fallback для нестандартных босс-этажей.

**Архитектура:**
- `BossBase(Enemy)` — фазовая система (`current_phase`), хуки `on_card_played` /
  `on_turn_start` (hasattr duck-typing в CombatManager, как у реликвий).
- `IntentHeal` (в `core/enemies/base.py`) — новый тип намерения (хил врага), нужен
  для Temporal Shift Хранителя Времени.

**5 боссов:**

| Этаж | Класс | Ворота | Механика |
|------|-------|--------|----------|
| 20 | `ThresholdGuardian` | Защита/хил | Эскалация урона (+40% за цикл, кап ×3). Фаза 2: отчаянные атаки. |
| 40 | `OblivionArchivist` | Чистота колоды | +щит за карту (+2/+3). Слабость если колода >15 карт. |
| 60 | `VoidElemental` | Мульт. урон | Щит Пустоты (8+floor//10) ↔ Уязвимость (×1.5). Burst-окно. |
| 80 | `TimeKeeper` | Персист. скейлинг | Растущий заряд (+15%×N к урону). Temporal Shift: хил 15% HP. |
| 100 | `TowerArchitect` | Полный компаунд | 3 фазы по HP. Victory lap после эт.80. |

**Sim-видимость:** боссы работают через тот же `EnemySpawner.build_enemy()` →
симулятор видит их без изменений в `runner.py`.

**Файлы:** `core/enemies/bosses/__init__.py` (BOSS_BY_FLOOR), `base.py` (BossBase),
`guardian.py`, `archivist.py`, `elemental.py`, `keeper.py`, `architect.py`.
Тесты: `tests/test_bosses.py` (+60 тестов).

### Элитные враги-контры (core/enemies/elites/) — Сессия 42

Элитки с уникальными механиками-контрами билдам (Этап B роадмапа), вместо простого
стат-буста рядового. Тот же паттерн, что у боссов: `EliteBase(Enemy)` с хуками
`on_card_played`/`on_turn_start` (duck-typing), но БЕЗ фаз и с `is_elite=True`.
Диспатч: `EnemySpawner.build_enemy` при `is_elite` берёт `random.choice(ELITE_REGISTRY)`
+ `random_title()`. Стат-множители элиты (×1.5 HP и т.д.) сохранены.

**4 архетипа:**

| Класс | Контра | Механика |
|-------|--------|----------|
| `SpellEater` | Колоды-пулемёты | `on_card_played` → +4 щита за карту. |
| `PlaguePustule` | Оборона | `on_turn_start` → +3 Яда, ×2 при щите игрока. |
| `ButcherTorturer` | Вампир/хил | Шипы 3 + Слабость при росте HP игрока. |
| `CorruptionDevourer` | DoT-билды | Пожирает свои DoT-стаки (cap 8) → лечение. |

**Sim-видимость:** элитные бои в `runner.py` (не-босс этаж ≥8, шанс
`_ELITE_ROOM_CHANCE=0.10`) → архетипы видны балансу. Награда элиты в симе НЕ
моделируется (AUDIT 2.4). → [[balance-findings-elites]].

**Файлы:** `core/enemies/elites/__init__.py` (ELITE_REGISTRY), `base.py` (EliteBase),
`spell_eater.py`, `plague.py`, `butcher.py`, `devourer.py`.
Тесты: `tests/test_elites.py` (+28 тестов).

### Реликвии — хуки
`on_combat_start`, `on_turn_start`, `on_damage_calculated(base_dmg, is_player_attack=True)`,
`on_tick_ignited`, `on_wet_applied`, `on_card_played`, `on_shield_gained(amount, creature, combat_manager=None)`,
`on_kill` (заглушка), `on_combat_end`, `on_boss_defeated`, `on_bleed_tick`, `on_heal`, `on_chest_opened`

`on_turn_start` вызывается в `CombatManager.start_turn_phase` ПОСЛЕ сброса щита.

### Персистентный слой по забегу (шаг №5 framework)
Хук **`on_boss_defeated(player, combat_manager)`** — триггерит на босс-этажах
(20/40/60/80/100, `local_step == FLOORS_PER_ACT`). Вызовы зеркальны в двух местах:
`GameManager.distribute_combat_rewards` (игра, при `is_boss`) и
`managers/balance/runner.py` (сим — предусловие [[boss-filter-ladder]]: симулятор
обязан видеть чекпойнты, иначе тюнинг вслепую). Назначение — единственный источник
кат.4-компаунда, который переносится МЕЖДУ боями (внутрибоевые движки
barrier/mastery/echo/virulence сбрасываются `reset_combat_statuses`): растущие
реликвии копят множитель через забег, бустя НАКЛОН кривой игрока (модель R(f)).
- **`КоронаВознесения`** (EPIC, `core/relics/advanced/persistent.py`) — флагман: каждый
  босс ×`GROWTH_PER_BOSS`(=1.25) к урону атак игрока (компаунд по забегу, ×1.25^5≈3.05
  за 5 боссов). Состояние `_mult` на инстансе → свежий инстанс/забег = авто-сброс.
  `on_damage_calculated` ОКРУГЛЯЕТ (не усекает) — мелкий урон не теряет бонус.
  Замер-свип: механизм флипает наклон (Маг пробивает эт.100 при ×2.0/босс); ×1.25 =
  «заметно, но не ломает» для ОДНОЙ реликвии. A/B (+Корона): Warrior wr50 80→98%,
  Mage 91→97%, у Druid медиана почти не движется (стена оборонительная — [[balance-findings-druid-engine]]).
- **`СердцеБездны`** (EPIC, `persistent.py`) — ОБОРОННОЕ зеркало Короны: каждый босс
  +`GROWTH_PCT`(=15%) к `player.max_hp` навсегда + хил на дельту. Растит экспоненту
  ВЫЖИВАЕМОСТИ (p в R(f)) — закрывает дефицит оборонного кат.4-компаунда. Компаунд
  хранится прямо в `max_hp` (перенос тем же игроком, авто-сброс на новом забеге).

### Реликвии — высокотировые движки и джокеры (EPIC/LEGENDARY)
`core/relics/advanced/epic_legendary.py` — высокотировый контент на ДОЛГОЖИВУЩИХ
примитивах (echo/barrier/щит/×урон/изгнание), без привязки к классам:
- **`ЭхоВечности`** (EPIC) — `on_turn_start` → Эхо 1 (ретриггер-движок темпа).
- **`НесокрушимыйБастион`** (EPIC) — `on_shield_gained` → `BARRIER_FRACTION`(=0.5) от
  щита в несгораемый Барьер (без рекурсии: `add_status`, не `gain_shield`).
- **`СтеклянныйГлаз`** (LEGENDARY-джокер) — `on_damage_calculated` ×`DAMAGE_MULT`(=3);
  `on_card_played` с шансом `BURN_CHANCE`(=0.10) удаляет карту из `gm.current_deck`
  навсегда (хук ДО discard → карта отыгрывает текущий розыгрыш, исчезает со след. боя).
- **`ГнилоеСердце`** (LEGENDARY-джокер) — `on_combat_start` сажает `max_hp=1`;
  `on_turn_end` банкует щит в Барьер + Сила = Барьер//`SHIELD_TO_RAGE`(=10), вклад в
  Силу инкрементальный (`_granted_rage`, не затирает чужую Силу).
- NB: новые EPIC/LEG в ceiling-билды НЕ добавлены → baseline-гард не затронут.

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
- **DruidAbility «Токсичный взрыв»** (Сессия 35): снять весь яд с врага, нанести разом, Регенерация = яд // 4 (потолок 8). Один раз за бой.
- **BerserkerAbility «Кровавая ярость»**: -10% макс HP себе сквозь щит, +Ярость = урон × 2. Один раз за бой.
- **SummonerAbility «Подкрепление»** (Сессия 32, каркас): призвать Волка (HP 12, Атака 4) в `allies`. Один раз за бой. Пассив класса — «Свора» (см. раздел «Союзники»).

UI: `draw_ability_slot` в `hud.py` → `view.ability_rect` (пересчитывается каждый кадр).
Тултип: `CombatHUD.draw_ability_tooltip(screen, font, ability, mouse_pos)` — вызывается в конце `draw_combat_screen` при наведении.

### Пассивы классов (хуки в `core/players/base.py`, переопределяются в подклассах)
- **Warrior** «Железный задел» (`on_turn_start_passive`, warrior.py): переносит 50% текущего щита (Сессия 35, было 30% — топливо для карты «Возмездие») на новый ход через `_passive_shield_carry`. Считается ДО сброса щита в `start_turn_phase`.
- **Mage** «Стихийный резонанс» (`on_card_played_passive`, mage.py:26): если разыгранная карта вызвала комбо (флаг `_combo_triggered`, выставляется через data-driven реестр `core/ComboRegistry.py`), +1 карта из колоды. Сессия 35: флаг переименован из `_steam_combo_triggered` в общий `_combo_triggered`.
- **Druid** «Токсичный круговорот» (`on_heal_passive`, druid.py:34): при любом хиле игрока враг получает яд = размеру хила.
- **Rogue / Berserker**: классовых пассивов НЕТ (только активные способности + спец-логика в `start_turn_phase`/EffectCalculator).
- Хуки пассивок: `on_turn_start_passive`, `on_card_played_passive`, `on_heal_passive` (база — заглушки).

### Балансер (managers/balance/ + BalanceSimulator.py) — ПЕРЕПИСАН (Сессия 32)
Модель **сквозного забега**: бот идёт этаж за этажом ОДНОЙ колодой, HP переносится,
костёр лечит 30% на предбоссовом этаже. Использует РЕАЛЬНЫЕ формулы врагов
(`build_enemy_group`), а не захардкоженные статы.
- `bot.py::BotCombatManager` — КОМПЕТЕНТНЫЙ бот: играет по классовой политике
  (`policy.py`), глушит сеть/UI (`check_player_defeat` без `send_run_record`).
- `policy.py` (Сессия 34, синергийный слой Сессия 36) — `BotPolicy` (одна на класс)
  + реестр `get_policy`. Тайминг классовой способности (`on_turn_begin`/`on_turn_end`
  по предусловиям: щит/стаки/проактивно) + выбор карты по шаблону
  `pick_card` → `_synergy_pick` → `_class_pick`:
  - **`_synergy_pick` (общий для всех классов)** — пилотирует синергийные карты из
    generic-пула (их получает как награду любой класс). Детект по ТИПУ эффекта
    (`DamageEffect`/`StatusEffect`/`DetonateEffect`/`FlowEffect` — устойчиво к новым
    картам), цель = `get_target_enemy()`. Приоритет по «отдаче»: готовая детонация
    (бурст) → сетап Раскола (только при `target.shield>0`) → сетап Шока (при
    `shock==0`) → темпо Потока (чистый энейблер при запасной карте). Срабатывает
    ТОЛЬКО при синергии в руке, иначе `None` → несинергийные прогоны не меняются.
  - **`_class_pick`** — класс-специфика (Призыватель приоритизирует призывы по
    `SummonEffect`; Воин копит щит→«Возмездие»; Маг сетапит ПАР) или random у базы.
  Пороги «компетентности» — именованные константы вверху файла.
- `runner.py::run_single_run` — один забег floor=1..100, `_StubGM` (лёгкий контекст).
  **Параметризован (Сессия 36):** `draft` (стратегия добора карты), `extra_cards`
  (фабрики в стартовую колоду), `relics` (фабрики/классы в `gm.relics`). Дефолты =
  метрика WALL (прежнее поведение, побитово). `default_draft` — случайная награда.
- `report.py` — перцентили глубины смерти, win-rate по чекпоинтам [10,25,50,75,100],
  кривая %HP. **`format_dual_report` (Сессия 36)** — wall и ceiling рядом + «ЗАЗОР».
- **`builds.py` (Сессия 36) — метрика CEILING** (двойная экспонента, см. ниже):
  `CLASS_CORES` (ручное ядро архетипа на класс: карты+реликвии) + `greedy_draft`
  (добор лучшей из N карт по эвристике `_card_score` = отдача/энергию + бонус за
  тему колоды `_deck_themes`). `get_ceiling_build(name)` → `(draft, extra, relics)`
  для `run_single_run`. Ядра — прокси «к чему класс собирался», не идеальная игра.
- `BalanceSimulator.py` — тонкий фасад, `python -m managers.BalanceSimulator`
  (6 классов × 200, ОБЕ метрики через `run_dual`).
- 📐 **Две метрики = две границы кривой (Сессия 36, парадигма двойной экспоненты).**
  `wall` (случайный драфт) = базовая стена без билда — должна быть ОДНОЙ кривой на
  всех. `ceiling` (ядро+жадный драфт+реликвии) = потолок собранного билда — у
  каждого класса свой. Зазор стена↔потолок = пространство геймплея. Замер вскрыл:
  ceiling ≥ wall у всех, но **пробивают потолок лишь Summoner** (зазор med +28,
  wr50 +92пп — стая+перенос = компаундящий движок кат.4) **и Mage** (+18). У
  остальных потолок упёрт в ту же стену (~эт.30-50): **категории-4 компаунда нет**.
- 📊 **Аудит масштабирования (Сессия 37, шаг №3 framework):** полная инвентаризация
	  всех источников роста по 5 категориям → [[scaling-audit]]. Результат: **весь
	  скейлинг — кат.1-3** (флат/линейный/×разовый). Единственный кат.4+ = «Свора»
	  Призывателя (N² + перенос стаи) — потому Summoner ceiling пробивает стену.
	  Карта дефицита: ни у одного класса нет персистентного кросс-бой множителя.
	- **Замер компетентным ботом (Сессия 34, % до эт.100):** Воин 0 · Маг 2 ·
  Призыватель 0 · Берсерк 14 · Разбойник 22 · **Друид 76**. Бот теперь жмёт
  способности → картина изменилась: Друид сломан через «Токсичный взрыв»
  (бурст+реген), Призыватель реально слаб (гипотеза «скрыто силён» опровергнута).
  Числа sustain-ребаланса Сессии 33 (мерены без способностей) недостоверны.
- **Нерф Друида (Сессия 35):** «Токсичный взрыв»: Реген = яд // 4 + потолок 8
  (было яд // 2). Замер: **76% → 34%** (медианная смерть эт.29).
- ✅ **Артефакт симулятора адресован (Сессия 36):** был — `_maybe_reward_card` берёт
  награды `random.choice` из generic-пула, но у бота не было политики под синергию;
  после добавления карт Шока/Раскола/Потока глубокие классы просели (Druid 22→~13,
  Rogue 12→6, Berserker 11→6), т.к. бот тащил энейблеры как мусор и разбавлял колоду.
  Это НЕ баланс-баг (живой игрок юзает синергию в плюс), а предел модели. **Фикс —
  синергийный слой `BotPolicy._synergy_pick`** (см. выше): бот пилотирует эти карты.
  A/B на одинаковых seed'ах (слой ВКЛ vs ВЫКЛ, текущий пул) поднял именно глубокие
  классы: Druid med 23→26 / wr50 18→23%, Rogue p75 21→25, Berserker wr100 4→8%;
  рано умирающие (Воин/Маг/Призыватель) без изменений. Полного возврата к до-Шоковым
  числам нет (карты всё равно разбавляют колоду), но замер стал честнее.
  См. [[balance-findings-shock-dilution]].
- 🎯 **Ребаланс слабой тройки (Сессия 36).** Честный замер (с синергийным ботом)
  вскрыл: Призыватель/Воин/Маг не пробивают эт.50 (wr50 ≤6%). Чиним структурно,
  поэтапно. **Этап S — Призыватель ГОТОВ:** случайный таргетинг врага (стая танкует)
  + потолок переноса `MAX_PERSISTENT_ALLIES` 10→6. A/B (таргетинг старый vs новый):
  Призыватель med 29→54, wr25 86→100%, wr50 0→68% при cap10; cap6 ставит med=43
  (вровень с Берсерком 42), wr50 6% — стена эт.50 снята без перелёта. Остальные 5
  классов A/B-идентичны (нет стаи → пул целей = [игрок]). Маг и Воин — следующие этапы.

### Враги — формулы (актуальные, Сессия 37 — ЧИСТАЯ ЭКСПОНЕНТА)
Числа вынесены в константы вверху `EnemySpawner.py` (тюнятся балансером):

stat = BASE * GROWTH ** floor   →   E₀·g^f

HP:   HP_BASE(45)  * HP_GROWTH(1.028)  ** floor
DMG:  DMG_BASE(5.5) * DMG_GROWTH(1.026) ** floor
SHLD: SHLD_BASE(3.5) * SHLD_GROWTH(1.008) ** floor

Плавный рост без ступеней актов (tier² удалён). g≈1.03 → удвоение ~каждые 23 этажа.
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
1. Класс-наследник `Relic` в подходящем по теме модуле `core/relics/advanced/` (`bleed_poison`/`shield`/`healing`/`damage`/`utility`; или starter/elemental), переопределить нужные хуки (см. «Реликвии — хуки»). Передать `rarity` по **контракту редкости** (docstring `core/relics/base.py`). Реэкспортировать из `core/relics/advanced/__init__.py`.
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

Реликвии — 27 итого. **Контракт редкости** (рамка калибровки) — module-docstring в
`core/relics/base.py`: COMMON = плоский стат/разовый эффект без условий · UNCOMMON =
условные/синергийные · RARE = движки/билд-дефайнеры · EPIC = компаунд по забегу ·
LEGENDARY = меняет правила с трейдоффом. Цены по редкости в `ui/shop/data.py`.
- COMMON (13): LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер (Реген 3), Заплатка, ЗаточенныйОсколок, ПанцирьДикобраза (Шипы 3), ГрозоваяБатарея (Шок 2 врагу), МеткаОхотника (Уязв. 1 врагу), ТотемЯрости (Ярость 1), ФлаконКатализатора (Мокрый случайному врагу)
- UNCOMMON: ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник, ШипастаяБроня, ТрофейныйКлык
- RARE: ЭнергоЯдро, СердцеТитана, ГнилойКлык, ЖелезнаяВоля, БерсеркМедальон
- EPIC: КоронаВознесения (`persistent.py` — растущая, ×1.25 урон/босс по забегу)
- LEGENDARY: ПроклятаяКорона
- **Дроп EPIC/LEGENDARY**: только с боссов по этажу (`RewardManager._roll_relic_rarity(floor)`): floor≥40 → шанс EPIC, floor≥60 → шанс LEGENDARY (раньше упирался в RARE — флагманы были недостижимы вне сима).

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

## Мета-прогрессия / сейв (Сессия 40)
- `managers/SaveManager.py` — ЕДИНСТВЕННЫЙ слой записи на диск. Только примитивы
  (никакой сериализации живых объектов). Путь PyInstaller-safe в пользовательском
  каталоге (`%APPDATA%`/`XDG_DATA_HOME` → `Roguelike-CardGame/meta_save.json`), НЕ
  рядом с frozen exe. Запись атомарна (temp + `os.replace`), UTF-8, сбой записи
  проглатывается (сейв не критичен для геймплея).
- Модульный кэш `_meta` (ленив, `get_meta()`); битый/чужой файл → дефолт (не падает).
  Схема v1: `stats` (пожизненные) + `class_best{cls}` + `runs` (кольцо `RUNS_CAP=50`).
- Врезки: `GameManager.__init__` → `self.meta = SaveManager.get_meta()`;
  `CombatManager.check_player_defeat` → `record_run` (local-first, ДО сети) с классом
  игрока (`type(player).__name__`). `BotCombatManager` НЕ задет (свой defeat без записи)
  → симулятор/baseline не пишут на диск.
- Лидерборд (`ui/LeaderboardView.py`) — local-first: `SaveManager.leaderboard_rows`
  (локальные забеги + мерж сетевого `fetch_top_scores`, дедуп, сорт этаж↓). Столбец
  КЛАСС (русский label из `CLASS_INFO`). Работает офлайн.
- Хаб (`ui/hub/base.py::_draw_meta_stats`) — панель пожизненных статов из `gm.meta`
  («игра помнит тебя»). Инертна без меты/`class_best`.
- ВНЕ объёма (бэклог): гейтинг/разблокировки, мета-валюта, сейв ПОСРЕДИ забега.

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

### 🔥 Приоритет 0 (Сессия 35) — БАЛАНСОВАЯ ИТЕРАЦИЯ
Балансер теперь компетентен (бот жмёт способности — `policy.py`), база честная.
Цель: **подтянуть все классы к примерно одинаковому % доходимости** (сейчас разброс
огромный: Друид 34 — Воин/Призыватель 0). Разрешено **добавлять/менять карты и
стартовые колоды классов** (`core/cards/`, `core/players/*.py`, каталог
`core/cards/catalog.py`). Первоочерёдно:
- (а) ✅ **Ослабить движок Друида** — «Токсичный взрыв»: Реген = яд // 4 + потолок 8
  (было // 2). Замер: 76% → 34% (медианная смерть эт.29).
- (б) ✅ **Структурный фикс Призывателя** — выбрана **персистентность стаи** между
  боями (`Player.persistent_allies` + потолок переноса `MAX_PERSISTENT_ALLIES=6`,
  см. «Персистентность стаи»). Замер: дошёл до эт.25 ~10% → 37%, max этаж 27 → 38+.
  Стена на этаже ~50 осталась → классу нужен ещё рычаг (HP/масштаб) в Этапе 5.
- (в) ✅ **Бафф Воина** (Этап 3) — классовая карта «Возмездие» (AoE урон = щит,
  щит не тратится, cost 1) + «Железный задел» 30→50%. Ранне-средняя выживаемость
  заметно выше (эт.10 81→99%), но глубокая стена (эт.20-50) держится: у Воина нет
  sustain → нужен второй рычаг в Этапе 5.
- (г) **Маг тоже в подвале** (эт.100: ~2-3%) — Этап 4: пересмотреть способность/колоду.
- Источник идей по контенту (стихии-синергии Пар/Электро-взрыв, реликвии-джокеры,
  типы сундуков, элитки-контрпики) — файл `Идеи.xlsx` в корне.
- Подкрепить тестами политики бота (`managers/balance/policy.py`).

### Приоритет 1 — ✅ ВЫПОЛНЕНО в Сессии 30
1. ✅ **Инвентарь реликвий в бою** — реликвии-чипы уезжали за край экрана. Сделаны компактные
   бейджи (помещаются 19+) + панель-оверлей `RelicPanel` по клику на «АРТЕФАКТЫ»/«+N»
   (см. «Реликвии — UI в бою»). Скролл панели при очень большом пуле — возможный follow-up.

### Приоритет 2 (рефакторинг) — ✅ ВЫПОЛНЕНО в Сессии 29
Все три стадии плана рефакторинга крупных файлов завершены:
- ✅ **Stage 1** (контент-ядро): abilities.py→пакет, relics/advanced.py→пакет (по теме), GameManager god-object разобран (EnemySpawner + RewardManager, 266→145).
- ✅ **Stage 2** (крупный UI): HubView→`ui/hub/`, CombatInterface→`ui/combat/` (+мёртвый дубль `draw_ability_slot` удалён), CardRenderer→`ui/cards/`.
- ✅ **Stage 3** (остальной UI): Shop→`ui/shop/`, GameView разнесён (`draw_dispatchers`/`hover_state`/`combat/hover`, 271→140, мёртвый `_draw_placeholder` удалён), VictoryScreen→`ui/victory/`, CardLibraryView→`ui/library/`.

Оставлено намеренно (UI-render под мягким потолком 220 / цельные оркестраторы): `MapView.py` (167, цельный render, делегирует в `map_icons.py`), `core/Creature.py` (198), `ui/combat/hud.py` (252), `ui/combat/panels.py` (157).

**Долг размера: ✅ ЗАКРЫТ (С49).** `managers/CombatManager.py` дорос до 619 строк
(god-object) → разнесён на оркестратор (124) + миксины `managers/combat/` (см. раздел
«Бой: цикл хода»). По обновлённому ГОСТу (150=триггер, потолок ~250) остальные крупные
логические файлы — когезивные, благословлены.

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