# _project_map.md
# Roguelike-CardGame — Project Map
# Последнее обновление: Сессия 26 (Jun 3, 2026)

## Архитектура
- core/ — вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py)
- ui/ — вся отрисовка (CardRenderer.py, CombatInterface.py, GameView.py, HubView.py, MainMenu.py и др.)
- managers/ — CombatManager, DeckManager, GameManager, MapGenerator, network_manager
- Разрешение: строго 1920x1080 Full HD
- Ветка разработки: dev (main — стабильная, dev — активная работа)

## Железные ГОСТы
- Лимит файла: 150 строк (золотой стандарт)
- Если файл разрастается — рефакторинг и разбивка на модули
- Модульность и логичные зависимости — главный принцип
- Никаких "божественных объектов"

## Навигация по проекту
- В корне репо лежит _project_map.md — читать ПЕРВЫМ в каждой сессии
- URL: https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/_project_map.md
- Большие файлы (GameManager.py, CombatInterface.py, GameView.py) — использовать query_context
- Остальные файлы читаются за один запрос напрямую
- Все файлы читать из ветки dev: https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу

## Ключевые системы

### Creature.py
- Базовый класс (hp, shield, self.statuses={} через __getattr__/__setattr__)
- take_damage(amount, attacker=None, combat_manager=None)
- heal(amount, combat_manager=None)
- gain_shield(amount, combat_manager=None) — с хуком on_shield_gained
- add_status(key, amount, combat_manager=None) — блокирует стихии (_ELEMENTAL_KEYS) если combat_manager._elemental_blocked и self is enemy

### StatusRegistry.py
- Единый реестр всех 10 статусов: vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire

### EffectCalculator.py
- Единая точка боевой математики. dry_run=True для превью
- Обновляет gm.stats["max_damage_dealt"]
- Определяет is_player_attack, передаёт в on_damage_calculated
- Пассив Берсерка: бонус = int((1 - hp/max_hp) * 10), применяется между шагом 2 (ярость) и шагом 3 (слабость), только is_player_attack и type(attacker).__name__ == "Berserker"

### Реликвии — хуки
on_combat_start, on_turn_start, on_damage_calculated(base_dmg, is_player_attack=True),
on_tick_ignited, on_wet_applied, on_card_played, on_shield_gained(amount, creature, combat_manager=None),
on_kill (заглушка), on_combat_end, on_bleed_tick, on_heal, on_chest_opened

- on_turn_start вызывается в CombatManager.start_turn_phase ПОСЛЕ сброса щита

### Активные способности классов (Сессия 26)
- core/players/ability.py — базовый класс ClassAbility
- core/players/abilities.py — все 5 способностей
- Хуки: on_combat_start(cm), on_turn_start(cm), activate(cm)
- is_ready() -> not self._used (базовая реализация, один раз за бой)

|
 Класс     
|
 Способность        
|
 Эффект                                                              
|
|
-----------
|
--------------------
|
---------------------------------------------------------------------
|
|
 Warrior   
|
 Щитовой удар       
|
 Урон врагу = 50% текущего щита. 1×/бой                             
|
|
 Rogue     
|
 Вскрытие           
|
 Удвоить bleed на враге, -1 энергия следующий ход. 1×/бой           
|
|
 Mage      
|
 Стихийный барьер   
|
 Блок стихий на врага 1 ход + щит = сумма стихий×3. 1×/бой         
|
|
 Druid     
|
 Токсичный взрыв    
|
 Снять весь яд с врага, нанести разом, regen = яд//2. 1×/бой       
|
|
 Berserker 
|
 Кровавая ярость    
|
 -10% макс HP себе сквозь щит, +strength = урон×2. 1×/бой          
|

### Пассивки классов (Сессия 25)
- Хуки в base.py: on_turn_start_passive(cm), on_card_played_passive(card, cm), on_heal_passive(healed, cm)
- Warrior «Железный задел»: carry = int(shield * 0.3) до сброса щита
- Mage «Стихийный резонанс»: добрать 1 карту после триггера «Пар»
- Druid «Токсичный круговорот»: при хиле накладывает яд на врага = healed

### CombatManager
- __init__: вызывает ability.on_combat_start(self) после реликвий
- start_turn_phase: вызывает ability.on_turn_start(self) после реликвий
- self._elemental_blocked = False — флаг для МагоМ способности
- self._steam_combo_triggered = False — флаг для пассивки Мага
- Порядок start_turn_phase: on_turn_start_passive → carry → shield=carry → _iron_will_shield → energy → draw → on_turn_start (реликвии) → on_turn_start (ability)

### UI — CombatInterface / CombatHUD
- draw_ability_slot(screen, font, ability, x, y) → pygame.Rect
  - Зелёная кнопка если ready, серая если used
  - Hover через pygame.mouse.get_pos() напрямую
  - Статус-текст под кнопкой ("готова" / "использована")
- view.ability_rect — сохраняется каждый кадр в _draw_player_panel
- InputHandler: клик по ability_rect → ability.activate(combat_manager)

### Персонажи
Warrior (HP80, E3), Rogue (HP65, E4), Mage (HP55, E3), Druid (HP70, E3), Berserker (HP60, E3)

### Враги
Cultist, SlimeAndGoblins, BossTitan

