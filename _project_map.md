# _project_map.md
# Читать ПЕРВЫМ в каждой сессии. Актуально на Jun 3, 2026 — Сессия 16.

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
core/EffectCalculator.py, core/StatusRegistry.py
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
- take_damage(amount, attacker=None, combat_manager=None) — combat_manager нужен для bleed и on_bleed_tick
- heal(amount, combat_manager=None) — возвращает фактически восстановленное, вызывает on_heal

**StatusRegistry.py** — единый реестр 9 статусов:
vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed
Добавить статус = одна запись здесь.

**EffectCalculator.py** — единая точка боевой математики (реликвии → ярость → слабость → уязвимость → комбо пар). dry_run=True для превью. При dry_run=False обновляет gm.stats["max_damage_dealt"]. Определяет is_player_attack и передаёт в on_damage_calculated.

**base.py (cards)** — все эффекты:
- DamageEffect, VampireDamageEffect (урон + хил max(1, dmg//2))
- ShieldEffect, HealEffect, RegenEffect, StatusEffect, PoisonEffect
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
- on_shield_gained — заглушка
- on_kill — заглушка

## Реликвии (17 штук)

**COMMON:** LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок
**UNCOMMON:** ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник
**RARE:** ЭнергоЯдро, СердцеТитана, ГнилойКлык
**LEGENDARY:** ПроклятаяКорона

Детали реализации:
- ТочильныйКамень, ПроклятаяКорона, ЗаточенныйОсколок: проверяют is_player_attack в on_damage_calculated
- ГнилойКлык: bleed в конце хода //= 2 вместо сброса в 0 — логика в Creature.tick_statuses
- Заплатка, ЭнергоЯдро: флаг _applied, эффект один раз за забег
- СвинцовыйНабалдашник: флаг _used_this_turn, сбрасывается в on_turn_start
- ЗаточенныйОсколок: флаг _used_this_combat, сбрасывается в on_combat_start
- ПроклятаяКорона: цена удаления ×2 реализована в get_removal_price ✅
- ПроклятаяКорона: пропуск gold reward — TODO (не реализован)

## Механики

**Heal** — HealEffect в base.py, карты в core/cards/heal.py (Бинт COMMON, Второе Дыхание UNCOMMON, Эликсир RARE)

**Regen** — RegenEffect в base.py, статус в StatusRegistry. Тик в Creature.tick_statuses: хилит N HP, убывает на 1. Карты в core/cards/buff/regen.py (Регенерация COMMON, Живучесть UNCOMMON, Перевязка RARE)

**Exile** — exile=False на Card. В CombatManager.play_card_by_index: exile=True → deck_manager.exile_pile. DeckManager.reset_deck() возвращает exile_pile в pool перед новым боем.

**Bleed** — BleedEffect в core/cards/debuff/bleed.py. Триггер в take_damage при amount>0 → on_bleed_tick → +bleed урона сквозь щит. Конец хода: s['bleed']=0 (без ГнилогоКлыка) или //=2 (с ним). Карты: Порез COMMON, Кровопускание UNCOMMON, Открытая Рана RARE+exile.

**Vampirism** — VampireDamageEffect в base.py. Хил = max(1, final_dmg//2). Карты в core/cards/buff/vampirism.py: Жизнеотвод COMMON, Высасывание UNCOMMON, Кровавый Пир RARE+exile.

## Библиотека карт
- ui/CardLibraryView.py — статический класс CardLibraryView
- Кнопка "КАРТЫ" в MainMenu.py между "ВОЙТИ В ЛАГЕРЬ" и "ВЫХОД"
- State "CARD_LIBRARY" в DRAW_HANDLERS (GameView) и STATE_HANDLERS (InputHandler)
- 4 вкладки: Все / Воин / Разбойник / Маг
- COLS=8, CARD_W=180, CARD_H=250, START_X=60, START_Y=200
- Скролл колесом, клиппинг под шапку (y=90), тултипы при наведении
- Новые карты (heal/regen/vampirism/bleed) добавлены в NEW_CARDS без привязки к классу ✅
- Привязка к классам — TODO (Сессия 17)

## Экран победы
- distribute_combat_rewards() → pending_rewards → state "VICTORY"
- Кнопки "Получить" / "Получить все" / "Продолжить" + модалка подтверждения
- После боя сбрасывается: energy=max_energy, shield=0, weak/vulnerable/wet/ignited/strength=0 ✅

## Реализованные системы
- Все 14 пунктов плана масштабируемости (A-N) ✅
- Система сундуков: common / locked / cursed (ui/chest/) ✅
- Система ивентов: positive / negative / neutral / special (ui/events/) ✅
- UI реликвий в бою с тултипами (ui/combat/hud.py) ✅
- Экран победы с наградами и модалкой (ui/VictoryScreen.py) ✅
- Библиотека карт (ui/CardLibraryView.py) ✅
- Heal / Regen / Exile / Bleed / Vampirism ✅
- 17 реликвий (starter.py, elemental.py, advanced.py) ✅
- Все хуки реликвий подключены ✅
- Контентный аудит: новые карты зарегистрированы в Shop, CardLibrary, events, chest ✅

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
- ПроклятаяКорона: пропуск gold reward не реализован
- Привязка новых карт к классам в CardLibraryView — TODO

## План следующей сессии (Сессия 17)

**Приоритет 1 — тестирование:**
1. Запустить игру, пройти несколько боёв — проверить все фиксы Сессии 16
2. Новые карты появляются в магазине, сундуках, ивентах?
3. Ярость сбрасывается после боя?
4. Word wrap в проклятом сундуке работает?

**Приоритет 2 — новый контент:**
5. Привязка карт к классам (Воин/Разбойник/Маг) в CardLibraryView и стартовых деках
6. ПроклятаяКорона: пропуск gold reward в distribute_combat_rewards

**Приоритет 3 — полировка:**
7. Хуки on_shield_gained, on_kill — подключить если нужны реликвии
8. Балансировка по результатам тестирования

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
- ui/chest/ — маленькая c: from ui.chest import ...
- distribute_combat_rewards() → pending_rewards → VICTORY; _handle_combat не вызывает setup_next_floor
- VictoryScreen._show_modal — классовая переменная, сбрасывается в _proceed()
- CardRenderer.draw(player=None) — карта всегда доступна (can_afford=True)
- Creature.take_damage сигнатура: (amount, attacker=None, combat_manager=None)
- Creature.heal сигнатура: (amount, combat_manager=None)
- bleed: триггер в take_damage при amount>0; сброс =0 (без ГнилогоКлыка) или //=2 (с ним)
- VampireDamageEffect: хил = max(1, final_dmg // 2)
- on_damage_calculated(base_dmg, is_player_attack=True) — ВСЕГДА проверять флаг, иначе баффает врагов

## Исправленные баги (Сессия 16)
[57] Ярость (strength) не сбрасывалась после боя — добавлен сброс в distribute_combat_rewards
[58] Word wrap в проклятом сундуке — добавлен _draw_wrapped() в cursed.py
[59] Новые карты отсутствовали в магазине — расширен пул в Shop.py
[60] core/cards/__init__.py — добавлены экспорты heal/regen/vampirism/bleed
[61] CardLibraryView — новые карты добавлены в NEW_CARDS (без привязки к классу)
[62] event_data.py CARD_FACTORIES — добавлены все 12 новых фабрик
[63] event_effects.py — _get_card_factory и _get_relic_class дополнены до полного списка
[64] chest/data.py CHEST_CARD_POOL — добавлены все 12 новых фабрик
[65] ПроклятаяКорона: цена удаления ×2 реализована в get_removal_price