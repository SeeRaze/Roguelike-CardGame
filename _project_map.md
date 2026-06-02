# _project_map.md
# Читать ПЕРВЫМ в каждой сессии. Актуально на Jun 3, 2026 — Сессия 14.

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
core/cards/__init__.py, base.py, basic.py, fire.py, poison.py, water.py, heal.py
core/cards/buff/__init__.py, strength.py, thorns.py, regen.py, vampirism.py
core/cards/debuff/__init__.py, vulnerable.py, weak.py, bleed.py
core/enemies/__init__.py, base.py, cultist.py, slime.py, boss.py
core/players/__init__.py, base.py, mage.py, rogue.py, warrior.py
core/relics/__init__.py, base.py, starter.py, elemental.py
managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py, MapGenerator.py, network_manager.py
ui/chest/__init__.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py
ui/combat/__init__.py, hud.py
ui/events/__init__.py, event_data.py, event_effects.py, positive.py, negative.py, neutral.py, special.py
ui/Campfire.py, CardRenderer.py, CombatInterface.py
ui/CardLibraryView.py
ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py
ui/VictoryScreen.py

## Ключевые системы

**Creature.py** — базовый класс. self.statuses={} через __getattr__/__setattr__.
- add_status(key, amount, combat_manager=None) — хук on_wet_applied внутри
- take_damage(amount, attacker=None, combat_manager=None) — combat_manager нужен для триггера bleed и лога
- heal(amount) — с ограничением по max_hp, возвращает фактически восстановленное

**StatusRegistry.py** — единый реестр 9 статусов:
vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed
Добавить статус = одна запись здесь.

**EffectCalculator.py** — единая точка боевой математики (реликвии → ярость → слабость → уязвимость → комбо пар). dry_run=True для превью. При dry_run=False обновляет gm.stats["max_damage_dealt"].

