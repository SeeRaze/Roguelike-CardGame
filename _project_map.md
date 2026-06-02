# _project_map.md — навигатор проекта
# Читать ПЕРВЫМ в каждой сессии
# Последнее обновление: Jun 2, 2026 — Сессия 7

## РЕПОЗИТОРИЙ
GitHub: https://github.com/SeeRaze/Roguelike-CardGame
Ветка разработки: dev
Читать файлы: https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу

## ТЕХНИЧЕСКИЕ КОНСТАНТЫ
- Разрешение: 1920x1080 Full HD
- Лимит файла: 150 строк (золотой стандарт)
- Python + Pygame

## ПОЛНЫЙ СПИСОК ФАЙЛОВ (актуально на Jun 2, 2026 — Сессия 7)

main.py, server.py, _project_map.md

core/rarity.py                          — Rarity enum: COMMON, UNCOMMON, RARE, EPIC, LEGENDARY
core/Creature.py                        — базовый класс (hp, shield, self.statuses={}, __getattr__/__setattr__)
core/EffectCalculator.py                — единая точка боевой математики (dry_run=True)
core/StatusRegistry.py                  — единый реестр 7 статусов

core/cards/__init__.py
core/cards/base.py                      — Card + rarity поле; StatusEffect читает из StatusRegistry
core/cards/basic.py
core/cards/fire.py                      — create_ignite, create_fire_breath
core/cards/poison.py                    — create_poison_stab
core/cards/water.py                     — create_splash, create_rain_cloud
core/cards/buff/__init__.py
core/cards/buff/strength.py
core/cards/buff/thorns.py
core/cards/debuff/__init__.py
core/cards/debuff/vulnerable.py
core/cards/debuff/weak.py

core/enemies/__init__.py
core/enemies/base.py                    — Enemy + Intent-объекты (IntentAttack/Defend/Debuff/None) + сеттеры совместимости
core/enemies/cultist.py
core/enemies/slime.py
core/enemies/boss.py                    — BossTitan (убран дублирующий turn_count += 1)

core/players/__init__.py
core/players/base.py                    — Player + _extra_starter_cards + add_to_starter_deck()
core/players/mage.py
core/players/rogue.py
core/players/warrior.py

core/relics/__init__.py                 — RELIC_POOL по редкостям + ALL_RELICS
core/relics/base.py                     — Relic + rarity поле + 8 хуков (5 активных + 3 заглушки)
core/relics/starter.py
core/relics/elemental.py

managers/BalanceSimulator.py            — перепись под текущую архитектуру (Warrior/Rogue/Mage)
managers/CombatManager.py
managers/DeckManager.py
managers/GameManager.py                 — ENEMY_REGISTRY dict; distribute_combat_rewards с роллом редкости
managers/MapGenerator.py               — ROW_OVERRIDES конфиг; MapNode, generate_map()
managers/network_manager.py

ui/Campfire.py
ui/CardRenderer.py
ui/Chest.py
ui/CombatInterface.py                   — оркестратор; читает view.hover.* (HoverState)
ui/EventView.py
ui/GameView.py                          — HoverState dataclass + DRAW_HANDLERS диспетчер
ui/HubView.py
ui/InputHandler.py                      — STATE_HANDLERS диспетчер
ui/LeaderboardView.py
ui/MainMenu.py
ui/MapView.py
ui/Shop.py
ui/combat/__init__.py
ui/combat/hud.py                        — CombatHUD: draw_hp_bar, draw_status_badges, draw_status_tooltip
ui/events/__init__.py
ui/events/event_data.py
ui/events/event_effects.py

## КЛЮЧЕВЫЕ СИСТЕМЫ

### Creature.py
- self.statuses={} через __getattr__/__setattr__
- _STATUS_KEYS вычисляется при загрузке через STATUSES.all_keys()
- tick_statuses принимает combat_manager=None — всегда передавать self из CombatManager

### StatusRegistry.py
- Единый реестр 7 статусов (abbr, badge_bg, badge_fg, tooltip, keyword, is_duration, is_stack)
- Добавить статус = одна запись здесь

### EffectCalculator.py
- Единая точка боевой математики: реликвии → ярость → слабость → уязвимость → комбо пар
- Поддерживает dry_run=True

### Rarity (core/rarity.py)
- COMMON, UNCOMMON, RARE, EPIC, LEGENDARY
- Card.rarity = Rarity.COMMON по умолчанию
- Relic.rarity = Rarity.COMMON по умолчанию

