# Roguelike-CardGame — Project Map
_Последнее обновление: Сессия 24, Jun 3, 2026_

## Архитектура

- `core/` — вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py)
- `ui/` — вся отрисовка (CardRenderer.py, CombatInterface.py, GameView.py, HubView.py, MainMenu.py и др.)
- `managers/` — CombatManager, DeckManager, GameManager, MapGenerator, network_manager
- Разрешение: строго **1920×1080** Full HD
- **Ветка разработки: dev** (main — стабильная, dev — активная работа)

---

## Железные ГОСТы

- Лимит файла: **150 строк** (золотой стандарт, выбиваться нежелательно)
- Если файл разрастается — рефакторинг и разбивка на модули
- Модульность и логичные зависимости — главный принцип
- Никаких "божественных объектов"

---

## Навигация по проекту

- Читать этот файл **ПЕРВЫМ** в каждой сессии
- Большие файлы (GameManager.py, CombatInterface.py, GameView.py) — использовать `query_context`
- Остальные файлы читаются за один запрос напрямую
- Все файлы читать из ветки **dev**:
  `https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу`

---

## Полный список файлов
main.py, server.py, _project_map.md

core/rarity.py, core/Creature.py, core/EffectCalculator.py, core/StatusRegistry.py

core/cards/init.py, base.py, basic.py, fire.py, poison.py, water.py, heal.py

core/cards/buff/init.py, strength.py, thorns.py, regen.py, vampirism.py

core/cards/debuff/init.py, vulnerable.py, weak.py, bleed.py

core/enemies/init.py, base.py, cultist.py, slime.py, boss.py

core/players/init.py, base.py, mage.py, rogue.py, warrior.py, druid.py, berserker.py

core/relics/init.py, base.py, starter.py, elemental.py, advanced.py

managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py, MapGenerator.py, network_manager.py

ui/chest/init.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py

ui/combat/init.py, hud.py

ui/events/init.py, event_data.py, event_effects.py, positive.py, negative.py, neutral.py, special.py

ui/Campfire.py, CardRenderer.py, CombatInterface.py, CardLibraryView.py

ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py

ui/VictoryScreen.py


---

## Ключевые системы

### Creature.py
Базовый класс. `hp`, `shield`, `self.statuses={}` через `__getattr__`/`__setattr__`.
- `take_damage(amount, attacker=None, combat_manager=None)`
- `heal(amount, combat_manager=None)`
- `gain_shield(amount, combat_manager=None)` — с хуком `on_shield_gained`

### StatusRegistry.py
Единый реестр всех 10 статусов: `vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire`

### EffectCalculator.py
Единая точка боевой математики. `dry_run=True` для превью. Обновляет `gm.stats["max_damage_dealt"]`.
Определяет `is_player_attack`, передаёт в `on_damage_calculated`.
Пассив Берсерка: `бонус = int((1 - hp/max_hp) * 10)`, применяется между шагом 2 (ярость) и шагом 3 (слабость), только `is_player_attack` и `type(attacker).__name__ == "Berserker"`.

### Хуки реликвий
`on_combat_start`, `on_turn_start`, `on_damage_calculated(base_dmg, is_player_attack=True)`,
`on_tick_ignited`, `on_wet_applied`, `on_card_played`, `on_shield_gained(amount, creature, combat_manager=None)`,
`on_kill` (заглушка), `on_combat_end`, `on_bleed_tick`, `on_heal`, `on_chest_opened`

`on_turn_start` — вызывается в `CombatManager.start_turn_phase` **ПОСЛЕ** сброса щита.

### Персонажи
Warrior (HP80, E3), Rogue (HP65, E4), Mage (HP55, E3), Druid (HP70, E3), Berserker (HP60, E3)

### Враги
Cultist, SlimeAndGoblins, BossTitan

### Формулы врагов (тестовый режим)
- `hp = 20 + floor×3 + tier×10`
- `dmg = 3 + tier×1`
- `shld = 2`
- Босс: `hp×2.2, dmg×1.3, shld×1.8, shield=shld×2`

### Лидерборд
Google Apps Script, асинхронный фоновый поток `threading.Thread daemon=True`

---

## Реализованные системы

Все 14 пунктов плана масштабируемости (A–N) **ВЫПОЛНЕНЫ**.

### Реликвии — 19 итого
- **COMMON:** LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок
- **UNCOMMON:** ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник, ШипастаяБроня
- **RARE:** ЭнергоЯдро, СердцеТитана, ГнилойКлык, ЖелезнаяВоля
- **LEGENDARY:** ПроклятаяКорона

### Сессия 24 — Combat UI Refactor

**[UI-08] CombatInterface.py** — полный рефакторинг под тёмно-синюю тему:
- Палитра: BG=(12,12,22), панели=(22,22,40), рамки=(160,160,255), золото=(255,220,60)
- Геометрия 1920×1080: игрок слева (x=30), враг справа зеркально (x=1330), отступ 30px от краёв
- Полоса реликвий вверху (высота 52px)
- HP-бары с проекцией урона: намерение врага → на бар игрока, hover-карта → на бар врага
- Энергия: ромбы вместо кружков (`CombatHUD.draw_energy_diamonds`)
- Статусы: бейджи без лейбла "Статусы:", компактно
- Лог боевых действий: под панелью врага, тот же правый край (x=1330)
- Кнопка "КОНЕЦ ХОДА": над рубашкой сброса, правый край совпадает с рубашкой
- Hover кнопки: `btn.collidepoint(pygame.mouse.get_pos())` — прямая проверка, не через `view.hover`
- Разделители: `pygame.draw.line` вместо текстовых `---`
- Шрифты: main=24bold, card=18, desc=14

