# _project_map.md — Roguelike-CardGame
# > Последнее обновление: Сессия 25, Jun 3, 2026

## Архитектура
- `core/` — вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py)
- `ui/` — вся отрисовка (CardRenderer.py, CombatInterface.py, GameView.py, HubView.py, MainMenu.py и др.)
- `managers/` — CombatManager, DeckManager, GameManager, MapGenerator, network_manager
- Разрешение: строго 1920x1080 Full HD
- **Ветка разработки: dev** (main — стабильная, dev — активная работа)

## Железные ГОСТы
- Лимит файла: 150 строк (золотой стандарт)
- Модульность и логичные зависимости — главный принцип
- Никаких "божественных объектов"

## Навигация
- Читать этот файл ПЕРВЫМ в каждой сессии
- Большие файлы (GameManager.py, CombatInterface.py, GameView.py) — query_context
- Все файлы из ветки dev: `https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу`

## Полный список файлов (после Сессии 25)
main.py, server.py, _project_map.md

core/rarity.py, core/Creature.py, core/EffectCalculator.py, core/StatusRegistry.py

core/cards/__init__.py, base.py, basic.py, fire.py, poison.py, water.py, heal.py

core/cards/buff/__init__.py, strength.py, thorns.py, regen.py, vampirism.py

core/cards/debuff/__init__.py, vulnerable.py, weak.py, bleed.py

core/enemies/__init__.py, base.py, cultist.py, slime.py, boss.py

core/players/__init__.py, base.py, mage.py, rogue.py, warrior.py, druid.py, berserker.py

core/relics/__init__.py, base.py, starter.py, elemental.py, advanced.py

managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py, MapGenerator.py, network_manager.py

ui/chest/__init__.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py

ui/combat/__init__.py, hud.py

ui/events/__init__.py, event_data.py, event_effects.py, positive.py, negative.py, neutral.py, special.py

ui/Campfire.py, CardRenderer.py, CombatInterface.py, CardLibraryView.py

ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py

ui/VictoryScreen.py

## Ключевые системы

### Creature.py
Базовый класс. `hp`, `shield`, `self.statuses={}` через `__getattr__`/`__setattr__`.
- `take_damage(amount, attacker=None, combat_manager=None)`
- `heal(amount, combat_manager=None)` — после хука реликвий вызывает `self.on_heal_passive(healed, cm)` если атрибут есть
- `gain_shield(amount, combat_manager=None)` — с хуком `on_shield_gained`

### StatusRegistry.py
Единый реестр всех 10 статусов: `vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire`

### EffectCalculator.py
Единая точка боевой математики. `dry_run=True` для превью. Обновляет `gm.stats["max_damage_dealt"]`.
- Пассив Берсерка: `бонус = int((1 - hp/max_hp) * 10)`, только `is_player_attack` и `type(attacker).__name__ == "Berserker"`
- После триггера «Пар»: выставляет `combat_manager._steam_combo_triggered = True`

### Хуки реликвий
`on_combat_start`, `on_turn_start`, `on_damage_calculated(base_dmg, is_player_attack=True)`,
`on_tick_ignited`, `on_wet_applied`, `on_card_played`,
`on_shield_gained(amount, creature, combat_manager=None)`,
`on_kill` (заглушка — до мульти-врагов),
`on_combat_end`, `on_bleed_tick`, `on_heal`, `on_chest_opened`

`on_turn_start` вызывается в `CombatManager.start_turn_phase` ПОСЛЕ сброса щита и применения пассивки класса.

### Хуки классовых пассивок (core/players/base.py)
Заглушки — переопределяются в подклассах:
- `on_turn_start_passive(combat_manager)` — Warrior: сохраняет 30% щита
- `on_card_played_passive(card, combat_manager)` — Mage: добирает карту при «Паре»
- `on_heal_passive(healed_amount, combat_manager)` — Druid: яд на врага

### CombatManager
- `__init__(player, enemy, starting_deck, game_manager=None)`
- `start_turn_phase`: порядок критичен:
  1. `on_turn_start_passive(self)` — пассивка читает щит ДО сброса, пишет в `_passive_shield_carry`
  2. `carry = getattr(player, '_passive_shield_carry', 0)` → `player.shield = carry`
  3. `player._iron_will_shield = carry` — для ЖелезнойВоли
  4. `on_turn_start` реликвий — ЖелезнаяВоля восстанавливает `_iron_will_shield`
- `play_card_by_index`: сбрасывает `_steam_combo_triggered = False` перед `card.apply`, затем вызывает `on_card_played_passive`
- Пассив Разбойника: `temp_cost = max(0, original - 1)` на случайную карту в руке

### Персонажи
Warrior (HP80, E3), Rogue (HP65, E4), Mage (HP55, E3), Druid (HP70, E3), Berserker (HP60, E3)

Пассивки реализованы у всех пяти классов:
- **Берсерк**: бонус урона от недостающего HP (в EffectCalculator)
- **Разбойник**: temp_cost -1 на случайную карту в руке (в CombatManager)
- **Warrior «Железный задел»**: 30% щита переносится на следующий ход
- **Mage «Стихийный резонанс»**: при комбо «Пар» — добрать 1 карту
- **Druid «Токсичный круговорот»**: при любом хиле — яд на врага равный healed

### Враги
Cultist, SlimeAndGoblins, BossTitan

Формулы (тестовый режим):
- `hp = 20 + floor×3 + tier×10`, `dmg = 3 + tier×1`, `shld = 2`
- Босс: `hp×2.2`, `dmg×1.3`, `shld×1.8`, `shield=shld×2`

## Реликвии (19 итого)

|
 Редкость 
|
 Реликвии 
