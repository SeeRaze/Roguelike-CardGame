# _project_map.md — Roguelike Card Game
# Читать ПЕРВЫМ в каждой сессии. Актуально: Jun 2, 2026 (Сессия 10)

## СТРУКТУРА ПРОЕКТА

main.py, server.py

core/rarity.py              — Rarity enum + RARITY_COLORS dict
core/Creature.py            — базовый класс; add_status(key, amount, combat_manager=None); хук on_wet_applied внутри
core/EffectCalculator.py    — вся боевая математика; dry_run=True
core/StatusRegistry.py      — реестр 7 статусов (vulnerable, weak, wet, ignited, poison, strength, thorns)

core/cards/__init__.py
core/cards/base.py          — Card, StatusEffect (использует enemy.add_status с combat_manager)
core/cards/basic.py, fire.py, poison.py, water.py
core/cards/buff/__init__.py, buff/strength.py, buff/thorns.py
core/cards/debuff/__init__.py, debuff/vulnerable.py, debuff/weak.py

core/enemies/__init__.py, base.py, cultist.py, slime.py, boss.py
core/players/__init__.py, base.py, mage.py, rogue.py, warrior.py
core/relics/__init__.py     — RELIC_POOL по редкостям
core/relics/base.py         — Relic + rarity + 8 хуков
core/relics/starter.py, elemental.py

managers/BalanceSimulator.py
managers/CombatManager.py   — draw_cards(5 + bonus_draw); бой стартует в __init__
managers/DeckManager.py
managers/GameManager.py     — player_keys=0; босс роняет ключ в distribute_combat_rewards
managers/MapGenerator.py
managers/network_manager.py

ui/Campfire.py
ui/CardRenderer.py
ui/Chest.py                 — 354 строки; 3 типа сундуков (common/locked/cursed); ⚠️ запланирован рефакторинг → ui/chest/
ui/CombatInterface.py       — draw_relics через CombatHUD; draw_relic_tooltip последним
ui/combat/__init__.py
ui/combat/hud.py            — draw_relics() + draw_relic_tooltip()
ui/EventView.py             — НЕ содержит класс, только функции
ui/events/__init__.py, events/event_data.py, events/event_effects.py
ui/GameView.py              — HoverState + relic_obj поле + relic_rects в update()
ui/HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py

---

## КЛЮЧЕВЫЕ СИСТЕМЫ

### Сундуки (ui/Chest.py)
- Типы: common (2 карты), locked (4 карты + 30-60 золота, требует ключ), cursed (баффы за HP)
- Веса: 33 / 33 / 34
- player_keys хранится в GameManager; босс роняет +1 ключ в distribute_combat_rewards
- CURSED_BUFF_POOL: +3 Ярости (15HP), +5 Шипов (12HP), +1 Энергия (20HP),
  +15 Щита (10HP), +25 Золота (8HP), +1 Карта/ход (18HP)
- bonus_draw на игроке: getattr(player, 'bonus_draw', 0) — CombatManager учитывает

### Реликвии (все 6 работают)
- LuckyClover: on_combat_start → draw_cards(2)
- SpikedBracelet: on_combat_start → gain_shield(10)
- ТочильныйКамень: on_damage_calculated → +2 урона
- ЭнергоЯдро: on_combat_start → max_energy+1, флаг _applied
- ДревнееОгниво: on_tick_ignited → +2 к горению
- НамокшаяРукавица: on_wet_applied → +4 щита (хук в Creature.add_status)
- Хуки-заглушки (не подключены): on_card_played, on_shield_gained, on_kill

### Формулы врагов
⚠️ ТЕСТОВЫЙ РЕЖИМ: hp = 20 + floor×3 + tier×10, dmg = 3 + tier×1, shld = 2
Боевые (продакшн): hp = 40 + floor×8 + tier×25, dmg = 5 + floor×1 + tier×4, shld = 3 + floor×1
Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

### Персонажи
Warrior (HP80), Rogue (HP65), Mage (HP55)

---

## ПЛАН СЕССИИ 11

### Приоритет 1 — рефакторинг ui/Chest.py (354 строки → ui/chest/)
ui/chest/__init__.py   — реэкспорт Chest (обратная совместимость)
ui/chest/base.py       — init_chest, draw_screen, handle_clicks + константы
ui/chest/common.py     — _draw_common, _clicks_common
ui/chest/locked.py     — _draw_locked, _clicks_locked
ui/chest/cursed.py     — _draw_cursed, _clicks_cursed + CURSED_BUFF_POOL
ui/chest/shared.py     — _draw_card_row, кнопки (take/skip/leave/continue)
ui/chest/data.py       — CHEST_CARD_POOL, pick_chest_type, generate_*

### Приоритет 2 — хуки в CombatManager
1. on_card_played → play_card_by_index
2. on_shield_gained → Creature.gain_shield (аналогично on_wet_applied)
3. on_kill → end_turn_phase
4. Первые реликвии на этих хуках (UNCOMMON/RARE)

### Приоритет 3 — контент
- Новые карты UNCOMMON/RARE/EPIC для каждого класса
- Реликвии EPIC/LEGENDARY
- Экран выбора реликвии с рамкой по редкости
- Запустить BalanceSimulator, проверить win rate

---

## ВАЖНЫЕ ГРАБЛИ

- Отступы Python сбиваются при копировании из чата — всегда проверять
- view.view.gm — двойной view это баг
- Pygame не поддерживает эмодзи в SysFont
- pygame.display.flip() — один раз в конце draw()
- EventView.py — НЕ класс, только функции
- self.relics (не self.player_relics!) в GameManager
- tick_statuses принимает combat_manager=None — всегда передавать self из CombatManager
- spawn_procedural_enemy — МЕТОД GameManager, не импортировать из core.enemies
- LeaderboardView.handle_clicks() — только возвращает True/False
- Реликвии управляют своими эффектами САМИ через хуки
- fire.py: create_ignite, create_fire_breath (только эти две)
- water.py: create_splash, create_rain_cloud (только эти две)
- poison.py: create_poison_stab (НЕ create_poison_dart)
- Все файлы читать из ветки DEV
- CombatManager.__init__ сигнатура: (player, enemy, starting_deck, game_manager=None)
- RARITY_COLORS импортировать из core.rarity (не из core.relics)
- on_wet_applied — через Creature.add_status, НЕ напрямую из StatusEffect
- bonus_draw — getattr с дефолтом 0, не хранится в Creature напрямую