### RELIC_POOL (core/relics/__init__.py)
- {Rarity.COMMON: [LuckyClover, SpikedBracelet, ТочильныйКамень],
   Rarity.UNCOMMON: [ДревнееОгниво, НамокшаяРукавица],
   Rarity.RARE: [ЭнергоЯдро], EPIC: [], LEGENDARY: []}
- Ролл редкости: 60% COMMON, 30% UNCOMMON, 10% RARE

### ENEMY_REGISTRY (managers/GameManager.py)
- {"Культист": Cultist, "Страж": Cultist,
   "Слизень": SlimeAndGoblins, "Гоблин": SlimeAndGoblins, "Орк": SlimeAndGoblins}
- BossTitan отдельно (local_step == 20)

### Intent-объекты (core/enemies/base.py)
- IntentAttack, IntentDefend, IntentDebuff, IntentNone
- Обратная совместимость: .intent_type и .intent_value работают как раньше через @property + setter
- Предпочтительный способ: enemy.set_intent("attack", 10)

### HoverState (ui/GameView.py)
- Все hover-данные в self.hover (card_index, card_rect, card_obj, status_key, status_val, end_turn, map_col)
- Сбрасывается в update() каждый кадр
- CombatInterface читает view.hover.* (не плоские атрибуты)

### Реликвии — хуки
- on_combat_start, on_turn_start, on_damage_calculated, on_tick_ignited, on_wet_applied — активные
- on_card_played, on_shield_gained, on_kill — заглушки для будущих реликвий
- Реликвии управляют своими эффектами САМИ через хуки

### Player (core/players/base.py)
- _extra_starter_cards: list — карты добавленные реликвиями/событиями
- add_to_starter_deck(card) — добавить карту в стартовую деку
- get_starter_deck() — фабрика + extra карты

## ФОРМУЛЫ ВРАГОВ (тестовый режим, Jun 2 сессия)
hp  = 20 + floor×3 + tier×10
dmg = 3 + tier×1
shld = 2
Босс (local_step==20): hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

## ПЕРСОНАЖИ
- Warrior: HP80, energy 3, gold 100
- Rogue:   HP65, energy 3, gold 120
- Mage:    HP55, energy 3, gold 90

## ИЗВЕСТНЫЕ НЕРЕШЁННЫЕ ПРОБЛЕМЫ
- Ключи как предмет для закрытых сундуков (отложено)
- Щит врага сбрасывается каждый ход (намеренно)

## ВАЖНЫЕ ГРАБЛИ
- При копировании кода из чата легко сбиваются отступы Python — всегда проверять
- view.view.gm — двойной view это баг
- Pygame не поддерживает эмодзи в SysFont
- pygame.display.flip() должен быть в конце draw() один раз
- EventView.py НЕ содержит класс — только функции
- self.relics (не self.player_relics!) в GameManager
- tick_statuses принимает combat_manager=None — всегда передавать self из CombatManager
- spawn_procedural_enemy — МЕТОД GameManager, НЕ импортировать из core.enemies
- LeaderboardView.handle_clicks() — только возвращает True/False
- __setattr__ в Creature: _STATUS_KEYS вычисляется при загрузке модуля через all_keys()
- Все файлы читать из ветки DEV, не main
- BotCombatManager: бой стартует в __init__, вызывать run_bot_loop() после создания объекта
- CombatManager.__init__ сигнатура: (player, enemy, starting_deck, game_manager=None)

## ИСПРАВЛЕННЫЕ БАГИ (полная история, 52 штука)
[1-51 — см. предыдущие сессии]
52. core/enemies/boss.py — убран дублирующий turn_count += 1 (двойной инкремент счётчика)

## ПЛАН СЛЕДУЮЩЕЙ СЕССИИ (Сессия 8)
Все 14 пунктов A-N из плана масштабируемости ВЫПОЛНЕНЫ.

Возможные направления:
1. Новый контент: карты UNCOMMON/RARE/EPIC, реликвии EPIC/LEGENDARY
2. Хуки on_card_played, on_shield_gained, on_kill — реализовать первые реликвии на них
3. Запустить BalanceSimulator, проверить win rate по классам, скорректировать баланс
4. UI: экран выбора реликвии с отображением редкости (цвет рамки по Rarity)
5. Новые типы врагов или боссов

## СТАТУС
Сессия 7 завершена (Jun 2, 2026).
Реализованы все 14 пунктов плана масштабируемости (A-N).
Проект полностью переведён на диспетчеры, объекты намерений, систему редкостей и HoverState.