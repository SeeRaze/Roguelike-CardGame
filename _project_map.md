# _project_map.md
_Последнее обновление: Сессия 27, Jun 3, 2026_

## Архитектура
- `core/` — вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py)
- `ui/` — вся отрисовка (CardRenderer.py, CombatInterface.py, GameView.py, HubView.py, MainMenu.py и др.)
- `managers/` — CombatManager, DeckManager, GameManager, MapGenerator, network_manager
- Разрешение: строго 1920×1080 Full HD
- **Ветка разработки: dev** (main — стабильная, dev — активная работа)

## Железные ГОСТы
- Лимит файла: 150 строк (золотой стандарт)
- Если файл разрастается — рефакторинг и разбивка на модули
- Модульность и логичные зависимости — главный принцип
- Никаких "божественных объектов"

## Навигация по проекту
- Читать этот файл ПЕРВЫМ в каждой сессии
- Большие файлы (GameManager.py, CombatInterface.py, GameView.py) — использовать query_context
- Остальные файлы читаются за один запрос напрямую
- Все файлы читать из ветки dev:
  `https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу`

## Полный список файлов (актуально на Jun 3, 2026 — после Сессии 27)
main.py, server.py, _project_map.md

core/rarity.py, core/Creature.py, core/EffectCalculator.py, core/StatusRegistry.py

core/cards/init.py, base.py, basic.py, fire.py, poison.py, water.py, heal.py

core/cards/buff/init.py, strength.py, thorns.py, regen.py, vampirism.py

core/cards/debuff/init.py, vulnerable.py, weak.py, bleed.py

core/enemies/init.py, base.py, cultist.py, slime.py, boss.py

core/players/init.py, base.py, mage.py, rogue.py, warrior.py, druid.py, berserker.py

core/players/ability.py, abilities.py

core/relics/init.py, base.py, starter.py, elemental.py, advanced.py

managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py,

     MapGenerator.py, network_manager.py
ui/chest/init.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py

ui/combat/init.py, hud.py

ui/events/init.py, event_data.py, event_effects.py, positive.py, negative.py,

      neutral.py, special.py
ui/Campfire.py, CardRenderer.py, CombatInterface.py, CardLibraryView.py

ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py,

MainMenu.py, MapView.py, Shop.py, VictoryScreen.py


## Ключевые системы

### Creature.py
Базовый класс (hp, shield, self.statuses={} через __getattr__/__setattr__).
- `take_damage(amount, attacker=None, combat_manager=None)`
- `heal(amount, combat_manager=None)`
- `gain_shield(amount, combat_manager=None)` — с хуком on_shield_gained
- `_ELEMENTAL_KEYS = frozenset(("ignited", "wet", "poison"))` — блокируется при `_elemental_blocked`

### StatusRegistry.py
Единый реестр всех 10 статусов:
vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire

### EffectCalculator.py
Единая точка боевой математики. `dry_run=True` для превью.
- Обновляет `gm.stats["max_damage_dealt"]`
- Определяет `is_player_attack`, передаёт в `on_damage_calculated`
- Пассив Берсерка: бонус = `int((1 - hp/max_hp) * 10)`, применяется между шагом 2 (ярость) и шагом 3 (слабость), только `is_player_attack` и `type(attacker).__name__ == "Berserker"`

### Реликвии — хуки
`on_combat_start`, `on_turn_start`, `on_damage_calculated(base_dmg, is_player_attack=True)`,
`on_tick_ignited`, `on_wet_applied`, `on_card_played`, `on_shield_gained(amount, creature, combat_manager=None)`,
`on_kill` (заглушка), `on_combat_end`, `on_bleed_tick`, `on_heal`, `on_chest_opened`

`on_turn_start` вызывается в `CombatManager.start_turn_phase` ПОСЛЕ сброса щита.

### Активные способности классов
Файлы: `core/players/ability.py` (базовый класс), `core/players/abilities.py` (все 5).
- **WarriorAbility «Щитовой удар»**: урон врагу = 50% текущего щита. Один раз за бой.
- **RogueAbility «Вскрытие»**: удвоить кровотечение на враге, -1 энергия в следующем ходу. Один раз за бой. Флаг `_penalty_pending`, хук `on_turn_start`.
- **MageAbility «Стихийный барьер»**: блок стихий на врага на 1 ход (`_elemental_blocked` на CombatManager), щит = сумма стихийных стаков × 3. Один раз за бой.
- **DruidAbility «Токсичный взрыв»**: снять весь яд с врага, нанести разом, Регенерация = яд // 2. Один раз за бой.
- **BerserkerAbility «Кровавая ярость»**: -10% макс HP себе сквозь щит, +Ярость = урон × 2. Один раз за бой.

UI: `draw_ability_slot` в `hud.py` → `view.ability_rect` (пересчитывается каждый кадр).
Тултип: `CombatHUD.draw_ability_tooltip(screen, font, ability, mouse_pos)` — вызывается в конце `draw_combat_screen` при наведении.

### Пассивы классов
- **Warrior**: `on_turn_start` — +1 щит за каждые 2 карты в руке
- **Mage**: `on_card_played` — если карта стихийная, +1 к соответствующему стаку (ignited/wet/poison)
- **Druid**: `on_turn_start` — если яд на враге > 0, +1 регенерация себе

### Враги — формулы (актуальные)
hp = 35 + floor5 + tier15

dmg = 5 + tier*2 + floor//3

shld = 3 + tier*1

Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

