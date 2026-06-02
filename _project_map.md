# _project_map.md — навигатор проекта
# Читать ПЕРВЫМ в каждой сессии
# Последнее обновление: Jun 2, 2026 — Сессия 9

## РЕПОЗИТОРИЙ
GitHub: https://github.com/SeeRaze/Roguelike-CardGame
Ветка разработки: dev
Читать файлы: https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу

## ТЕХНИЧЕСКИЕ КОНСТАНТЫ
- Разрешение: 1920x1080 Full HD
- Лимит файла: 150 строк (золотой стандарт)
- Python + Pygame

## ПОЛНЫЙ СПИСОК ФАЙЛОВ (актуально на Jun 2, 2026 — Сессия 9)

main.py, server.py, _project_map.md

core/rarity.py                          — Rarity enum + RARITY_COLORS dict
core/Creature.py                        — add_status(key, amount, combat_manager=None)
                                          хук on_wet_applied срабатывает внутри
core/EffectCalculator.py                — единая точка боевой математики (dry_run=True)
core/StatusRegistry.py                  — единый реестр 7 статусов

core/cards/__init__.py
core/cards/base.py                      — StatusEffect использует enemy.add_status(type, turns, cm)
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
core/enemies/base.py                    — Enemy + Intent-объекты + сеттеры совместимости
core/enemies/cultist.py
core/enemies/slime.py
core/enemies/boss.py

core/players/__init__.py
core/players/base.py                    — Player + _extra_starter_cards + add_to_starter_deck()
core/players/mage.py
core/players/rogue.py
core/players/warrior.py

core/relics/__init__.py                 — RELIC_POOL по редкостям + ALL_RELICS
core/relics/base.py                     — Relic + rarity + 8 хуков (5 активных + 3 заглушки)
core/relics/starter.py
core/relics/elemental.py

managers/BalanceSimulator.py
managers/CombatManager.py
managers/DeckManager.py
managers/GameManager.py                 — ENEMY_REGISTRY dict; distribute_combat_rewards
managers/MapGenerator.py               — ROW_OVERRIDES конфиг; MapNode, generate_map()
managers/network_manager.py

ui/Campfire.py
ui/CardRenderer.py
ui/Chest.py
ui/CombatInterface.py                   — draw_relics через CombatHUD; draw_relic_tooltip последним
ui/EventView.py
ui/GameView.py                          — HoverState (+ relic_obj) + DRAW_HANDLERS + relic_rects
ui/HubView.py
ui/InputHandler.py                      — STATE_HANDLERS диспетчер
ui/LeaderboardView.py
ui/MainMenu.py
ui/MapView.py
ui/Shop.py
ui/combat/__init__.py
ui/combat/hud.py                        — draw_hp_bar, draw_status_badges, draw_status_tooltip,
                                          draw_relics, draw_relic_tooltip

ui/events/__init__.py
ui/events/event_data.py
ui/events/event_effects.py

## КЛЮЧЕВЫЕ СИСТЕМЫ

### Creature.py
- self.statuses={} через __getattr__/__setattr__
- _STATUS_KEYS вычисляется при загрузке через STATUSES.all_keys()
- tick_statuses принимает combat_manager=None — всегда передавать self из CombatManager
- add_status(key, amount, combat_manager=None) — хук on_wet_applied внутри при key=="wet"

### StatusRegistry.py
- Единый реестр 7 статусов (abbr, badge_bg, badge_fg, tooltip, keyword, is_duration, is_stack)
- Добавить статус = одна запись здесь

### EffectCalculator.py
- Единая точка боевой математики: реликвии → ярость → слабость → уязвимость → комбо пар
- Поддерживает dry_run=True

### Rarity (core/rarity.py)
- COMMON, UNCOMMON, RARE, EPIC, LEGENDARY
- RARITY_COLORS: {Rarity → (R, G, B)} — импортировать из core.rarity

### RELIC_POOL (core/relics/__init__.py)
- {Rarity.COMMON: [LuckyClover, SpikedBracelet, ТочильныйКамень],
   Rarity.UNCOMMON: [ДревнееОгниво, НамокшаяРукавица],
   Rarity.RARE: [ЭнергоЯдро], EPIC: [], LEGENDARY: []}
- Ролл редкости: 60% COMMON, 30% UNCOMMON, 10% RARE

### Хуки реликвий (core/relics/base.py)
- on_combat_start, on_turn_start, on_damage_calculated, on_tick_ignited — активные
- on_wet_applied — активный, вызывается через Creature.add_status (НЕ из StatusEffect напрямую)
- on_card_played, on_shield_gained, on_kill — ЗАГЛУШКИ (не подключены в CombatManager)

### Аудит реликвий (все работают ✅)
- LuckyClover: on_combat_start → draw_cards(2)
- SpikedBracelet: on_combat_start → gain_shield(10)
- ТочильныйКамень: on_damage_calculated → +2 урона
- ЭнергоЯдро: on_combat_start → max_energy+1, флаг _applied защищает от повтора
- ДревнееОгниво: on_tick_ignited → +2 к тику горения
- НамокшаяРукавица: on_wet_applied → +4 щита

### UI реликвий в бою (ui/combat/hud.py)
- draw_relics(screen, font, relics, x, y) → [(rect, relic)]
- draw_relic_tooltip(screen, font, relic, mouse_pos)
- HoverState.relic_obj — реликвия под курсором, сбрасывается каждый кадр

### ENEMY_REGISTRY (managers/GameManager.py)
- {"Культист": Cultist, "Страж": Cultist,
   "Слизень": SlimeAndGoblins, "Гоблин": SlimeAndGoblins, "Орк": SlimeAndGoblins}
- BossTitan отдельно (local_step == 20)

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
- Хуки on_card_played, on_shield_gained, on_kill — заглушки, не подключены в CombatManager

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
- Реликвии управляют своими эффектами САМИ через хуки
- on_wet_applied вызывается через Creature.add_status, НЕ напрямую из StatusEffect
- __setattr__ в Creature: _STATUS_KEYS вычисляется при загрузке модуля через all_keys()
- Все файлы читать из ветки DEV, не main
- BotCombatManager: бой стартует в __init__, вызывать run_bot_loop() после создания объекта
- CombatManager.__init__ сигнатура: (player, enemy, starting_deck, game_manager=None)
- RARITY_COLORS импортировать из core.rarity (не из core.relics)

## ИСПРАВЛЕННЫЕ БАГИ (полная история, 52 штука)
[1-52 — см. предыдущие сессии]

## ПЛАН СЛЕДУЮЩЕЙ СЕССИИ (Сессия 10)

Приоритет — подключить хуки-заглушки:
1. on_card_played — подключить в CombatManager.play_card_by_index
2. on_shield_gained — подключить в Creature.gain_shield (аналогично on_wet_applied)
3. on_kill — подключить в CombatManager.end_turn_phase
4. Написать первые реликвии на этих хуках (UNCOMMON/RARE)

Дополнительно:
- Карты UNCOMMON/RARE/EPIC для каждого класса
- Реликвии EPIC/LEGENDARY
- Экран выбора реликвии с рамкой по RARITY_COLORS
- Запустить BalanceSimulator, проверить win rate по классам

## СТАТУС
Сессия 9 завершена (Jun 2, 2026).
Аудит реликвий: все 6 работают корректно.
on_wet_applied перенесён в Creature.add_status — теперь универсальный.
Следующая стадия: подключение хуков on_card_played / on_shield_gained / on_kill.