### Формулы врагов (ТЕСТОВЫЕ — занижены, требуют балансировки)
- hp = 20 + floor×3 + tier×10
- dmg = 3 + tier×1
- shld = 2
- Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

### Лидерборд
Через Google Apps Script (асинхронный фоновый поток, threading.Thread daemon=True)

## Полный список файлов (актуально на Jun 3, 2026 — после Сессии 26)
main.py, server.py, _project_map.md
core/rarity.py, core/Creature.py, core/EffectCalculator.py, core/StatusRegistry.py
core/cards/__init__.py, base.py, basic.py, fire.py, poison.py, water.py, heal.py
core/cards/buff/__init__.py, strength.py, thorns.py, regen.py, vampirism.py
core/cards/debuff/__init__.py, vulnerable.py, weak.py, bleed.py
core/enemies/__init__.py, base.py, cultist.py, slime.py, boss.py
core/players/__init__.py, base.py, ability.py, abilities.py
core/players/mage.py, rogue.py, warrior.py, druid.py, berserker.py
core/relics/__init__.py, base.py, starter.py, elemental.py, advanced.py
managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py, MapGenerator.py, network_manager.py
ui/chest/__init__.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py
ui/combat/__init__.py, hud.py
ui/events/__init__.py, event_data.py, event_effects.py, positive.py, negative.py, neutral.py, special.py
ui/Campfire.py, CardRenderer.py, CombatInterface.py, CardLibraryView.py
ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py
ui/VictoryScreen.py

## Реализованные системы (после Сессии 26)
Все 14 пунктов плана масштабируемости (A-N) ВЫПОЛНЕНЫ.

Реликвии — 19 итого:
- COMMON: LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок
- UNCOMMON: ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник, ШипастаяБроня
- RARE: ЭнергоЯдро, СердцеТитана, ГнилойКлык, ЖелезнаяВоля
- LEGENDARY: ПроклятаяКорона

## Важные грабли (накопленные)
- Отступы Python сбиваются при копировании из чата — всегда проверять
- view.view.gm — двойной view это баг
- Pygame не поддерживает эмодзи в SysFont — использовать текстовые маркеры ([A] для активных)
- pygame.display.flip() — один раз в конце GameView.draw()
- EventView.py — НЕ класс, только функции
- self.relics (не self.player_relics!) в GameManager
- tick_statuses принимает combat_manager=None — всегда передавать self из CombatManager
- spawn_procedural_enemy — МЕТОД GameManager, не импортировать из core.enemies
- Все файлы читать из ветки DEV, не main
- CombatManager.__init__: (player, enemy, starting_deck, game_manager=None)
- RARITY_COLORS импортировать из core.rarity
- on_wet_applied — через Creature.add_status, НЕ напрямую
- bonus_draw — getattr с дефолтом 0
- ui/chest/ — маленькая c: from ui.chest import ...
- VictoryScreen._show_modal — классовая переменная, сбрасывается в _proceed()
- CardRenderer.draw(player=None) — карта всегда доступна (can_afford=True)
- _classify_card импортирует DamageEffect, ShieldEffect, BuffEffect
- random.shuffle в тултипе стопки — НЕ вызывать каждый кадр
- gain_shield без combat_manager — on_shield_gained не сработает; всегда передавать cm
- InputHandler обрабатывает только MOUSEDOWN (клики), MOUSEMOTION не реализован — hover считать прямо в draw-методах через pygame.mouse.get_pos()
- end_turn_rect пересчитывается каждый кадр в _draw_end_turn_btn (не хранить статично)
- ability_rect пересчитывается каждый кадр в _draw_player_panel (не хранить статично)
- _elemental_blocked проверяется в add_status только если self is combat_manager.enemy
- RogueAbility._penalty_pending: on_turn_start снимает -1 энергию ПОСЛЕ восстановления

## Задачи для будущих сессий

### on_kill хук — реликвии-заглушки
- Пока 1 враг в бою → on_kill не имеет смысла
- Когда появятся мульти-враги → реализовать: Трофейный Клык (UNCOMMON, +1 Сила после убийства), Берсерк-Медальон (RARE, +1 Энергия после убийства)

### Активные способности — тултип в бою
- draw_ability_tooltip в CombatHUD (по аналогии с draw_relic_tooltip)
- Показывать ability.description при наведении на кнопку

### HubView — описание активных способностей
- Добавить строку «Активная: [название] — [описание]» в карточку класса

### Балансировка (ПРИОРИТЕТ)
- Тестовые формулы врагов занижены — повысить сложность
- Пересмотреть hp/dmg/shld для всех тиров и этажей
- Учесть контентные обновления (реликвии, пассивки, активки)

### Элитные враги на карте
- Новый тип узла на карте (elite)
- Класс EliteEnemy или флаг is_elite на базовом Enemy
- Повышенные статы + гарантированная редкая реликвия как награда

## План Сессии 27
Приоритет 1:
1. HubView — описание активных способностей в карточках классов
2. Тултип активной способности при наведении в бою

Приоритет 2:
3. Балансировка врагов — повысить сложность (пересмотр формул)
4. Механика элитных врагов на карте

## Статус: Сессия 26 завершена (Jun 3, 2026). Активки работают, протестирован Воин.