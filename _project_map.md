# Project Map — Roguelike Card Game
_Обновлено: Jun 2, 2026_

---

## Структура проекта
main.py

server.py

core/

Creature.py

EffectCalculator.py

cards/

base.py, basic.py, fire.py, poison.py, water.py

buff/strength.py, buff/thorns.py

debuff/vulnerable.py, debuff/weak.py
enemies/

base.py, cultist.py, slime.py, boss.py
players/

base.py, warrior.py, rogue.py, mage.py
relics/

base.py, starter.py, elemental.py
managers/

GameManager.py ⚠️ большой файл — использовать query_context

CombatManager.py

DeckManager.py

BalanceSimulator.py

network_manager.py

ui/

MainMenu.py, HubView.py, GameView.py

MapView.py, CombatInterface.py, CardRenderer.py

Shop.py, Campfire.py, Chest.py, EventView.py

InputHandler.py, LeaderboardView.py


---

## Ключевые классы и сигнатуры

### core/Creature.py
Базовый класс для игрока и врагов.
- `__init__(name, hp, max_hp)`
- Поля: `hp, max_hp, shield, strength, thorns`
- Статусы: `vulnerable, weak, wet, ignited, poison`
- `take_damage(amount, attacker=None)`
- `gain_shield(amount)`
- `tick_statuses(combat_manager=None)` — вызывается в конце хода

### core/EffectCalculator.py
Единая точка боевой математики.
- `calculate_damage(attacker, target, base_damage, gm=None, cm=None, dry_run=False)`
- Формула: `(base + relic + strength) × 0.75_weak × 1.5_vulnerable × 2.0_комбо_пар`
- `dry_run=True` — без побочных эффектов, для предпросмотра урона на карте

### managers/GameManager.py  ⚠️ большой
- `spawn_procedural_enemy()` — генерирует врага по этажу, создаёт CombatManager
  - Формулы: `hp = 20 + floor×3 + tier×10`, `dmg = 3 + tier×1`, `shld = 2` _(тестовый режим)_
  - Босс (local_step==20): hp×2.2, dmg×1.3, shld×1.8, shield=shld×2
- `add_card(card)` — добавляет карту в current_deck
- `enter_chosen_room(room_type, col)` — роутинг по типу узла
- `get_available_nodes()` — доступные узлы карты
- Поля: `current_floor, relics[], current_deck, player, active_combat, event_result`
- `reset()` — НЕТ. При новом забеге создаётся новый `GameManager()`
- Константы: `FLOORS_PER_ACT = 20`, `NODE_WEIGHTS: COMBAT=55, CAMPFIRE=15, SHOP=10, CHEST=12, EVENT=8`

### managers/CombatManager.py
- `start_turn_phase()` — начало хода игрока
- `end_turn_phase()` — конец хода, тики статусов, ход врага, проверка смерти
- `add_log_message(text)` — лог боя
- Реликвии: хуки `on_combat_start` срабатывают ДО `start_turn_phase()`
- Проверка `enemy.hp <= 0` в `end_turn_phase()` ДО начала нового хода

### core/enemies/base.py — Enemy(Creature)
- Поля: `base_test_damage, base_test_shield, intent_type, intent_value, turn_count`
- `choose_intent()` — переопределяется в каждом моб-классе
- `execute_intent(player, combat_manager=None)` — выполняет намерение, вызывает `turn_count += 1`

### core/enemies/cultist.py — Cultist(Enemy)
- Ход 0: defend (base_test_shield)
- Ход 1+: attack (base_test_damage + turn_count), разгон +1/ход

### core/enemies/slime.py — SlimeAndGoblins(Enemy)
- Чётный ход: attack (base_test_damage)
- Нечётный ход: defend (base_test_shield + 2)

### core/enemies/boss.py — BossTitan(Enemy)
- step 0: defend (base_test_shield × 2)
- step 1: debuff weak +2
- step 2: attack (base_test_damage × 2)
- `turn_count += 1` — в `choose_intent()` (НЕ в execute_intent!)

