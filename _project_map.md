# Project Map — Roguelike Card Game
_Обновлено: Jun 2, 2026 — Сессия 6_

---

## Структура проекта
main.py

server.py

_project_map.md

core/

rarity.py ← НОВЫЙ (Сессия 6, запланирован): Rarity enum

Creature.py ← self.statuses={}, getattr/setattr, обратная совместимость

EffectCalculator.py

StatusRegistry.py ← ЕДИНЫЙ реестр 7 статусов (Сессия 4)

cards/

base.py            ← Card + rarity поле (Сессия 6, запланировано)

basic.py, fire.py, poison.py, water.py

buff/strength.py, buff/thorns.py

debuff/vulnerable.py, debuff/weak.py
enemies/

base.py, cultist.py, slime.py, boss.py
players/

base.py, warrior.py, rogue.py, mage.py
relics/

__init__.py        ← RELIC_POOL по редкостям (Сессия 6, запланировано)

base.py            ← Relic + rarity поле (Сессия 6, запланировано)

starter.py, elemental.py
managers/

GameManager.py ← ~110 строк

MapGenerator.py ← НОВЫЙ (Сессия 5): MapNode, generate_map(), _pick_node_type()

CombatManager.py

DeckManager.py

BalanceSimulator.py

network_manager.py

ui/

MainMenu.py, HubView.py

GameView.py ⚠️ ~160 строк — использовать query_context

MapView.py

CombatInterface.py ← оркестратор ~60 строк (Сессия 6)

combat/

__init__.py

hud.py             ← НОВЫЙ (Сессия 6): CombatHUD
CardRenderer.py

Shop.py, Campfire.py, Chest.py

EventView.py ← ~80 строк (Сессия 5)

events/

__init__.py

event_data.py      ← НОВЫЙ (Сессия 5)

event_effects.py   ← НОВЫЙ (Сессия 5)
InputHandler.py, LeaderboardView.py


---

## ПЛАН СЛЕДУЮЩЕЙ СЕССИИ (Сессия 7)

### Приоритет 1 — СРОЧНО

**A. core/rarity.py** (новый файл):
```python

from enum import Enum

class Rarity(Enum):

    COMMON    = "common"

    UNCOMMON  = "uncommon"

    RARE      = "rare"

    EPIC      = "epic"

    LEGENDARY = "legendary"
B. core/cards/base.py — два изменения:

Card.__init__ получает rarity=Rarity.COMMON (все существующие карты автоматически COMMON)
StatusEffect.execute() убрать if/elif, читать через creature.add_status(key, val) из StatusRegistry
C. core/relics/base.py:

Relic.__init__ получает rarity=Rarity.COMMON
D. core/relics/init.py — RELIC_POOL по редкостям:


RELIC_POOL = {

    Rarity.COMMON:    [LuckyClover, SpikedBracelet, ТочильныйКамень],

    Rarity.UNCOMMON:  [ЭнергоЯдро, ДревнееОгниво, НамокшаяРукавица],

    Rarity.RARE:      [],

    Rarity.EPIC:      [],

    Rarity.LEGENDARY: [],

}
GameManager.distribute_combat_rewards читает из пула, не перечисляет классы вручную.

E. GameManager.spawn_procedural_enemy — EnemyRegistry вместо if "Культист" in e_name:

ENEMY_POOL в core/enemies/__init__.py: список классов врагов
GameManager тянет пул оттуда, не знает конкретных классов
Приоритет 2 — ПРЕВЕНТИВНО
F. InputHandler.py — словарь-диспетчер:


STATE_HANDLERS = {

    "COMBAT": _handle_combat,

    "CAMPFIRE": _handle_campfire,

    ...

}
G. GameView.draw() — словарь-диспетчер:


DRAW_HANDLERS = {

    "COMBAT": CombatInterface.draw_combat_screen,

    ...

}
H. enemies/base.py — намерения как объекты:

IntentAttack, IntentDefend, IntentDebuff и т.д.
execute_intent вызывает self.intent_obj.execute(...)
I. MapGenerator.py — конфиг вместо логики:


ROW_OVERRIDES = {0: "COMBAT", 19: "BOSS", 18: ["CAMPFIRE", "SHOP"]}
J. GameView.py — HoverState dataclass:


@dataclass

class HoverState:

    status_key: str = None

    status_val: int = 0

    card_index: int = -1

    card_rect: pygame.Rect = None

    card_obj: object = None

    enemy_badge_rects: list = field(default_factory=list)

    player_badge_rects: list = field(default_factory=list)
K. CardRenderer.py — аудит веток card_type

Приоритет 3 — АРХИТЕКТУРНЫЕ УЛУЧШЕНИЯ
L. relics/base.py — аудит хуков (on_card_played, on_shield_gained?)
M. players/base.py — стартовые деки при добавлении Rogue/Mage карт
N. BalanceSimulator.py — проверка актуальности формул

Ключевые классы и сигнатуры
core/rarity.py ← НОВЫЙ (Сессия 6)

from core.rarity import Rarity
Rarity.COMMON / UNCOMMON / RARE / EPIC / LEGENDARY

### core/StatusRegistry.py
```python

