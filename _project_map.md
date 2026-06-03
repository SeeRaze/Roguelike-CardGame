# _project_map.md — Roguelike CardGame
# Актуально: Jun 3, 2026 — после Сессии 18

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

- Читать этот файл ПЕРВЫМ в каждой сессии
- Большие файлы (GameManager.py, CombatInterface.py, GameView.py) — использовать query_context
- Все файлы читать из ветки dev:
  https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу

## Полный список файлов (после Сессии 18)

main.py, server.py, _project_map.md
core/rarity.py
core/Creature.py
core/EffectCalculator.py, core/StatusRegistry.py
core/cards/__init__.py, base.py, basic.py, fire.py, poison.py, water.py
core/cards/heal.py
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

- **Creature.py** — базовый класс (hp, shield, self.statuses={} через __getattr__/__setattr__).
  take_damage(amount, attacker=None, combat_manager=None). heal(amount, combat_manager=None).
- **StatusRegistry.py** — единый реестр всех 9 статусов:
  vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed.
  НЕ добавлять сюда псевдо-ключи (heal, vampire) — сломает Creature.statuses.
- **EffectCalculator.py** — единая точка боевой математики. dry_run=True для превью.
  Обновляет gm.stats["max_damage_dealt"]. Определяет is_player_attack, передаёт в on_damage_calculated.
- **CardRenderer.draw** сигнатура: (surface, card, x, y, font_title, font_desc, is_hovered=False, player=None, enemy=None) — НЕ принимает Rect!
- **_EXTRA_KEYWORDS** в CardRenderer.py — псевдо-ключи {"heal": ..., "vampire": ...} для тултипов карт без статусного эффекта.
- Реликвии через хуки: on_combat_start, on_turn_start, on_damage_calculated(base_dmg, is_player_attack=True),
  on_tick_ignited, on_wet_applied, on_card_played, on_shield_gained (заглушка), on_kill (заглушка),
  on_combat_end, on_bleed_tick, on_heal, on_chest_opened
- Лидерборд через Google Apps Script (асинхронный фоновый поток, threading.Thread daemon=True)
- Персонажи: Warrior (HP80), Rogue (HP65), Mage (HP55)
- Враги: Cultist, SlimeAndGoblins, BossTitan

## Формулы врагов (тестовый режим)

- hp = 20 + floor×3 + tier×10
- dmg = 3 + tier×1
- shld = 2
- Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

## Реализованные системы (после Сессии 18)

Все 14 пунктов плана масштабируемости (A-N) ВЫПОЛНЕНЫ.

### Реликвии — 17 итого:
- COMMON: LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок
- UNCOMMON: ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник
- RARE: ЭнергоЯдро, СердцеТитана, ГнилойКлык
- LEGENDARY: ПроклятаяКорона

### Выполнено в Сессии 18:
- [S18-01] Аудит тултипов карт — _get_card_keywords расширен: RegenEffect→"regen", BleedEffect→"bleed",
  VampireDamageEffect→"vampire", HealEffect→"heal". Добавлен _EXTRA_KEYWORDS.
  draw_card_keyword_tooltip берёт данные из STATUSES[key] или _EXTRA_KEYWORDS[key].
- [S18-02] Баг create_triage — добавлен ShieldEffect(4, 6) в effects.
- [S18-03] EventView card reward — замена текста на модельку карты:
  GameManager.__init__: self.event_result_card = None.
  event_effects.py: сброс event_result_card в начале apply_effect; gain_card/gain_random_card сохраняют карту.
  EventView.py: импорт CardRenderer; рисует CardRenderer.draw при наличии event_result_card.

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
- VictoryScreen._show_modal — классовая переменная, сбрасывается в _proceed()
- CardRenderer.draw(player=None) — карта всегда доступна (can_afford=True)

## Известные нерешённые проблемы

- on_shield_gained, on_kill — заглушки, не подключены
- ПроклятаяКорона: пропуск gold reward не реализован
- Привязка карт к классам в CardLibraryView — TODO

## План Сессии 19

**Приоритет 1 — новый контент:**
1. Привязка карт к классам (Воин/Разбойник/Маг) в CardLibraryView и стартовых деках
2. ПроклятаяКорона: пропуск gold reward в distribute_combat_rewards

**Приоритет 2 — полировка:**
3. Хуки on_shield_gained, on_kill — подключить если нужны реликвии
4. Балансировка врагов и карт по результатам тестирования