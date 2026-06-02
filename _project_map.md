# Project Map — Roguelike Card Game
_Обновлено: Jun 2, 2026 — Сессия 4_

---

## Структура проекта
main.py
server.py
_project_map.md

core/
  Creature.py          ← self.statuses={}, __getattr__/__setattr__, обратная совместимость
  EffectCalculator.py
  StatusRegistry.py    ← ЕДИНЫЙ реестр 7 статусов (создан в Сессии 4)
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
  GameManager.py       ⚠️ ~176 строк — использовать query_context
  CombatManager.py
  DeckManager.py
  BalanceSimulator.py
  network_manager.py

ui/
  MainMenu.py, HubView.py
  GameView.py          ⚠️ ~160 строк
  MapView.py
  CombatInterface.py   ⚠️ ~200 строк — использовать query_context
  CardRenderer.py
  Shop.py, Campfire.py, Chest.py
  EventView.py         ⚠️ ~233 строки — использовать query_context
  InputHandler.py, LeaderboardView.py

---

## СЛЕДУЮЩАЯ СТАДИЯ: ДРОБЛЕНИЕ ФАЙЛОВ

### Приоритет 1 — СРОЧНО (уже за лимитом 150 строк)

**A. EventView.py (~233 строк) → разбить на:**
- ui/events/event_data.py — 7 событий как данные (title, text, options + эффекты)
- ui/events/event_effects.py — функции heal, lose_hp, gain_gold, gain_card, gain_relic и т.д.
- ui/EventView.py — только init_event, reset, draw_screen, handle_clicks (~60 строк)

**B. GameManager.py (~176 строк) → разбить на:**
- managers/MapGenerator.py — MapNode, generate_new_map_progression, _pick_node_type (~70 строк)
- managers/GameManager.py — прогрессия, награды, состояние игрока (~110 строк)

### Приоритет 2 — ПРЕВЕНТИВНО (разрастутся при добавлении контента)

**C. CombatInterface.py (~200 строк) → разбить на:**
- ui/combat/hud.py — draw_hp_bar, draw_status_badges, draw_status_tooltip, энергия
- ui/CombatInterface.py — только draw_combat_screen как оркестратор (~60 строк)

**D. InputHandler.py** — при добавлении BOSS_INTRO, DIALOGUE и т.д. разбить на:
  combat_handler.py, map_handler.py, menu_handler.py

**E. core/cards/base.py** — при добавлении HealEffect, DrawEffect разбить на effects/ подпапку

### Приоритет 3 — АРХИТЕКТУРНЫЕ УЛУЧШЕНИЯ (не срочно)

**F.** GameView.py (~160 строк) — hover-логика в отдельный dataclass HoverState
**G.** core/BuffRegistry.py — по аналогии с StatusRegistry когда баффов станет больше 4
**H.** BalanceSimulator.py — проверить актуальность формул после рефакторинга Creature

---

## Ключевые классы и сигнатуры