|
|
---
|
---
|
|
 COMMON 
|
 LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок 
|
|
 UNCOMMON 
|
 ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник, ШипастаяБроня 
|
|
 RARE 
|
 ЭнергоЯдро, СердцеТитана, ГнилойКлык, ЖелезнаяВоля 
|
|
 LEGENDARY 
|
 ПроклятаяКорона 
|

**ШипастаяБроня** (UNCOMMON): `on_shield_gained` → враг получает +1 Кровотечение
**ЖелезнаяВоля** (RARE, АКТИВНАЯ): `is_active=True`, `activate()` из InputHandler при клике. Один раз за бой — щит не сбрасывается в начале следующего хода. UI: `[A]` префикс, золотой/серый по состоянию.

## Изменения по сессиям

### Сессия 25
- `core/players/base.py`: добавлены заглушки `on_turn_start_passive`, `on_card_played_passive`, `on_heal_passive`
- `core/players/warrior.py`: пассивка «Железный задел» — `_passive_shield_carry = int(shield * 0.3)`
- `core/players/mage.py`: пассивка «Стихийный резонанс» — добор карты при флаге `_steam_combo_triggered`
- `core/players/druid.py`: пассивка «Токсичный круговорот» — яд на врага при хиле
- `core/EffectCalculator.py`: после триггера «Пар» выставляет `_steam_combo_triggered = True`
- `core/Creature.py`: `heal()` вызывает `on_heal_passive` если атрибут есть на существе
- `managers/CombatManager.py`: новый порядок в `start_turn_phase` (пассивка → carry → сброс → iron_will → реликвии), `_steam_combo_triggered` сбрасывается перед `card.apply`

### Сессия 24
- [UI-08] CombatInterface.py — полный рефакторинг под тёмно-синюю тему
- [UI-09] ui/combat/hud.py — новый файл CombatHUD (HP-бары, энергия-ромбы, статусы, реликвии, тултипы)
- Палитра: BG=(12,12,22), панели=(22,22,40), рамки=(160,160,255), золото=(255,220,60)
- Геометрия: игрок слева (x=30), враг справа (x=1330), отступ 30px от краёв
- Hover кнопок: прямая проверка `pygame.mouse.get_pos()`, НЕ через `view.hover`

### Сессия 23
- `CardRenderer`: `display_cost = getattr(card, 'temp_cost', card.cost)`, `COLOR_COST_DISC = (80,220,80)`
- `ПроклятаяКорона`: gold skip в `distribute_combat_rewards`
- `Creature.gain_shield`: новая сигнатура `(amount, combat_manager=None)` + хук `on_shield_gained`
- Добавлены реликвии: ШипастаяБроня, ЖелезнаяВоля
- `InputHandler._handle_combat`: клик по активной реликвии → `relic.activate()`

### Сессия 22
- BUG-01: дублирование наград — guard в InputHandler + первая строка distribute_combat_rewards

### Сессия 17
- UI: Campfire/Shop EventView-стиль, FORGE/REMOVE full-screen, MainMenu тёмно-синяя тема

## Важные грабли
- `_passive_shield_carry` — пассивка пишет ДО сброса щита, CombatManager читает ПОСЛЕ; нельзя делать `shield = 0` до вызова `on_turn_start_passive`
- `_steam_combo_triggered` — флаг на combat_manager, сбрасывается перед каждым `card.apply`
- `gain_shield` без `combat_manager` → `on_shield_gained` не сработает
- `on_heal_passive` вызывается только если `hasattr(self, 'on_heal_passive')` — враги не затронуты
- Pygame не поддерживает эмодзи в SysFont → текстовые маркеры (`[A]`)
- `view.view.gm` — двойной view это баг
- `pygame.display.flip()` — один раз в конце `GameView.draw()`
- `EventView.py` — НЕ класс, только функции
- `self.relics` (не `self.player_relics`!) в GameManager
- `tick_statuses` принимает `combat_manager=None` — всегда передавать `self` из CombatManager
- `spawn_procedural_enemy` — МЕТОД GameManager, не импортировать из `core.enemies`
- `CombatManager.__init__`: `(player, enemy, starting_deck, game_manager=None)`
- `RARITY_COLORS` импортировать из `core.rarity`
- `on_wet_applied` — через `Creature.add_status`, НЕ напрямую
- `ui/chest/` — маленькая c: `from ui.chest import ...`
- `VictoryScreen._show_modal` — классовая переменная, сбрасывается в `_proceed()`
- `CardRenderer.draw(player=None)` — карта всегда доступна (`can_afford=True`)
- `_EXTRA_KEYWORDS` — модульная переменная в `CardRenderer.py`, НЕ в StatusRegistry
- `draw_pile_rect` и `discard_pile_rect` — атрибуты GameView, не CombatInterface
- `VampireDamageEffect` — DEPRECATED stub, не использовать
- `random.shuffle` в тултипе стопки — НЕ вызывать каждый кадр
- `end_turn_rect` пересчитывается каждый кадр в `_draw_end_turn_btn`
- Hover кнопки конца хода: прямая проверка `pygame.mouse.get_pos()`, НЕ через `view.hover.end_turn`

## Правила работы
- Никогда не просить у пользователя отдельные файлы — брать из репо напрямую
- В конце каждой сессии — полный готовый текст `_project_map.md` для ручной вставки

## План Сессии 26
1. Аудит вызовов `gain_shield` в картах/реликвиях — убедиться что везде передаётся `combat_manager`
2. Тестирование ЖелезнойВоли и ШипастойБрони
3. Проектирование и реализация активных способностей классов (инфраструктура: UI слот, `activate()`, cooldown/charges, InputHandler)
4. Балансировка по результатам тестирования