Элита: hp×1.5, dmg×1.4, shld×1.5, shield=shld (стартует со щитом)


### Элитные враги
- Тип узла `"ELITE"` в MapGenerator (вес 5, не появляется на строках 0 и 1)
- `enemy.is_elite = True` флаг на объекте
- Награды: 100% реликвия (25% RARE / 75% UNCOMMON), золото ×1.5
- `handle_click`: `ELITE` → `room_type = "COMBAT"`

### MapView.py — иконки узлов
`_draw_node_icon(screen, ntype, cx, cy, r, fill, border, bw)` — геометрические символы:
- COMBAT: скрещенные мечи | ELITE: корона | CAMPFIRE: костёр
- SHOP: монета "з" | CHEST: сундук | EVENT: "?" | BOSS: череп
- ⚠️ MapView.py превышает 150 строк — кандидат на рефакторинг (вынести в `ui/map_icons.py`)

## Реализованные системы (после Сессии 27)
Все 14 пунктов плана масштабируемости (A–N) ВЫПОЛНЕНЫ.

Реликвии — 19 итого:
- COMMON: LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок
- UNCOMMON: ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник, ШипастаяБроня
- RARE: ЭнергоЯдро, СердцеТитана, ГнилойКлык, ЖелезнаяВоля
- LEGENDARY: ПроклятаяКорона

## Важные детали и грабли
- `on_damage_calculated(base_dmg, is_player_attack=True)` — ВСЕГДА проверять флаг в реликвиях
- `Creature.take_damage(amount, attacker=None, combat_manager=None)`
- `gain_shield` без `combat_manager` — `on_shield_gained` не сработает; всегда передавать cm
- `bleed`: триггер в `take_damage` при `amount>0`; сброс =0 (без ГнилогоКлыка) или //=2 (с ним)
- `vampire`: триггер в `take_damage` при `amount>0` и `attacker.vampire>0`; хил `max(1, amount//2)`; `vampire //= 2`
- `distribute_combat_rewards()` → `pending_rewards` → VICTORY
- `CardLibraryView`: карты привязаны к классам, NEW_CARDS упразднён
- `ui/chest/shared.py`: `draw_card_row` возвращает `(card, rect)` или `None`
- `CardRenderer.draw` сигнатура: `(surface, card, x, y, font_title, font_desc, is_hovered=False, player=None, enemy=None)` — НЕ Rect!
- `_EXTRA_KEYWORDS` — модульная переменная в `CardRenderer.py`, НЕ в StatusRegistry
- `draw_pile_rect` и `discard_pile_rect` — атрибуты GameView, не CombatInterface
- `temp_cost` на карте — временный атрибут Разбойника, живёт только в руке
- `ЖелезнаяВоля`: `is_active=True`, `activate()` вызывается из InputHandler при клике
- `end_turn_rect` пересчитывается каждый кадр в `_draw_end_turn_btn`
- Hover кнопки: прямая проверка `pygame.mouse.get_pos()`, НЕ через `view.hover`
- `VictoryScreen._show_modal` — классовая переменная, сбрасывается в `_proceed()`
- `random.shuffle` в тултипе стопки — НЕ вызывать каждый кадр
- `CombatManager.__init__(player, enemy, starting_deck, game_manager=None)`
- `RARITY_COLORS` импортировать из `core.rarity`
- `on_wet_applied` — через `Creature.add_status`, НЕ напрямую
- `bonus_draw` — `getattr` с дефолтом 0
- `ui/chest/` — маленькая c: `from ui.chest import ...`
- `pygame.display.flip()` — один раз в конце `GameView.draw()`
- `EventView.py` — НЕ класс, только функции
- `self.relics` (не `self.player_relics`!) в GameManager
- `tick_statuses` принимает `combat_manager=None` — всегда передавать `self` из CombatManager
- `spawn_procedural_enemy` — МЕТОД GameManager, не импортировать из core.enemies
- `_elemental_blocked` проверяется в `Creature.add_status` только если `self is combat_manager.enemy`
- `RogueAbility._penalty_pending`: `on_turn_start` снимает -1 энергию ПОСЛЕ восстановления
- `BerserkerAbility`: урон себе напрямую в `hp` (сквозь щит), не через `take_damage`

## Правила работы
- Никогда не просить у пользователя отдельные файлы — брать из репо через query_context
- В конце каждой сессии — скидывать полный готовый текст `_project_map.md` для ручной вставки (не фрагменты, не диффы — весь файл целиком)

## Задачи для будущих сессий

### Сессия 28 — Приоритет 1:
1. **Инвентарь реликвий в бою** — реликвии не помещаются на полосе, нужен отдельный UI (свёрнутая панель / скролл / отдельный экран по кнопке)

### Сессия 28 — Приоритет 2 (аудит и рефакторинг):
2. MapView.py: вынести `_draw_node_icon` в `ui/map_icons.py`
3. Проверить все файлы на превышение 150 строк
4. Общий аудит зависимостей и модульности

### Отложено (нужны мульти-враги):
- `on_kill` хук — реликвии-заглушки:
  - Трофейный Клык (UNCOMMON, +1 Сила после убийства)
  - Берсерк-Медальон (RARE, +1 Энергия после убийства)

### Отложено (инфраструктура не готова):
- Механика элитных врагов на карте — **ВЫПОЛНЕНО в Сессии 27**

## Статус
Сессия 27 завершена (Jun 3, 2026).
Следующая: Сессия 28 — инвентарь реликвий в бою + аудит/рефакторинг.