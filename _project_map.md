# _project_map.md — Roguelike Card Game
_Последнее обновление: Jun 2, 2026 — Сессия 11_

## ЧИТАТЬ ПЕРВЫМ В КАЖДОЙ СЕССИИ

---

## АРХИТЕКТУРА
core/ — вся логика

ui/ — вся отрисовка

managers/ — менеджеры состояний и генерация

main.py — точка входа

server.py — лидерборд (Google Apps Script)


Разрешение: **1920×1080** (строго)
Ветка разработки: **dev** (main — стабильная)
Лимит файла: **150 строк** (золотой стандарт)

---

## ПОЛНЫЙ СПИСОК ФАЙЛОВ (после Сессии 11)
main.py

server.py

_project_map.md

core/rarity.py — Rarity enum + RARITY_COLORS dict

core/Creature.py — базовый класс, add_status(key, amount, combat_manager=None)

core/EffectCalculator.py — вся боевая математика, dry_run=True

core/StatusRegistry.py — реестр 7 статусов

core/cards/init.py

core/cards/base.py

core/cards/basic.py

core/cards/fire.py — create_ignite, create_fire_breath

core/cards/poison.py — create_poison_stab, create_toxic_cloud, create_acid_shield

core/cards/water.py — create_splash, create_rain_cloud

core/cards/buff/init.py

core/cards/buff/strength.py — BuffEffect, create_flex, create_battle_cry

core/cards/buff/thorns.py — create_thorn_armor

core/cards/debuff/init.py

core/cards/debuff/vulnerable.py

core/cards/debuff/weak.py

core/enemies/init.py

core/enemies/base.py

core/enemies/cultist.py

core/enemies/slime.py

core/enemies/boss.py

core/players/init.py

core/players/base.py

core/players/mage.py — HP55

core/players/rogue.py — HP65

core/players/warrior.py — HP80

core/relics/init.py — RELIC_POOL по редкостям

core/relics/base.py — Relic + rarity + 8 хуков

core/relics/starter.py — LuckyClover, SpikedBracelet, ТочильныйКамень

core/relics/elemental.py — ДревнееОгниво, НамокшаяРукавица, ЭнергоЯдро

managers/BalanceSimulator.py

managers/CombatManager.py — init(player, enemy, starting_deck, game_manager=None)

managers/DeckManager.py

managers/GameManager.py — player_keys=0, self.relics (не player_relics!)

managers/MapGenerator.py

managers/network_manager.py

ui/chest/init.py — реэкспорт Chest

ui/chest/base.py

ui/chest/common.py — 2 карты на выбор

ui/chest/locked.py — 4 карты + 30-60 золота, требует ключ

ui/chest/cursed.py — 3 баффа из CURSED_BUFF_POOL, каждый стоит HP

ui/chest/data.py

ui/chest/shared.py

ui/combat/init.py

ui/combat/hud.py — draw_relics(), draw_relic_tooltip()

ui/events/init.py

ui/events/event_data.py — get_random_event(gm=None)

ui/events/event_effects.py — apply_effect(), включая remove_flag:key

ui/events/positive.py — 3 позитивных ивента

ui/events/negative.py — 3 негативных ивента

ui/events/neutral.py — 4 нейтральных ивента

ui/events/special.py — особые ивенты с condition: (gm) -> bool

ui/Campfire.py

ui/CardRenderer.py

ui/CombatInterface.py

ui/EventView.py — только функции, НЕ класс

ui/GameView.py

ui/HubView.py

ui/InputHandler.py

ui/LeaderboardView.py — handle_clicks() возвращает только True/False

ui/MainMenu.py

ui/MapView.py

ui/Shop.py


---

## КЛЮЧЕВЫЕ СИСТЕМЫ

### Creature.py
- `self.statuses = {}` через `__getattr__` / `__setattr__`
- `_STATUS_KEYS` вычисляется при загрузке модуля через `all_keys()`
- `add_status(key, amount, combat_manager=None)` — хук `on_wet_applied` внутри

### StatusRegistry.py
Единый реестр 7 статусов. Добавить статус = одна запись здесь.
Поля: `abbr, badge_bg, badge_fg, tooltip, keyword, is_duration, is_stack`

