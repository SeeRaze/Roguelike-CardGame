# _project_map.md
# Последнее обновление: Сессия 25 (Jun 3, 2026)

## Структура проекта

main.py, server.py, _project_map.md
core/rarity.py, core/Creature.py, core/EffectCalculator.py, core/StatusRegistry.py
core/cards/__init__.py, base.py, basic.py, fire.py, poison.py, water.py, heal.py
core/cards/buff/__init__.py, strength.py, thorns.py, regen.py, vampirism.py
core/cards/debuff/__init__.py, vulnerable.py, weak.py, bleed.py
core/enemies/__init__.py, base.py, cultist.py, slime.py, boss.py
core/players/__init__.py, base.py, mage.py, rogue.py, warrior.py, druid.py, berserker.py
core/relics/__init__.py, base.py, starter.py, elemental.py, advanced.py
managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py, MapGenerator.py, network_manager.py
ui/chest/__init__.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py
ui/combat/__init__.py, hud.py
ui/events/__init__.py, event_data.py, event_effects.py, positive.py, negative.py, neutral.py, special.py
ui/Campfire.py, CardRenderer.py, CombatInterface.py, CardLibraryView.py
ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py
ui/VictoryScreen.py

---

## Архитектура

- core/ — вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py)
- ui/ — вся отрисовка
- managers/ — CombatManager, DeckManager, GameManager, MapGenerator, network_manager
- Разрешение: строго 1920x1080 Full HD
- Ветка разработки: dev (main — стабильная, dev — активная работа)

## Железные ГОСТы

- Лимит файла: 150 строк
- Модульность и логичные зависимости — главный принцип
- Никаких "божественных объектов"

---

## Ключевые системы

### Creature.py
- Базовый класс: hp, shield, self.statuses={} через __getattr__/__setattr__
- take_damage(amount, attacker=None, combat_manager=None)
- heal(amount, combat_manager=None) — после хуков реликвий вызывает self.on_heal_passive(healed, cm) если hasattr
- gain_shield(amount, combat_manager=None) — с хуком on_shield_gained

### StatusRegistry.py
- Единый реестр всех 10 статусов: vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire

### EffectCalculator.py
- Единая точка боевой математики. dry_run=True для превью
- Обновляет gm.stats["max_damage_dealt"]
- Определяет is_player_attack, передаёт в on_damage_calculated
- Пассив Берсерка: бонус = int((1 - hp/max_hp) * 10), между шагом 2 (ярость) и шагом 3 (слабость), только is_player_attack и type(attacker).__name__ == "Berserker"
- После триггера «Пар»: выставляет combat_manager._steam_combo_triggered = True (для пассива Мага)

### Реликвии — хуки
on_combat_start, on_turn_start, on_damage_calculated(base_dmg, is_player_attack=True),
on_tick_ignited, on_wet_applied, on_card_played, on_shield_gained(amount, creature, combat_manager=None),
on_kill (заглушка), on_combat_end, on_bleed_tick, on_heal, on_chest_opened
- on_turn_start вызывается в CombatManager.start_turn_phase ПОСЛЕ сброса щита

### Классовые пассивки (Сессия 25)
Хуки в core/players/base.py: on_turn_start_passive(cm), on_card_played_passive(card, cm), on_heal_passive(healed, cm)
CombatManager вызывает хуки — никаких if type == "ClassName" в менеджере.

**Warrior «Железный задел»:**
- on_turn_start_passive: carry = int(shield * 0.3) → self._passive_shield_carry
- CombatManager.start_turn_phase: пассивка ДО сброса → carry → shield=0 → shield=carry → _iron_will_shield=carry
- Порядок критичен: нельзя обнулять щит до вызова пассивки

**Mage «Стихийный резонанс»:**
- EffectCalculator ставит _steam_combo_triggered=True после триггера Пар
- CombatManager.play_card_by_index: сбрасывает флаг перед card.apply, после вызывает on_card_played_passive
- on_card_played_passive: если флаг True → сбросить флаг, добрать 1 карту

**Druid «Токсичный круговорот»:**
- Creature.heal вызывает on_heal_passive(healed, cm) после хуков реликвий
- on_heal_passive: enemy.add_status('poison', healed_amount) если enemy.hp > 0

**Rogue:** temp_cost -1 на случайную карту в руке (живёт только в руке)
**Berserker:** бонус урона = int((1 - hp/max_hp) * 10)

### Персонажи
Warrior (HP80, E3), Rogue (HP65, E4), Mage (HP55, E3), Druid (HP70, E3), Berserker (HP60, E3)

### Враги
Cultist, SlimeAndGoblins, BossTitan

### Формулы врагов (тестовый режим)
hp = 20 + floor×3 + tier×10 | dmg = 3 + tier×1 | shld = 2
Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

