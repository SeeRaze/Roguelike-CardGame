# _project_map.md
# Читать ПЕРВЫМ в каждой сессии. Актуально на Jun 3, 2026 — Сессия 15.

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
core/relics/__init__.py, base.py, starter.py, elemental.py, advanced.py
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
- take_damage(amount, attacker=None, combat_manager=None) — combat_manager нужен для триггера bleed и on_bleed_tick
- heal(amount, combat_manager=None) — с ограничением по max_hp, возвращает фактически восстановленное, вызывает on_heal

**StatusRegistry.py** — единый реестр 9 статусов:
vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed
Добавить статус = одна запись здесь.

**EffectCalculator.py** — единая точка боевой математики (реликвии → ярость → слабость → уязвимость → комбо пар). dry_run=True для превью. При dry_run=False обновляет gm.stats["max_damage_dealt"]. Определяет is_player_attack (attacker is combat_manager.player) и передаёт в on_damage_calculated.

**base.py (cards)** — все эффекты:
- DamageEffect — урон, передаёт combat_manager в take_damage
- VampireDamageEffect — урон + хил 50% от фактического (max(1, dmg//2)), передаёт combat_manager в heal
- ShieldEffect, HealEffect (передаёт combat_manager в heal), RegenEffect, StatusEffect, PoisonEffect
- BleedEffect — в core/cards/debuff/bleed.py

**Реликвии** — хуки:
- on_combat_start(cm) ✅
- on_turn_start(cm) ✅
- on_damage_calculated(base_dmg, is_player_attack=True) ✅ — ВСЕГДА проверять флаг!
- on_tick_ignited(creature) ✅
- on_wet_applied(cm) ✅
- on_card_played(card, cm) ✅ подключён в CombatManager.play_card_by_index
- on_combat_end(player) ✅ подключён в GameManager.distribute_combat_rewards
- on_bleed_tick(bleed_dmg, creature, cm) ✅ подключён в Creature.take_damage
- on_heal(healed_amount, creature) ✅ подключён в Creature.heal
- on_chest_opened(chest_type, gm) ✅ подключён в ui/chest/common.py
- on_shield_gained(amount, creature) — заглушка
- on_kill(enemy, cm) — заглушка

## Реликвии (17 штук, актуально Сессия 15)

**COMMON:** LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок
**UNCOMMON:** ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник
**RARE:** ЭнергоЯдро, СердцеТитана, ГнилойКлык
**LEGENDARY:** ПроклятаяКорона

Детали реализации:
- ТочильныйКамень, ПроклятаяКорона, ЗаточенныйОсколок: проверяют is_player_attack в on_damage_calculated
- ГнилойКлык: bleed в конце хода делится вдвое (//2) вместо сброса в 0 — логика в Creature.tick_statuses
- Заплатка, ЭнергоЯдро: флаг _applied, эффект применяется один раз за забег
- СвинцовыйНабалдашник: флаг _used_this_turn, сбрасывается в on_turn_start
- ЗаточенныйОсколок: флаг _used_this_combat, сбрасывается в on_combat_start
- ПроклятаяКорона: gold/removal_price эффекты — TODO (не реализованы)

## Механики (Сессия 14)

**Heal** — HealEffect в base.py, карты в core/cards/heal.py

**Regen** — RegenEffect в base.py, статус в StatusRegistry.
Тик в Creature.tick_statuses: хилит N HP, затем убывает на 1.
Карты в core/cards/buff/regen.py.

**Exile** — свойство exile=False на Card.
Логика в CombatManager.play_card_by_index: exile=True → deck_manager.exile_pile.
DeckManager.reset_deck() возвращает exile_pile в pool перед новым боем.

**Bleed (кровотечение)** — BleedEffect в core/cards/debuff/bleed.py.
Триггер в Creature.take_damage: при каждом ударе (amount > 0) → on_bleed_tick → +bleed урона сквозь щит.
В конце хода: s['bleed'] = 0 (полный сброс) — если нет ГнилогоКлыка (тогда //= 2).
Карты: Порез COMMON, Кровопускание UNCOMMON, Открытая Рана RARE+exile.

**Vampirism (вампиризм)** — VampireDamageEffect в base.py.
Хил = max(1, final_dmg // 2). Синергия с Яростью автоматическая.
Карты в core/cards/buff/vampirism.py: Высасывание UNCOMMON, Кровавый Пир RARE+exile, Жизнеотвод COMMON.

## Библиотека карт (Сессия 13)
- ui/CardLibraryView.py — статический класс CardLibraryView
- Кнопка "КАРТЫ" в MainMenu.py между "ВОЙТИ В ЛАГЕРЬ" и "ВЫХОД"
- State "CARD_LIBRARY" в DRAW_HANDLERS (GameView) и STATE_HANDLERS (InputHandler)
- 4 вкладки: Все / Воин / Разбойник / Маг
- COLS=8, CARD_W=180, CARD_H=250, START_X=60, START_Y=200
- Скролл колесом, клиппинг под шапку (y=90), тултипы при наведении
- ⚠️ Новые карты (bleed, regen, vampirism, heal) в библиотеку ещё не добавлены

## Экран победы (VictoryScreen) — Сессия 12
- distribute_combat_rewards() → pending_rewards → state "VICTORY"
- Кнопки "Получить" / "Получить все" / "Продолжить" + модалка подтверждения

## Сброс состояния игрока после боя — Сессия 12
В distribute_combat_rewards(): energy=max_energy, shield=0, weak/vulnerable/wet/ignited=0.
strength, thorns НЕ сбрасываются — ⚠️ БАГ: strength нужно сбрасывать (план Сессии 16).

## Реализованные системы
- Все 14 пунктов плана масштабируемости (A-N) ✅
- Система сундуков: common / locked / cursed (ui/chest/) ✅
- Система ивентов: positive / negative / neutral / special (ui/events/) ✅
- UI реликвий в бою с тултипами (ui/combat/hud.py) ✅
- Хук on_wet_applied в Creature.add_status ✅
- Экран победы с наградами и модалкой (ui/VictoryScreen.py) ✅
- Библиотека карт (ui/CardLibraryView.py) ✅
- Heal / Regen / Exile / Bleed / Vampirism ✅
- 11 новых реликвий в core/relics/advanced.py ✅
- Хуки on_card_played / on_combat_end / on_bleed_tick / on_heal / on_chest_opened ✅
- Флаг is_player_attack в EffectCalculator ✅

## Аудит реликвий (все работают)
- LuckyClover: on_combat_start → draw_cards(2) ✅
- SpikedBracelet: on_combat_start → gain_shield(10) ✅
- ТочильныйКамень: on_damage_calculated(is_player_attack) → +2 урона ✅
- ЭнергоЯдро: on_combat_start → max_energy+1, флаг _applied ✅
- ДревнееОгниво: on_tick_ignited → +2 к горению ✅
- НамокшаяРукавица: on_wet_applied → +4 щита ✅
- ОкровавленныйШприц: on_card_played (exile) → +1 энергия + яд 2 ✅
- СердцеТитана: on_combat_end → хил 20% недостающего HP ✅
- ГнилойКлык: on_bleed_tick + tick_statuses (bleed //= 2) ✅
- ПроклятаяКорона: on_damage_calculated(is_player_attack) → x2 урон ✅
- ФлаконСЖелчью: on_combat_start → яд 3 на врага ✅
- СвинцовыйНабалдашник: on_card_played (первая атака) → слабость 1 ✅
- СтараяПиявка: on_heal → +2 HP бонус ✅
- СчастливаяМонетка: on_chest_opened("common") → +10 золота ✅
- ЗасохшийКлевер: on_combat_start → regen 1 ✅
- Заплатка: on_combat_start → max_hp+5, флаг _applied ✅
- ЗаточенныйОсколок: on_damage_calculated(is_player_attack) → +3 первая атака ✅

## Известные нерешённые проблемы
- Щит врага сбрасывается каждый ход (намеренно)
- Хуки on_shield_gained, on_kill — заглушки, не подключены
- Новые карты (bleed, regen, vampirism, heal) не добавлены в CardLibraryView
- ПроклятаяКорона: gold/removal_price эффекты не реализованы
- ⚠️ Ярость (strength) не сбрасывается в конце боя

## План следующей сессии (Сессия 16)

**Приоритет 1 — дебаг:**
1. Ярость (strength) не сбрасывается в конце боя — добавить в distribute_combat_rewards: player.statuses['strength'] = 0
2. Описание выборов в проклятом сундуке вылезает за рамки — фикс ui/chest/cursed.py (перенос текста / уменьшение шрифта / clipping)
3. Проверить другие баги UI (сундуки, ивенты, магазин)

**Приоритет 2 — магазин:**
4. Проверить Shop.py — все ли новые карты (bleed, regen, vampirism, heal) в ассортименте
5. Расширить пул карт магазина если нужно

**Приоритет 3 — TODO реликвий:**
6. ПроклятаяКорона: в distribute_combat_rewards пропускать gold reward если реликвия есть
7. ПроклятаяКорона: в get_removal_price умножать на 2 если реликвия есть

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
- Creature.heal сигнатура: (amount, combat_manager=None)
- bleed триггерится в take_damage при amount > 0; сброс в конце хода: =0 (без ГнилогоКлыка) или //=2 (с ним)
- VampireDamageEffect: хил = max(1, final_dmg // 2)
- on_damage_calculated(base_dmg, is_player_attack=True) — ВСЕГДА проверять флаг, иначе баффает врагов
- DamageEffect и Enemy.execute_intent — оба передают combat_manager в take_damage

## Исправленные баги (последние)
[53] ui/Chest.py → ui/chest/ — регистр импорта
[54] max_damage_dealt всегда 0 — исправлено в EffectCalculator.calculate_damage()
[55] Карты в сундуке затемнялись — player=None в draw_card_row + сброс energy в distribute_combat_rewards
[56] ПроклятаяКорона и ТочильныйКамень баффали урон врагов — добавлен флаг is_player_attack в EffectCalculator