### core/StatusRegistry.py ← НОВЫЙ (Сессия 4)
Единый реестр всех 7 статусов. Добавить статус = одна запись здесь.
```python

from core.StatusRegistry import STATUSES, get, all_keys
Поля каждой записи: abbr, badge_bg, badge_fg, tooltip, keyword (tuple), is_duration, is_stack
Статусы: vulnerable, weak, wet, ignited, poison, strength, thorns

core/Creature.py ← РЕФАКТОРИНГ (Сессия 4)
Базовый класс для игрока и врагов.

__init__(name, hp, max_hp)
Поля: hp, max_hp, shield
self.statuses = {k: 0 for k in _STATUS_KEYS} — единый словарь статусов
__getattr__ / __setattr__ — прозрачная совместимость (creature.weak работает как раньше)
Публичный API: get_status(key), set_status(key, val), add_status(key, amount)
take_damage(amount, attacker=None)
gain_shield(amount)
tick_statuses(combat_manager=None) — вызывается в конце хода
core/EffectCalculator.py
Единая точка боевой математики.

calculate_damage(attacker, target, base_damage, gm=None, cm=None, dry_run=False)
Формула: (base + relic + strength) × 0.75_weak × 1.5_vulnerable × 2.0_комбо_пар
dry_run=True — без побочных эффектов, для предпросмотра урона на карте
managers/GameManager.py ⚠️ большой
spawn_procedural_enemy() — генерирует врага по этажу, создаёт CombatManager
Формулы (тест): hp = 20 + floor×3 + tier×10, dmg = 3 + tier×1, shld = 2
Формулы (боевые): hp = 40 + floor×8 + tier×25, dmg = 5 + floor×1 + tier×4, shld = 3 + floor×1
Босс (local_step==20): hp×2.2, dmg×1.3, shld×1.8, shield=shld×2
add_card(card) — добавляет карту в current_deck
enter_chosen_room(room_type, col) — роутинг по типу узла
get_available_nodes() — доступные узлы карты
distribute_combat_rewards() — золото + рандомная реликвия
⚠️ НЕ содержит ручной if для ЭнергоЯдро — реликвия управляет сама через хук
Поля: current_floor, relics[], current_deck, player, active_combat, event_result
reset() — НЕТ. При новом забеге создаётся новый GameManager()
Константы: FLOORS_PER_ACT = 20, NODE_WEIGHTS: COMBAT=55, CAMPFIRE=15, SHOP=10, CHEST=12, EVENT=8
managers/CombatManager.py
start_turn_phase() — начало хода игрока
end_turn_phase() — конец хода, тики статусов, ход врага, проверка смерти
add_log_message(text) — лог боя
Реликвии: хуки on_combat_start срабатывают ДО start_turn_phase()
Проверка enemy.hp <= 0 в end_turn_phase() ДО начала нового хода
core/enemies/base.py — Enemy(Creature)
Поля: base_test_damage, base_test_shield, intent_type, intent_value, turn_count
choose_intent() — переопределяется в каждом моб-классе
execute_intent(player, combat_manager=None)
core/enemies/cultist.py — Cultist(Enemy)
Ход 0: defend (base_test_shield)
Ход 1+: attack (base_test_damage + turn_count), разгон +1/ход
core/enemies/slime.py — SlimeAndGoblins(Enemy)
Чётный ход: attack (base_test_damage)
Нечётный ход: defend (base_test_shield + 2)
core/enemies/boss.py — BossTitan(Enemy)
step 0: defend (base_test_shield × 2)
step 1: debuff weak +2
step 2: attack (base_test_damage × 2)
turn_count += 1 — в choose_intent() (НЕ в execute_intent!)
core/relics/base.py
Хуки: on_combat_start, on_turn_start, on_damage_calculated, on_tick_ignited, on_wet_applied

core/relics/starter.py
LuckyClover — on_combat_start: +2 карты в руку
SpikedBracelet — on_combat_start: +10 щита
ТочильныйКамень — on_damage_calculated: base_dmg + 2
core/relics/elemental.py
ЭнергоЯдро — on_combat_start: max_energy +1, energy +1 (один раз за забег, флаг _applied)
⚠️ Правило: только хук управляет эффектом. GameManager НЕ дублирует это вручную.
ДревнееОгниво — on_tick_ignited: возвращает +2 к урону тика горения
НамокшаяРукавица — on_wet_applied: +4 щита игроку
core/cards/fire.py
⚠️ Только две фабрики: create_ignite, create_fire_breath
НЕТ: create_ember, create_fireball, create_inferno

core/cards/water.py
⚠️ Только две фабрики: create_splash, create_rain_cloud
НЕТ: create_water_splash, create_tidal_wave

core/cards/poison.py
Фабрики: create_poison_stab, create_toxic_cloud, create_acid_shield
⚠️ НЕТ: create_poison_dart

ui/CardRenderer.py ← РЕФАКТОРИНГ (Сессия 4)
draw(surface, card, x, y, font_title, font_desc, is_hovered=False, player=None, enemy=None)
Возвращает rect карты
Рамка — всегда цвет стихии
_resolve_description() — подставляет реальный урон через EffectCalculator(dry_run=True)
_draw_unaffordable_overlay() — 50% затемнение
_get_card_keywords(card) — сканирует effects, возвращает [(key, val)] с реальными числами
draw_card_keyword_tooltip() — Hearthstone-style панель справа от карты
⚠️ Убран KEYWORD_DESCRIPTIONS — читает из StatusRegistry.STATUSES[key]["keyword"]
ui/CombatInterface.py ⚠️ большой ← РЕФАКТОРИНГ (Сессия 4)
⚠️ Убраны STATUS_STYLES + STATUS_TOOLTIPS — читает из StatusRegistry.STATUSES
draw_status_badges(screen, font, creature, x, y) — возвращает [(rect, key, val)], пропускает val≤0
draw_status_tooltip(screen, font, key, val, mouse_pos) — N→str(val), автоприжатие к краям
draw_combat_screen(view) — рисует всё, тултип статуса ПОСЛЕДНИМ
Динамический Intent врага с цветовой индикацией
ui/GameView.py ⚠️ ~160 строк
Хранит hover-состояния для тултипов:

hovered_status_key, hovered_status_val — сбрасываются каждый кадр в update()
enemy_badge_rects, player_badge_rects — тройки (rect, key, val)
hovered_card_index, hovered_card_rect, card_obj — для тултипа карты
ui/InputHandler.py
⚠️ Единственное место логики рестарта:
Блок LEADERBOARD: если handle_clicks() == True →
Shop.reset() + Campfire.reset() + MainMenu.reset() + event_reset() + GameManager()

ui/EventView.py ⚠️ ~233 строки
НЕ класс — модуль функций
init_event(gm) — вызывается из MapView при входе в EVENT
reset() — вызывается при рестарте из InputHandler
from ui.EventView import handle_clicks as event_clicks — правильный импорт
Пул карт: create_ignite, create_fire_breath, create_splash, create_rain_cloud,
create_poison_stab, create_toxic_cloud, create_strike, create_defend, create_heavy_blade, create_iron_wall
ui/MapView.py
handle_click() → gm.enter_chosen_room() → роутинг:
CHEST → Chest.init_chest(view)
EVENT → EventView.init_event(gm)
BOSS → room_type = "COMBAT"
Ориентация: row=X, col=Y, три пути ROW_Y=[300, 540, 780]
ui/HubView.py
reset() — сбрасывает анимацию стопки карт при старте забега
Эмодзи НЕ использовать (pygame SysFont не рендерит)
spread_total ограничен шириной экрана
ui/MainMenu.py
reset() classmethod → cls._hub = None
managers/network_manager.py
send_run_record() — асинхронный threading.Thread(daemon=True)
fetch_top_scores() → leaderboard_cache
Цепочки вызовов
Бой:


MapView.handle_click()

→ gm.enter_chosen_room("COMBAT")

→ gm.spawn_procedural_enemy()

→ CombatManager(player, enemy, deck, gm)

→ for relic in gm.relics: relic.on_combat_start(self)  ← ДО start_turn_phase

→ self.start_turn_phase()
Ход врага:


CombatManager.end_turn_phase()

→ enemy.execute_intent(player, combat_manager)

→ EffectCalculator.calculate_damage(...)

→ player.take_damage(final_dmg, attacker=enemy)
Рестарт:


InputHandler (LEADERBOARD блок)

→ LeaderboardView.handle_clicks() == True

→ Shop.reset(), Campfire.reset(), MainMenu.reset(), event_reset()

→ GameManager() (новый объект)
Добавление карты (везде одинаково):


gm.add_card(card)  ← Shop, Chest, Campfire, EventView
Экономика
Параметр	Значение
Стартовое золото	100
Награда за бой	random.randint(20, 35) + floor × 3
Цена карты в магазине	35 + floor × 3
Цена сжигания	(15 + floor × 2) + removal_count × 25
Костёр	бесплатно (лечение +25 HP или апгрейд)
Персонажи
Класс	HP	Энергия
Warrior	80	3
Rogue	65	3
Mage	55	3
Исправленные баги (49 штук, полная история)
#	Файл	Суть
1	GameView.py	pygame.display.flip() перенесён в конец draw()
2	GameView.py	CHEST и EVENT рендерятся через нативные модули
3	InputHandler.py	блоки CHEST и EVENT добавлены, импорты на уровне модуля
4	Chest.py	CHEST_CARD_POOL переделан на фабричные функции
5	Shop.py / Campfire.py	добавлены методы reset()
6	EventView.py	создан с нуля (7 событий, полный цикл)
7	EventView.py	ImportError — не класс, а модуль функций
8	MapView.py	добавлен вызов EventView.init_event(gm) при входе в EVENT
9	InputHandler.py	добавлен event_reset() при рестарте
10	Chest.py	ложная надпись "уже получено" → "при взятии карты"
11	InputHandler.py	удалён мёртвый legacy MAP-блок
12	EventView.py	gm.player_relics → gm.relics в gain_relic
13	MapView.py	подсказка y=1050 → y=1040
14	Chest.py	gm.current_deck.append() → gm.add_card()
15	MapView.py	BOSS-узел роутится через room_type = "COMBAT"
16	Shop.py	gm.current_deck.append() → gm.add_card()
17	CombatManager.py	реликвии on_combat_start ДО start_turn_phase()
18	CombatManager.py	проверка enemy.hp <= 0 ДО начала нового хода
19	core/enemies/init.py	удалена сломанная фабрика spawn_procedural_enemy
20	cultist.py + slime.py	убран двойной turn_count += 1 из choose_intent()
21	core/Creature.py	убрана двойная уязвимость ×1.5 из take_damage()
22	core/relics/base.py	добавлены хуки on_tick_ignited, on_wet_applied
23	core/relics/elemental.py	реализованы ЭнергоЯдро, ДревнееОгниво, НамокшаяРукавица
24	core/Creature.py	tick_statuses принимает combat_manager=None
25	core/cards/base.py	StatusEffect.execute вызывает on_wet_applied у реликвий
26	CombatManager.py	tick_statuses передают self
27	HubView.py	убраны эмодзи из CLASS_INFO
28	HubView.py	добавлен reset() метод
29	HubView.py	spread_total ограничен шириной экрана
30	MainMenu.py	добавлен reset() classmethod
31	InputHandler.py	MainMenu.reset() в блоке рестарта
32	LeaderboardView.py	handle_clicks() возвращает True/False, без логики рестарта
33	InputHandler.py	единственное место рестарта
34	network_manager.py	send_run_record() асинхронный
35	network_manager.py	_get_username() с try/except fallback
36	GameManager.py	удалён мёртвый импорт spawn_procedural_enemy
37	EventView.py	исправлены 6 несуществующих импортов карт
38	GameManager.py	удалён ручной if ЭнергоЯдро: max_energy += 1 (дублировал хук)
39	CardRenderer.py	§ маркер — только damage числа подсвечиваются золотом
40	CombatInterface.py	STATUS_STYLES + STATUS_TOOLTIPS для 7 статусов, фильтр val≤0
41	CombatInterface.py	draw_status_tooltip() с автоприжатием к краям
42	GameView.py	hovered_status_key/val + badge_rects как тройки (rect, key, val)
43	CardRenderer.py	_get_card_keywords() возвращает (key, val) с реальными числами
44	CardRenderer.py	draw_card_keyword_tooltip() Hearthstone-style панель
45	CombatInterface.py	draw_status_tooltip принимает val, N→реальное число
46	core/StatusRegistry.py	СОЗДАН — единый реестр 7 статусов
47	CombatInterface.py	убраны STATUS_STYLES/STATUS_TOOLTIPS, читает из реестра
48	CardRenderer.py	убран KEYWORD_DESCRIPTIONS, читает из реестра
49	core/Creature.py	self.statuses={}, getattr/setattr, обратная совместимость
Грабли (не повторять)
view.view.gm — двойной view это баг
Эмодзи в pygame SysFont — не рендерятся, никогда не использовать
EventView — НЕ класс, импортировать функции напрямую
self.relics (не self.player_relics!) в GameManager
tick_statuses(combat_manager=None) — всегда передавать self из CombatManager
spawn_procedural_enemy — МЕТОД GameManager, не импортировать из core.enemies
LeaderboardView.handle_clicks() — только возвращает True/False, рестарт в InputHandler
pygame.display.flip() — один раз в конце draw(), не внутри методов
Отступы Python при копировании из чата — всегда проверять структуру
Реликвии управляют своими эффектами САМИ через хуки — GameManager не дублирует
fire.py — только create_ignite, create_fire_breath. Нет ember/fireball/inferno
water.py — только create_splash, create_rain_cloud. Нет water_splash/tidal_wave
poison.py — create_poison_stab, не create_poison_dart
StatusRegistry должен быть импортирован ДО Creature (нет зависимостей, порядок ок)
__setattr__ в Creature: _STATUS_KEYS вычисляется при загрузке модуля через all_keys()
Файлы без сюрпризов (читать напрямую, влезают в контекст)
Все файлы кроме: GameManager.py, CombatInterface.py, GameView.py, EventView.py