### Лидерборд
Google Apps Script, асинхронный фоновый поток (threading.Thread daemon=True)

---

## Реликвии — 19 итого

COMMON: LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок
UNCOMMON: ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник, ШипастаяБроня
RARE: ЭнергоЯдро, СердцеТитана, ГнилойКлык, ЖелезнаяВоля
LEGENDARY: ПроклятаяКорона

---

## UI — стиль и палитра

Единая тёмно-синяя тема (MainMenu, CombatInterface, HubView, EventView):
BG=(12,12,22) или (10,10,20), панели=(20,20,40) или (22,22,40),
рамки=(160,160,255), золото=(255,220,60)

### HubView (рефакторинг Сессия 25)
- 5 карточек классов 300×260px, центрированы: _CLS_X0 = (1920 - 1596) // 2 = 162
- Описание построчно ВНУТРИ карточки — перекрытий нет
- Цветная полоска сверху, «Пассив:» выделен цветом класса
- Стопка карт и кнопка старта центрированы, кнопка y=960, 520×72

### CombatInterface (рефакторинг Сессия 24)
- Игрок слева (x=30), враг справа зеркально (x=1330), отступ 30px от краёв
- Полоса реликвий вверху (высота 52px)
- HP-бары с проекцией урона
- Энергия: ромбы (CombatHUD.draw_energy_diamonds)
- Лог боевых действий под панелью врага
- Кнопка «КОНЕЦ ХОДА» над рубашкой сброса
- Hover кнопок: btn.collidepoint(pygame.mouse.get_pos()) — прямая проверка

### ui/combat/hud.py (новый файл, Сессия 24)
draw_hp_bar, draw_energy_diamonds, draw_status_badges, draw_relics,
draw_status_tooltip, draw_relic_tooltip, draw_pile_tooltip, get_intent_damage_color

---

## Важные детали и грабли

- on_damage_calculated(base_dmg, is_player_attack=True) — ВСЕГДА проверять флаг в реликвиях
- bleed: триггер в take_damage при amount>0; сброс =0 (без ГнилогоКлыка) или //=2 (с ним)
- vampire: триггер в take_damage при amount>0 и attacker.vampire>0; хил max(1, amount//2); vampire //=2
- VampireDamageEffect: DEPRECATED stub в base.py, не использовать
- distribute_combat_rewards() → pending_rewards → VICTORY
- CardLibraryView: карты привязаны к классам, NEW_CARDS упразднён
- ПроклятаяКорона: gold reward пропуск — реализован (Сессия 23)
- ui/chest/shared.py: draw_card_row возвращает (card, rect) или None — не ломать контракт
- CardRenderer.draw сигнатура: (surface, card, x, y, font_title, font_desc, is_hovered=False, player=None, enemy=None) — НЕ Rect!
- _EXTRA_KEYWORDS — модульная переменная в CardRenderer.py, НЕ в StatusRegistry
- draw_pile_rect и discard_pile_rect — атрибуты GameView, не CombatInterface
- _draw_pile_display кешируется в GameView, обновляется по [id(c) for c in dm.draw_pile]
- temp_cost на карте — временный атрибут Разбойника, живёт только в руке
- ЖелезнаяВоля: is_active=True, activate() вызывается из InputHandler при клике
- end_turn_rect пересчитывается каждый кадр в _draw_end_turn_btn (не хранить статично в GameView)
- Hover кнопки конца хода: прямая проверка pygame.mouse.get_pos(), НЕ через view.hover.end_turn
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
- play_card_by_index в CombatManager был вложен сам в себя — исправлено в Сессии 21
- distribute_combat_rewards вызывался многократно — исправлено в Сессии 22
- gain_shield без combat_manager — on_shield_gained не сработает; всегда передавать cm
- InputHandler обрабатывает только MOUSEDOWN (клики), MOUSEMOTION не реализован

---

## Правила работы

- Никогда не просить у пользователя отдельные файлы — брать из репо через query_context
- В конце каждой сессии — скидывать полный готовый текст _project_map.md для ручной вставки (не фрагменты, не диффы — весь файл целиком)

---

## План Сессии 26

Приоритет 1:
1. Аудит вызовов gain_shield в картах/реликвиях — убедиться что везде передаётся combat_manager
2. Тестирование ЖелезнойВоли и ШипастойБрони

Приоритет 2:
3. Активные способности классов: инфраструктура (UI слот, хук activate(), cooldown/charges, InputHandler)
4. on_kill хук — реализовать когда появятся мульти-враги

---

## Статус

Сессия 25 завершена (Jun 3, 2026).
Реализованы пассивки Warrior/Mage/Druid + полный рефакторинг HubView.
Следующая: Сессия 26 — аудит gain_shield + активные способности.