### EffectCalculator.py
Цепочка: реликвии → ярость → слабость → уязвимость → комбо пар
Поддерживает `dry_run=True`

### Реликвии — хуки
| Хук | Где вызывается | Статус |
|-----|---------------|--------|
| on_combat_start | CombatManager.__init__ | ✅ |
| on_turn_start | CombatManager.start_turn | ✅ |
| on_damage_calculated | EffectCalculator | ✅ |
| on_tick_ignited | tick_statuses | ✅ |
| on_wet_applied | Creature.add_status | ✅ |
| on_card_played | play_card_by_index | ⚠️ заглушка |
| on_shield_gained | Creature.gain_shield | ⚠️ заглушка |
| on_kill | end_turn_phase | ⚠️ заглушка |

### Система сундуков
- Импорт: `from ui.chest import Chest` (маленькая c — ОБЯЗАТЕЛЬНО)
- Веса: common 33 / locked 33 / cursed 34
- Босс роняет ключ → `player_keys` в GameManager
- `player.bonus_draw` — `getattr` с дефолтом 0

### Система ивентов
- `get_random_event(gm=None)` — без gm: только обычные; с gm: особые с выполненным `condition` добавляются в пул ×2
- Добавить особый ивент = одна запись в `special.py`

### Формулы врагов
**Боевые:**
- `hp = 40 + floor×8 + tier×25`
- `dmg = 5 + floor×1 + tier×4`
- `shld = 3 + floor×1`
- Босс (local_step==20): hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

**⚠️ Тестовый режим (активен):**
- `hp = 20 + floor×3 + tier×10`
- `dmg = 3 + tier×1`
- `shld = 2`

---

## ВАЖНЫЕ ГРАБЛИ

- `from ui.chest import Chest` — маленькая `c`, иначе ImportError на Linux/Mac
- `view.view.gm` — двойной view это баг
- `pygame.display.flip()` — только один раз, в конце `draw()`
- Pygame не поддерживает эмодзи в SysFont
- `EventView.py` — только функции, НЕ класс
- `self.relics` (не `self.player_relics`!) в GameManager
- `tick_statuses` принимает `combat_manager=None` — всегда передавать `self` из CombatManager
- `spawn_procedural_enemy` — МЕТОД GameManager, не импортировать из `core.enemies`
- `BotCombatManager`: бой стартует в `__init__`, вызывать `run_bot_loop()` после
- `RARITY_COLORS` импортировать из `core.rarity` (не из `core.relics`)
- `on_wet_applied` вызывается через `Creature.add_status`, НЕ напрямую из StatusEffect
- При копировании кода из чата легко сбиваются отступы — всегда проверять
- Все файлы читать из ветки **dev**, не main

---

## ИСПРАВЛЕННЫЕ БАГИ (последние)

| # | Файл | Проблема |
|---|------|----------|
| 53 | GameView, InputHandler, MapView | `from ui.Chest` → `from ui.chest` (регистр) |

---

## СТАТУС РЕАЛИЗАЦИИ

✅ Все 14 пунктов плана масштабируемости (A–N)
✅ Система сундуков (ui/chest/, 3 типа, ключи)
✅ Система ивентов (ui/events/, типы + special с condition)
✅ UI реликвий в бою (рамки по редкости, тултипы)
✅ Хук on_wet_applied в Creature.add_status
✅ Аудит всех 6 реликвий — все работают

---

## ПЛАН — СЕССИЯ 12

### Приоритет 1 — хуки-заглушки
1. `on_card_played` → `CombatManager.play_card_by_index`
2. `on_shield_gained` → `Creature.gain_shield`
3. `on_kill` → `CombatManager.end_turn_phase`
4. Первые реликвии на этих хуках (UNCOMMON/RARE)

### Приоритет 2 — контент
- Новые карты UNCOMMON/RARE/EPIC для каждого класса
- Реликвии EPIC/LEGENDARY
- Экран выбора реликвии с рамкой по редкости
- Запустить BalanceSimulator, проверить win rate