from core.StatusRegistry import STATUSES, get, all_keys
Поля: abbr, badge_bg, badge_fg, tooltip, keyword (tuple), is_duration, is_stack
Статусы: vulnerable, weak, wet, ignited, poison, strength, thorns

### core/Creature.py
```python

__init__(name, hp, max_hp)
self.statuses = {k: 0 for k in _STATUS_KEYS}
getattr / setattr -- creature.weak работает как раньше
API: get_status(key), set_status(key, val), add_status(key, amount)
take_damage(amount, attacker=None)

gain_shield(amount)

tick_statuses(combat_manager=None)


### core/EffectCalculator.py
```python

calculate_damage(attacker, target, base_damage, gm=None, cm=None, dry_run=False)
Формула: (base + relic + strength) × 0.75_weak × 1.5_vulnerable × 2.0_комбо_пар
dry_run=True -- без побочных эффектов, для предпросмотра

### managers/MapGenerator.py
```python

FLOORS_PER_ACT = 20

NODE_WEIGHTS   # веса типов узлов

MapNode(node_type, col, row)  # .connections[]

_pick_node_type(row)

generate_map() -> list[list[MapNode]]
managers/GameManager.py

spawn_procedural_enemy()   # формулы тест: hp=20+floor×3+tier×10, dmg=3+tier×1, shld=2

add_card(card)

enter_chosen_room(room_type, col)

get_available_nodes()

distribute_combat_rewards()

setup_next_floor()
Поля: current_floor, relics[], current_deck, player, active_combat, event_result
⚠️ НЕ содержит ручной if для ЭнергоЯдро

### managers/CombatManager.py
```python

start_turn_phase()

end_turn_phase()

add_log_message(text)
Реликвии on_combat_start ДО start_turn_phase()
Проверка enemy.hp <= 0 ДО начала нового хода

### core/enemies/base.py — Enemy(Creature)
```python
Поля: base_test_damage, base_test_shield, intent_type, intent_value, turn_count
choose_intent() # переопределяется в каждом классе

execute_intent(player, combat_manager=None)


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
- turn_count += 1 в choose_intent() (НЕ в execute_intent!)

### core/relics/base.py
```python
Хуки: on_combat_start, on_turn_start, on_damage_calculated,
on_tick_ignited, on_wet_applied
rarity=Rarity.COMMON (Сессия 6, запланировано)

### core/relics/starter.py
- LuckyClover — on_combat_start: +2 карты
- SpikedBracelet — on_combat_start: +10 щита
- ТочильныйКамень — on_damage_calculated: base_dmg + 2

### core/relics/elemental.py
- ЭнергоЯдро — on_combat_start: max_energy +1, energy +1 (флаг _applied, один раз)
- ДревнееОгниво — on_tick_ignited: +2 к урону тика
- НамокшаяРукавица — on_wet_applied: +4 щита игроку
- ⚠️ Реликвии управляют эффектами САМИ. GameManager не дублирует.

### core/cards/fire.py
⚠️ Только: create_ignite, create_fire_breath

### core/cards/water.py
⚠️ Только: create_splash, create_rain_cloud

### core/cards/poison.py
⚠️ create_poison_stab (НЕ create_poison_dart), create_toxic_cloud, create_acid_shield

### ui/combat/hud.py ← НОВЫЙ (Сессия 6)
```python

class CombatHUD:

    draw_hp_bar(screen, x, y, width, height, current_hp, max_hp, shield)

    get_intent_damage_color(predicted_dmg, player_shield)

    draw_status_badges(screen, font, creature, x, y) -> [(rect, key, val)]

    draw_status_tooltip(screen, font_desc, status_key, status_val, mouse_pos)
ui/CombatInterface.py ← оркестратор (Сессия 6)

class CombatInterface:

    draw_combat_screen(view)  # импортирует CombatHUD
ui/events/event_data.py

CARD_FACTORIES   # список всех фабрик карт

EVENTS           # 7 событий, эффекты как строки ("heal:20", "lose_hp:15", ...)

get_random_event()
ui/events/event_effects.py

apply_effect(effect_str, gm)

apply_option(option, gm)
Ключи: heal, lose_hp, gain_gold, lose_gold, gain_card, gain_random_card, gain_relic, skip

### ui/EventView.py (~80 строк)
```python
НЕ класс -- модуль функций
init_event(gm)