### core/relics/base.py
Хуки: `on_combat_start, on_turn_start, on_damage_calculated, on_tick_ignited, on_wet_applied`

### ui/CardRenderer.py
- `draw(surface, card, x, y, player=None, enemy=None)`
- Рамка — всегда цвет стихии, не меняется при апгрейде
- Апгрейд: `"+"` в названии карты
- `_resolve_description()` — подставляет реальный урон через `EffectCalculator(dry_run=True)`

### ui/InputHandler.py
⚠️ Единственное место логики рестарта:
```python
Блок LEADERBOARD при handle_clicks() == True:
Shop.reset() + Campfire.reset() + MainMenu.reset() + event_reset() + GameManager()


### ui/EventView.py
- НЕ класс — модуль функций
- `init_event(gm)` — вызывается из MapView при входе в EVENT
- `reset()` — вызывается при рестарте из InputHandler
- `from ui.EventView import handle_clicks as event_clicks` — правильный импорт

### ui/MapView.py
- `handle_click()` → `gm.enter_chosen_room()` → роутинг:
  - CHEST → `Chest.init_chest(view)`
  - EVENT → `EventView.init_event(gm)`
  - BOSS → `room_type = "COMBAT"`
- Ориентация: row=X, col=Y, три пути `ROW_Y=[300, 540, 780]`

### ui/HubView.py
- `reset()` — сбрасывает анимацию стопки карт при старте забега
- Эмодзи НЕ использовать (pygame SysFont не рендерит)
- `spread_total` ограничен шириной экрана

### ui/MainMenu.py
- `reset()` classmethod → `cls._hub = None`

### managers/network_manager.py
- `send_run_record()` — асинхронный `threading.Thread(daemon=True)`
- `fetch_top_scores()` → `leaderboard_cache`

---

## Цепочки вызовов
Бой
MapView.handle_click()

→ gm.enter_chosen_room("COMBAT")

→ gm.spawn_procedural_enemy()

  → CombatManager(player, enemy, deck, gm)
Ход врага
CombatManager.end_turn_phase()

→ enemy.choose_intent()

→ enemy.execute_intent(player, combat_manager)

→ EffectCalculator.calculate_damage(...)

→ player.take_damage(final_dmg, attacker=enemy)
Рестарт
InputHandler (LEADERBOARD блок)

→ LeaderboardView.handle_clicks() == True

→ Shop.reset(), Campfire.reset(), MainMenu.reset(), event_reset()

→ GameManager() (новый объект)
Добавление карты (везде одинаково)
gm.add_card(card) ← Shop, Chest, Campfire


---

## Экономика (актуальные значения)

| Параметр | Значение |
|---|---|
| Стартовое золото | 100 |
| Награда за бой | `random.randint(20, 35) + floor × 3` |
| Цена карты в магазине | `35 + floor × 3` |
| Цена сжигания | `(15 + floor × 2) + removal_count × 25` |
| Костёр | бесплатно (лечение +25 HP или апгрейд) |

---

## Персонажи

| Класс | HP |
|---|---|
| Warrior | 80 |
| Rogue | 65 |
| Mage | 55 |

---

## Грабли (не повторять)

- `view.view.gm` — двойной view это баг
- Эмодзи в pygame SysFont — не рендерятся, никогда не использовать
- `EventView` — НЕ класс, импортировать функции напрямую
- `self.relics` (не `self.player_relics!`) в GameManager
- `tick_statuses(combat_manager=None)` — всегда передавать `self` из CombatManager
- `spawn_procedural_enemy` — МЕТОД GameManager, не импортировать из `core.enemies`
- `LeaderboardView.handle_clicks()` — только возвращает True/False, рестарт в InputHandler
- `pygame.display.flip()` — один раз в конце `draw()`, не внутри методов
- Отступы Python при копировании из чата — всегда проверять структуру

---

## Файлы без сюрпризов (читать напрямую, влезают в контекст)

Все файлы кроме `GameManager.py` и `CombatInterface.py` — читаются за один запрос.