**[UI-09] ui/combat/hud.py** — новый файл `CombatHUD`:
- `draw_hp_bar`: HP + проекция урона (красная) + щит (синяя полоска сверху)
- `draw_energy_diamonds`: ромбы энергии
- `draw_status_badges`: бейджи статусов из StatusRegistry
- `draw_relics`: полоса реликвий с поддержкой активных (`[A]` префикс)
- `draw_status_tooltip`, `draw_relic_tooltip`, `draw_pile_tooltip`: единый `_draw_tooltip` хелпер
- `get_intent_damage_color`: красный если пробивает щит, синий если нет

---

## Важные детали

- `on_damage_calculated(base_dmg, is_player_attack=True)` — ВСЕГДА проверять флаг в реликвиях
- `Creature.gain_shield(amount, combat_manager=None)` — `combat_manager` нужен для `on_shield_gained`; всегда передавать `cm`
- `bleed`: триггер в `take_damage` при `amount>0`; сброс `=0` (без ГнилогоКлыка) или `//=2` (с ним)
- `vampire`: триггер в `take_damage` при `amount>0` и `attacker.vampire>0`; хил `max(1, amount//2)`; `vampire //= 2`
- `VampireDamageEffect`: DEPRECATED stub в `base.py`, не использовать
- `VampireBuffEffect`: живёт в `core/cards/buff/vampirism.py`
- `distribute_combat_rewards()` → `pending_rewards` → VICTORY
- `CardLibraryView`: карты привязаны к классам, `NEW_CARDS` упразднён
- ПроклятаяКорона: gold reward пропуск — РЕАЛИЗОВАН (Сессия 23)
- `ui/chest/shared.py`: `draw_card_row` возвращает `(card, rect)` или `None` — не ломать контракт
- `CardRenderer.draw` сигнатура: `(surface, card, x, y, font_title, font_desc, is_hovered=False, player=None, enemy=None)` — НЕ Rect!
- `_EXTRA_KEYWORDS` — модульная переменная в `CardRenderer.py`, НЕ в `StatusRegistry`
- `draw_pile_rect` и `discard_pile_rect` — атрибуты `GameView`, не `CombatInterface`
- `_draw_pile_display` кешируется в `GameView`, обновляется по `[id(c) for c in dm.draw_pile]`
- `temp_cost` на карте — временный атрибут Разбойника, живёт только в руке
- `ЖелезнаяВоля`: `is_active=True`, `activate()` вызывается из `InputHandler` при клике
- `end_turn_rect` пересчитывается каждый кадр в `_draw_end_turn_btn` (не хранить статично в `GameView`)
- Hover кнопки конца хода: прямая проверка `pygame.mouse.get_pos()`, НЕ через `view.hover.end_turn`

---

## Важные грабли

- Отступы Python сбиваются при копировании из чата — всегда проверять
- `view.view.gm` — двойной view это баг
- Pygame не поддерживает эмодзи в SysFont — использовать текстовые маркеры (`[A]` для активных)
- `pygame.display.flip()` — один раз в конце `GameView.draw()`
- `EventView.py` — НЕ класс, только функции
- `self.relics` (не `self.player_relics`!) в `GameManager`
- `tick_statuses` принимает `combat_manager=None` — всегда передавать `self` из `CombatManager`
- `spawn_procedural_enemy` — МЕТОД `GameManager`, не импортировать из `core.enemies`
- `CombatManager.__init__`: `(player, enemy, starting_deck, game_manager=None)`
- `RARITY_COLORS` импортировать из `core.rarity`
- `on_wet_applied` — через `Creature.add_status`, НЕ напрямую
- `bonus_draw` — `getattr` с дефолтом 0
- `ui/chest/` — маленькая c: `from ui.chest import ...`
- `VictoryScreen._show_modal` — классовая переменная, сбрасывается в `_proceed()`
- `random.shuffle` в тултипе стопки — НЕ вызывать каждый кадр
- `InputHandler` обрабатывает только `MOUSEDOWN` (клики), `MOUSEMOTION` не реализован — hover считать прямо в draw-методах через `pygame.mouse.get_pos()`

---

## Задачи для будущих сессий

### Пассивные врождённые механики классов
- Берсерк и Разбойник — уже есть
- Нужно добавить: Warrior, Mage, Druid

### on_kill хук — реликвии-заглушки
- Пока 1 враг в бою → не имеет смысла
- Когда появятся мульти-враги → Трофейный Клык (UNCOMMON, +1 Сила), Берсерк-Медальон (RARE, +1 Энергия)

### Активные реликвии — панель UI
- ЖелезнаяВоля — первый активный артефакт (реализован Сессия 23)
- Панель уже подготовлена под расширение

---

## План Сессии 25

**Приоритет 1:**
1. Аудит вызовов `gain_shield` в картах/реликвиях — убедиться что везде передаётся `combat_manager`
2. Тестирование ЖелезнойВоли и ШипастойБрони

**Приоритет 2:**
3. Пассивные врождённые механики классов: Warrior, Mage, Druid
4. Балансировка врагов и карт по результатам тестирования

---

_Статус: Сессия 24 завершена (Jun 3, 2026). Следующая: тестирование новых реликвий + пассивки классов._