reset()

from ui.EventView import handle_clicks as event_clicks ← правильный импорт

### ui/CardRenderer.py
```python

draw(surface, card, x, y, font_title, font_desc, is_hovered=False, player=None, enemy=None)
Рамка -- всегда цвет стихии
_resolve_description() -- реальный урон через EffectCalculator(dry_run=True)
_draw_unaffordable_overlay() -- 50% затемнение
_get_card_keywords(card) -> [(key, val)]
draw_card_keyword_tooltip() -- Hearthstone-style

⚠️ Читает из StatusRegistry, KEYWORD_DESCRIPTIONS убран

### ui/GameView.py (~160 строк) ⚠️ использовать query_context
```python
Hover-состояния (плоские атрибуты, рефакторинг в HoverState запланирован):
hovered_status_key, hovered_status_val

enemy_badge_rects, player_badge_rects # тройки (rect, key, val)

hovered_card_index, hovered_card_rect, hovered_card_obj


### ui/InputHandler.py
```python

process_mouse_clicks(view, mouse_pos)

process_scroll(view, event_button)
⚠️ Единственное место логики рестарта (LEADERBOARD блок):
Shop.reset() + Campfire.reset() + MainMenu.reset() + event_reset() + GameManager()

### ui/MapView.py
```python

handle_click() -> gm.enter_chosen_room()
CHEST -> Chest.init_chest(view)
EVENT -> EventView.init_event(gm)
BOSS -> room_type = "COMBAT"
Ориентация: row=X, col=Y, три пути ROW_Y=[300, 540, 780]

---

## Цепочки вызовов

**Бой:**
MapView.handle_click()

→ gm.enter_chosen_room("COMBAT")

→ gm.spawn_procedural_enemy()

→ CombatManager(player, enemy, deck, gm)

→ for relic in gm.relics: relic.on_combat_start(self) ← ДО start_turn_phase

→ self.start_turn_phase()


**Генерация карты:**
gm.setup_next_floor() (local_step == 1)

→ MapGenerator.generate_map()

→ gm.map_grid = result


**Ход врага:**
CombatManager.end_turn_phase()

→ enemy.execute_intent(player, combat_manager)

→ EffectCalculator.calculate_damage(...)

→ player.take_damage(final_dmg, attacker=enemy)


**Рестарт:**
InputHandler (LEADERBOARD блок)

→ LeaderboardView.handle_clicks() == True

→ Shop.reset(), Campfire.reset(), MainMenu.reset(), event_reset()

→ GameManager() (новый объект)


**Добавление карты (везде одинаково):**
gm.add_card(card) ← Shop, Chest, Campfire, EventView


---

## Экономика

| Параметр | Значение |
|----------|----------|
| Стартовое золото | 100 |
| Награда за бой | random.randint(20, 35) + floor × 3 |
| Цена карты в магазине | 35 + floor × 3 |
| Цена сжигания | (15 + floor × 2) + removal_count × 25 |
| Костёр | бесплатно (лечение +25 HP или апгрейд) |

## Персонажи

| Класс | HP | Энергия |
|-------|----|---------|
| Warrior | 80 | 3 |
| Rogue | 65 | 3 |
| Mage | 55 | 3 |

---

## Исправленные баги (51 штука)