**base.py (cards)** — все эффекты:
- DamageEffect — урон, передаёт combat_manager в take_damage
- VampireDamageEffect — урон + хил 50% от фактического (max(1, dmg//2)), синергия с Яростью автоматическая
- ShieldEffect, HealEffect, RegenEffect, StatusEffect, PoisonEffect
- BleedEffect — в core/cards/debuff/bleed.py

**Реликвии** — хуки: on_combat_start, on_turn_start, on_damage_calculated, on_tick_ignited, on_wet_applied, on_card_played (заглушка), on_shield_gained (заглушка), on_kill (заглушка). Реликвии управляют своими эффектами САМИ.

**Лидерборд** — Google Apps Script, асинхронный фоновый поток (threading.Thread daemon=True).

**Персонажи:** Warrior (HP80), Rogue (HP65), Mage (HP55)

**Враги (тестовый режим):**
- hp = 20 + floor×3 + tier×10
- dmg = 3 + tier×1
- shld = 2
- Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

## Механики (Сессия 14)

**Heal** — HealEffect в base.py, карты в core/cards/heal.py

**Regen** — RegenEffect в base.py, статус в StatusRegistry.
Тик в Creature.tick_statuses: хилит N HP, затем убывает на 1.
Карты в core/cards/buff/regen.py.

**Exile** — свойство exile=False на Card.
Логика в CombatManager.play_card_by_index: exile=True → deck_manager.exile_pile.
DeckManager.reset_deck() возвращает exile_pile в pool перед новым боем.

**Bleed (кровотечение)** — BleedEffect в core/cards/debuff/bleed.py.
Статус в StatusRegistry (is_stack=True).
Триггер в Creature.take_damage: при каждом ударе (amount > 0) → +bleed урона сквозь щит.
В конце хода: s['bleed'] = 0 (полный сброс, не убывание на 1).
Карты: Порез COMMON, Кровопускание UNCOMMON, Открытая Рана RARE+exile.

**Vampirism (вампиризм)** — VampireDamageEffect в base.py.
Бьёт через EffectCalculator (учитывает Ярость/Слабость/Уязвимость/реликвии).
Хил = max(1, final_dmg // 2). Синергия с Яростью автоматическая.
Карты в core/cards/buff/vampirism.py: Высасывание UNCOMMON, Кровавый Пир RARE+exile, Жизнеотвод COMMON.

## Библиотека карт (Сессия 13)
- ui/CardLibraryView.py — статический класс CardLibraryView
- Кнопка "КАРТЫ" в MainMenu.py между "ВОЙТИ В ЛАГЕРЬ" и "ВЫХОД"
- State "CARD_LIBRARY" в DRAW_HANDLERS (GameView) и STATE_HANDLERS (InputHandler)
- 4 вкладки: Все / Воин / Разбойник / Маг
- COLS=8, CARD_W=180, CARD_H=250, START_X=60, START_Y=200
- Шапка (Назад + вкладки) y=18-64, разделитель y=80, надпись y=90 x=760
- Скролл колесом, клиппинг под шапку (y=90), тултипы при наведении
- Карты по вкладкам:
  - Воин: strike, defend, heavy_blade, iron_wall, bash, flex, battle_cry, thorn_armor
  - Разбойник: strike, defend, neutralize, intimidate, poison_stab, toxic_cloud, acid_shield
  - Маг: strike, defend, ignite, fire_breath, splash, rain_cloud
  - Все: дедупликация по __name__ фабрики
  - ⚠️ Новые карты (bleed, regen, vampirism) в библиотеку ещё не добавлены

## Экран победы (VictoryScreen) — Сессия 12
- distribute_combat_rewards() → pending_rewards → state "VICTORY"
- Кнопки "Получить" / "Получить все" / "Продолжить" + модалка подтверждения

## Сброс состояния игрока после боя — Сессия 12
В distribute_combat_rewards(): energy=max_energy, shield=0, weak/vulnerable/wet/ignited=0.
strength, thorns НЕ сбрасываются.

## Реализованные системы
- Все 14 пунктов плана масштабируемости (A-N) ✅
- Система сундуков: common / locked / cursed (ui/chest/) ✅
- Система ивентов: positive / negative / neutral / special (ui/events/) ✅
- UI реликвий в бою с тултипами (ui/combat/hud.py) ✅
- Хук on_wet_applied в Creature.add_status ✅
- Экран победы с наградами и модалкой (ui/VictoryScreen.py) ✅
- Библиотека карт (ui/CardLibraryView.py) ✅
- Heal / Regen / Exile / Bleed / Vampirism ✅

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
- Новые карты (bleed, regen, vampirism) не добавлены в CardLibraryView

## План следующей сессии (Сессия 15)

**Приоритет 1 — хуки:**
1. on_card_played → CombatManager.play_card_by_index
2. on_shield_gained → Creature.gain_shield
3. on_kill → CombatManager.end_turn_phase
4. Первые реликвии на этих хуках (UNCOMMON/RARE)

**Приоритет 2 — контент:**
- Новые карты UNCOMMON/RARE/EPIC для каждого класса
- Реликвии EPIC/LEGENDARY
- Экран выбора реликвии с рамкой по редкости
- Добавить bleed/regen/vampirism карты в CardLibraryView
- Запустить BalanceSimulator, проверить win rate

## Важные грабли
- Отступы Python сбиваются при копировании из чата — всегда проверять
- view.view.gm — двойной view это баг
- Pygame не поддерживает эмодзи в SysFont
- pygame.display.flip() — один раз в конце GameView.draw(), НЕ в draw_screen дочерних экранов
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
- CardLibraryView: from ui.CardLibraryView import CardLibraryView
- Creature.take_damage сигнатура: (amount, attacker=None, combat_manager=None)
- bleed триггерится в take_damage при amount > 0, стаки полностью сбрасываются (s['bleed'] = 0)
- VampireDamageEffect: хил = max(1, final_dmg // 2)
- DamageEffect и Enemy.execute_intent — оба передают combat_manager в take_damage

## Исправленные баги (последние)
[53] ui/Chest.py → ui/chest/ — регистр импорта
[54] max_damage_dealt всегда 0 — исправлено в EffectCalculator.calculate_damage()
[55] Карты в сундуке затемнялись — player=None в draw_card_row + сброс energy в distribute_combat_rewards