# _project_map.md
# Читать ПЕРВЫМ в каждой сессии. Актуально на Jun 2, 2026 — Сессия 12.

## Архитектура
- core/ — вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py)
- ui/ — вся отрисовка (CardRenderer.py, CombatInterface.py, GameView.py, HubView.py, MainMenu.py и др.)
- managers/ — CombatManager, DeckManager, GameManager, MapGenerator, network_manager
- Разрешение: строго 1920x1080 Full HD
- **Ветка разработки: dev** (main — стабильная, dev — активная работа)

## Железные ГОСТы
- Лимит файла: 150 строк (золотой стандарт)
- Если файл разрастается — рефакторинг и разбивка на модули
- Модульность и логичные зависимости — главный принцип
- Никаких "божественных объектов"

## Навигация
- Все файлы читать из ветки dev:
  https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу
- Большие файлы (GameManager.py, CombatInterface.py, GameView.py) — использовать query_context
- Остальные файлы читаются за один запрос напрямую

## Полный список файлов
main.py, server.py, _project_map.md
core/rarity.py
core/Creature.py
core/EffectCalculator.py
core/StatusRegistry.py
core/cards/__init__.py, base.py, basic.py, fire.py, poison.py, water.py
core/cards/buff/__init__.py, strength.py, thorns.py
core/cards/debuff/__init__.py, vulnerable.py, weak.py
core/enemies/__init__.py, base.py, cultist.py, slime.py, boss.py
core/players/__init__.py, base.py, mage.py, rogue.py, warrior.py
core/relics/__init__.py, base.py, starter.py, elemental.py
managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py, MapGenerator.py, network_manager.py
ui/chest/__init__.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py
ui/combat/__init__.py, hud.py
ui/events/__init__.py, event_data.py, event_effects.py, positive.py, negative.py, neutral.py, special.py
ui/Campfire.py, CardRenderer.py, CombatInterface.py
ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py
ui/VictoryScreen.py

## Ключевые системы

**Creature.py** — базовый класс. self.statuses={} через __getattr__/__setattr__. add_status(key, amount, combat_manager=None) — хук on_wet_applied внутри.

**StatusRegistry.py** — единый реестр 7 статусов. Добавить статус = одна запись здесь.

**EffectCalculator.py** — единая точка боевой математики (реликвии → ярость → слабость → уязвимость → комбо пар). dry_run=True для превью. При dry_run=False обновляет gm.stats["max_damage_dealt"].

**Реликвии** — хуки: on_combat_start, on_turn_start, on_damage_calculated, on_tick_ignited, on_wet_applied, on_card_played (заглушка), on_shield_gained (заглушка), on_kill (заглушка). Реликвии управляют своими эффектами САМИ.

**Лидерборд** — Google Apps Script, асинхронный фоновый поток (threading.Thread daemon=True).

**Персонажи:** Warrior (HP80), Rogue (HP65), Mage (HP55)

**Враги (тестовый режим):**
- hp = 20 + floor×3 + tier×10
- dmg = 3 + tier×1
- shld = 2
- Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

## Экран победы (VictoryScreen) — Сессия 12
- ui/VictoryScreen.py — статический класс
- distribute_combat_rewards() собирает pending_rewards (list of dict: type/label/value/applied), переключает state → "VICTORY". Награды не применяются сразу.
- Каждая награда: кнопка "Получить" / "Получено"
- "Получить все" — забирает все незабранные
- "Продолжить" — если есть незабранные, открывает модалку подтверждения (SRCALPHA затемнение + "Пропустить награду?" + Да/Нет)
- GameView: +_draw_victory, +DRAW_HANDLERS["VICTORY"]
- InputHandler: +_handle_victory, +STATE_HANDLERS["VICTORY"]; _handle_combat больше не вызывает setup_next_floor

## Сброс состояния игрока после боя — Сессия 12
В начале distribute_combat_rewards():
- player.energy = player.max_energy
- player.shield = 0
- weak / vulnerable / wet / ignited → 0
- strength, thorns НЕ сбрасываются (перманентные баффы)

## Реализованные системы
- Все 14 пунктов плана масштабируемости (A-N) ✅
- Система сундуков: common / locked / cursed (ui/chest/)
- Система ивентов: positive / negative / neutral / special (ui/events/)
- UI реликвий в бою с тултипами (ui/combat/hud.py)
- Хук on_wet_applied в Creature.add_status
- Экран победы с наградами и модалкой (ui/VictoryScreen.py)

## Аудит реликвий (все работают)
- LuckyClover: on_combat_start → draw_cards(2) ✅
- SpikedBracelet: on_combat_start → gain_shield(10) ✅
- ТочильныйКамень: on_damage_calculated → +2 урона ✅
- ЭнергоЯдро: on_combat_start → max_energy+1, флаг _applied ✅
- ДревнееОгниво: on_tick_ignited → +2 к горению ✅
- НамокшаяРукавица: on_wet_applied → +4 щита ✅

## Известные нерешённые проблемы
- Щит врага сбрасывается каждый ход (намеренно)
- Хуки on_card_played, on_shield_gained, on_kill — заглушки, не подключены

## План следующей сессии (Сессия 13)

**Приоритет 1 — хуки:**
1. on_card_played → CombatManager.play_card_by_index
2. on_shield_gained → Creature.gain_shield
3. on_kill → CombatManager.end_turn_phase
4. Первые реликвии на этих хуках (UNCOMMON/RARE)

**Приоритет 2 — контент:**
- Новые карты UNCOMMON/RARE/EPIC для каждого класса
- Реликвии EPIC/LEGENDARY
- Экран выбора реликвии с рамкой по редкости
- Запустить BalanceSimulator, проверить win rate

## Важные грабли
- Отступы Python сбиваются при копировании из чата — всегда проверять
- view.view.gm — двойной view это баг
- Pygame не поддерживает эмодзи в SysFont
- pygame.display.flip() — один раз в конце draw()
- EventView.py — НЕ класс, только функции
- self.relics (не self.player_relics!) в GameManager
- tick_statuses принимает combat_manager=None — всегда передавать self из CombatManager
- spawn_procedural_enemy — МЕТОД GameManager, не импортировать из core.enemies
- Все файлы читать из ветки DEV, не main
- CombatManager.__init__ сигнатура: (player, enemy, starting_deck, game_manager=None)
- RARITY_COLORS импортировать из core.rarity
- on_wet_applied — через Creature.add_status, НЕ напрямую
- bonus_draw — getattr с дефолтом 0
- ui/chest/ — маленькая c: from ui.chest import Chest
- distribute_combat_rewards() → pending_rewards → VICTORY; _handle_combat не вызывает setup_next_floor
- VictoryScreen._show_modal — классовая переменная, сбрасывается в _proceed()
- CardRenderer.draw(player=None) — карта всегда доступна (can_afford=True)

## Исправленные баги (последние)
[53] ui/Chest.py → ui/chest/ — регистр импорта
[54] max_damage_dealt всегда 0 — исправлено в EffectCalculator.calculate_damage()
[55] Карты в сундуке затемнялись — player.energy=0 после боя; player=None в draw_card_row + сброс в distribute_combat_rewards