| # | Файл | Суть |
|---|------|------|
| 1 | GameView.py | pygame.display.flip() перенесён в конец draw() |
| 2 | GameView.py | CHEST и EVENT рендерятся через нативные модули |
| 3 | InputHandler.py | блоки CHEST и EVENT добавлены |
| 4 | Chest.py | CHEST_CARD_POOL переделан на фабричные функции |
| 5 | Shop.py / Campfire.py | добавлены методы reset() |
| 6 | EventView.py | создан с нуля (7 событий, полный цикл) |
| 7 | EventView.py | ImportError -- не класс, а модуль функций |
| 8 | MapView.py | вызов EventView.init_event(gm) при входе в EVENT |
| 9 | InputHandler.py | event_reset() при рестарте |
| 10 | Chest.py | ложная надпись исправлена |
| 11 | InputHandler.py | удалён мёртвый legacy MAP-блок |
| 12 | EventView.py | gm.player_relics → gm.relics |
| 13 | MapView.py | подсказка y=1050 → y=1040 |
| 14 | Chest.py | gm.current_deck.append() → gm.add_card() |
| 15 | MapView.py | BOSS-узел роутится через room_type = "COMBAT" |
| 16 | Shop.py | gm.current_deck.append() → gm.add_card() |
| 17 | CombatManager.py | реликвии on_combat_start ДО start_turn_phase() |
| 18 | CombatManager.py | проверка enemy.hp <= 0 ДО начала нового хода |
| 19 | core/enemies/__init__.py | удалена сломанная фабрика spawn_procedural_enemy |
| 20 | cultist.py + slime.py | убран двойной turn_count += 1 |
| 21 | core/Creature.py | убрана двойная уязвимость ×1.5 |
| 22 | core/relics/base.py | добавлены хуки on_tick_ignited, on_wet_applied |
| 23 | core/relics/elemental.py | реализованы ЭнергоЯдро, ДревнееОгниво, НамокшаяРукавица |
| 24 | core/Creature.py | tick_statuses принимает combat_manager=None |
| 25 | core/cards/base.py | StatusEffect.execute вызывает on_wet_applied у реликвий |
| 26 | CombatManager.py | tick_statuses передают self |
| 27 | HubView.py | убраны эмодзи из CLASS_INFO |
| 28 | HubView.py | добавлен reset() метод |
| 29 | HubView.py | spread_total ограничен шириной экрана |
| 30 | MainMenu.py | добавлен reset() classmethod |
| 31 | InputHandler.py | MainMenu.reset() в блоке рестарта |
| 32 | LeaderboardView.py | handle_clicks() возвращает True/False |
| 33 | InputHandler.py | единственное место рестарта |
| 34 | network_manager.py | send_run_record() асинхронный |
| 35 | network_manager.py | _get_username() с try/except fallback |
| 36 | GameManager.py | удалён мёртвый импорт spawn_procedural_enemy |
| 37 | EventView.py | исправлены 6 несуществующих импортов карт |
| 38 | GameManager.py | удалён ручной if ЭнергоЯдро (дублировал хук) |
| 39 | CardRenderer.py | § маркер -- только damage числа подсвечиваются |
| 40 | CombatInterface.py | STATUS_STYLES + STATUS_TOOLTIPS для 7 статусов |
| 41 | CombatInterface.py | draw_status_tooltip() с автоприжатием |
| 42 | GameView.py | hovered_status_key/val + badge_rects как тройки |
| 43 | CardRenderer.py | _get_card_keywords() с реальными числами |
| 44 | CardRenderer.py | draw_card_keyword_tooltip() Hearthstone-style |
| 45 | CombatInterface.py | draw_status_tooltip принимает val |
| 46 | core/StatusRegistry.py | СОЗДАН -- единый реестр 7 статусов |
| 47 | CombatInterface.py | убраны STATUS_STYLES/STATUS_TOOLTIPS |
| 48 | CardRenderer.py | убран KEYWORD_DESCRIPTIONS |
| 49 | core/Creature.py | self.statuses={}, getattr/setattr |
| 50 | ui/events/ | создан пакет event_data.py + event_effects.py |
| 51 | managers/MapGenerator.py | создан: MapNode, generate_map(), _pick_node_type() |

---

## Грабли (не повторять)

- `view.view.gm` -- двойной view это баг
- Эмодзи в pygame SysFont -- не рендерятся, никогда
- EventView -- НЕ класс, импортировать функции напрямую
- `self.relics` (не `self.player_relics`!) в GameManager
- `tick_statuses(combat_manager=None)` -- всегда передавать self из CombatManager
- `spawn_procedural_enemy` -- МЕТОД GameManager, не импортировать из core.enemies
- `LeaderboardView.handle_clicks()` -- только True/False, рестарт в InputHandler
- `pygame.display.flip()` -- один раз в конце draw()
- Отступы Python при копировании из чата -- всегда проверять
- Реликвии управляют эффектами САМИ через хуки
- `fire.py`: только create_ignite, create_fire_breath
- `water.py`: только create_splash, create_rain_cloud
- `poison.py`: create_poison_stab (НЕ create_poison_dart)
- StatusRegistry импортируется ДО Creature (порядок ок, нет зависимостей)
- `__setattr__` в Creature: _STATUS_KEYS вычисляется при загрузке модуля
- Все файлы читать из ветки **dev**, не main
- `generate_map()` возвращает map_grid -- GameManager сохраняет сам

---

## Файлы без сюрпризов (читать напрямую)

Все файлы кроме: `CombatInterface.py`, `GameView.py` -- использовать query_context