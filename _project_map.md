# \# \_project\_map.md

# \# Читать ПЕРВЫМ в каждой сессии. Актуально на Jun 3, 2026 -- после Сессии 20.

# 

# === АРХИТЕКТУРА ===

# 

# \- core/       -- вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py)

# \- ui/         -- вся отрисовка (CardRenderer.py, CombatInterface.py, GameView.py, HubView.py, MainMenu.py и др.)

# \- managers/   -- CombatManager, DeckManager, GameManager, MapGenerator, network\_manager

# \- Разрешение: строго 1920x1080 Full HD

# \- Ветка разработки: dev (main -- стабильная, dev -- активная работа)

# 

# Железные ГОСТы:

# \- Лимит файла: 150 строк (золотой стандарт, выбиваться нежелательно)

# \- Если файл разрастается -- рефакторинг и разбивка на модули

# \- Модульность и логичные зависимости -- главный принцип

# \- Никаких "божественных объектов"

# 

# === НАВИГАЦИЯ ===

# 

# \- В корне репо лежит \_project\_map.md -- читать ПЕРВЫМ в каждой сессии

# \- URL: https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/\_project\_map.md

# \- Большие файлы (GameManager.py, CombatInterface.py, GameView.py) -- использовать query\_context

# \- Остальные файлы читаются за один запрос напрямую

# \- Все файлы читать из ветки dev: https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу

# 

# === КЛЮЧЕВЫЕ СИСТЕМЫ ===

# 

# \- Creature.py -- базовый класс (hp, shield, self.statuses={} через \_\_getattr\_\_/\_\_setattr\_\_).

# &#x20; take\_damage(amount, attacker=None, combat\_manager=None). heal(amount, combat\_manager=None).

# \- StatusRegistry.py -- единый реестр всех 10 статусов:

# &#x20; vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire

# \- EffectCalculator.py -- единая точка боевой математики. dry\_run=True для превью.

# &#x20; Обновляет gm.stats\["max\_damage\_dealt"]. Определяет is\_player\_attack, передаёт в on\_damage\_calculated.

# \- Реликвии через хуки: on\_combat\_start, on\_turn\_start, on\_damage\_calculated(base\_dmg, is\_player\_attack=True),

# &#x20; on\_tick\_ignited, on\_wet\_applied, on\_card\_played, on\_shield\_gained (заглушка), on\_kill (заглушка),

# &#x20; on\_combat\_end, on\_bleed\_tick, on\_heal, on\_chest\_opened

# \- Лидерборд через Google Apps Script (асинхронный фоновый поток, threading.Thread daemon=True)

# \- Персонажи: Warrior (HP80), Rogue (HP65), Mage (HP55)

# \- Враги: Cultist, SlimeAndGoblins, BossTitan

# 

# Формулы врагов (тестовый режим):

# \- hp = 20 + floor×3 + tier×10

# \- dmg = 3 + tier×1

# \- shld = 2

# \- Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

# 

# === ПОЛНЫЙ СПИСОК ФАЙЛОВ ===

# 

# main.py, server.py, \_project\_map.md

# core/rarity.py

# core/Creature.py

# core/EffectCalculator.py, core/StatusRegistry.py

# core/cards/\_\_init\_\_.py, base.py, basic.py, fire.py, poison.py, water.py

# core/cards/heal.py

# core/cards/buff/\_\_init\_\_.py, strength.py, thorns.py, regen.py, vampirism.py

# core/cards/debuff/\_\_init\_\_.py, vulnerable.py, weak.py, bleed.py

# core/enemies/\_\_init\_\_.py, base.py, cultist.py, slime.py, boss.py

# core/players/\_\_init\_\_.py, base.py, mage.py, rogue.py, warrior.py

# core/relics/\_\_init\_\_.py, base.py, starter.py, elemental.py, advanced.py

# managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py, MapGenerator.py, network\_manager.py

# ui/chest/\_\_init\_\_.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py

# ui/combat/\_\_init\_\_.py, hud.py

# ui/events/\_\_init\_\_.py, event\_data.py, event\_effects.py, positive.py, negative.py, neutral.py, special.py

# ui/Campfire.py, CardRenderer.py, CombatInterface.py

# ui/CardLibraryView.py

# ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py

# ui/VictoryScreen.py

# 

# === РЕАЛИЗОВАННЫЕ СИСТЕМЫ (после Сессии 20) ===

# 

# Все 14 пунктов плана масштабируемости (A-N) ВЫПОЛНЕНЫ.

# 

# Реликвии -- 17 итого:

# COMMON:    LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка,

# &#x20;          СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок

# UNCOMMON:  ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник

# RARE:      ЭнергоЯдро, СердцеТитана, ГнилойКлык

# LEGENDARY: ПроклятаяКорона

# 

# === ВЫПОЛНЕНО В СЕССИИ 19 ===

# 

# \[S19-01] Цветовое кодирование карт -- полный рефакторинг CardRenderer.get\_card\_colors:

# \- Новая система: \_classify\_card() анализирует эффекты карты (надёжно)

# \- Палитра \_C: 13 классов карт с уникальными bg+border цветами

# \- Классы: attack\_pure, bleed, poison, fire, water, vampire, heal, regen,

# &#x20; shield, buff, debuff, attack\_mixed, default

# \- При ховере фон осветляется на +20 к каждому каналу

# 

# \[S19-02] Вампиризм переработан в статус-бафф:

# \- "vampire" добавлен в StatusRegistry (стекающий, is\_stack=True, is\_duration=False)

# \- Creature.take\_damage: триггер вампиризма атакующего при amount>0 -- хил max(1, amount//2), затем vampire //= 2

# \- VampireBuffEffect в vampirism.py: накладывает статус на игрока

# \- Карты: Высасывание (урон 6(9) + вампиризм +4(6)), Кровавый Пир (урон 18(24) + вампиризм +10(15), изгнание),

# &#x20; Жизнеотвод (урон 4(6) + вампиризм +6(9))

# \- VampireDamageEffect в base.py -- DEPRECATED stub, не использовать в новых картах

# 

# === ВЫПОЛНЕНО В СЕССИИ 20 ===

# 

# \[S20-01] Стопки карт в боевом экране -- визуальные рубашки с числом карт:

# \- draw\_pile\_rect    = Rect(60,  820, 120, 160) -- левый нижний угол

# \- discard\_pile\_rect = Rect(1740, 820, 120, 160) -- правый нижний угол

# \- CombatInterface.\_draw\_pile(): тёмный фон + рамка цвета метки + сетка-узор + число по центру + подпись снизу

# \- Заменили текстовые строки "Колода: N шт." / "Сброс: N шт."

# 

# \[S20-02] Hover-превью стопок:

# \- HoverState.pile\_type: Optional\[str] = None -- "draw" | "discard" | None

# \- CombatHUD.draw\_pile\_tooltip() -- тултип со списком карт, всплывает вверх над стопкой

# \- Добор: рандомный порядок (не раскрывает реальный). Сброс: reversed(discard\_pile) -- последний сброшенный первым

# 

# \[S20-03] Кеш перемешанного порядка добора:

# \- GameView.\_draw\_pile\_display: list -- перемешанная копия для тултипа

# \- GameView.\_draw\_pile\_ids: list -- id карт последнего известного добора

# \- GameView.\_refresh\_draw\_pile\_display() -- пересчёт только при изменении состава

# \- Сравнение по \[id(c) for c in dm.draw\_pile] -- стабильно между кадрами

# 

# \[S20-04] Флаг reveal\_draw\_order для будущей реликвии:

# \- gm.reveal\_draw\_order = True -- показывает реальный порядок добора в тултипе

# \- По умолчанию отсутствует, getattr(view.gm, 'reveal\_draw\_order', False)

# 

# === UI-УЛУЧШЕНИЯ (Сессия 17) ===

# 

# \[UI-01] Campfire/Shop -- EventView-стиль: тёмные панели, border-radius, hover-эффекты

# \[UI-02] FORGE/REMOVE панели -- full-screen (W-80 × H-40), 7 карт/ряд, clip\_rect + scroll

# \[UI-03] MainMenu -- тёмно-синяя тема, центрированная панель, divider

# \[UI-04] InputHandler -- исправлен баг скролла CARD\_LIBRARY

# \[UI-05] Тултипы карт добавлены: Shop MAIN, Shop REMOVE, Campfire FORGE

# \[UI-06] Тултип реликвии добавлен в VictoryScreen

# \[UI-07] Тултипы карт в сундуках: shared.draw\_card\_row возвращает (card, rect) или None

# 

# === ВАЖНЫЕ ДЕТАЛИ ===

# 

# \- on\_damage\_calculated(base\_dmg, is\_player\_attack=True) -- ВСЕГДА проверять флаг в реликвиях

# \- Creature.take\_damage: (amount, attacker=None, combat\_manager=None)

# \- Creature.heal: (amount, combat\_manager=None)

# \- bleed: триггер в take\_damage при amount>0; сброс =0 (без ГнилогоКлыка) или //=2 (с ним)

# \- vampire: триггер в take\_damage при amount>0 и attacker.vampire>0; хил max(1, amount//2); vampire //= 2

# \- VampireDamageEffect -- DEPRECATED stub в base.py, не использовать

# \- VampireBuffEffect -- живёт в core/cards/buff/vampirism.py

# \- distribute\_combat\_rewards() → pending\_rewards → VICTORY

# \- CardLibraryView: новые карты в NEW\_CARDS без привязки к классу

# \- ПроклятаяКорона: gold reward пропуск -- НЕ реализован (отложено)

# \- ui/chest/shared.py: draw\_card\_row возвращает (card, rect) или None -- не ломать контракт

# \- CardRenderer.draw: (surface, card, x, y, font\_title, font\_desc, is\_hovered=False, player=None, enemy=None) -- НЕ Rect!

# \- \_EXTRA\_KEYWORDS -- модульная переменная в CardRenderer.py, НЕ в StatusRegistry

# \- draw\_pile\_rect и discard\_pile\_rect -- атрибуты GameView, не CombatInterface

# \- \_draw\_pile\_display кешируется в GameView, обновляется по \[id(c) for c in dm.draw\_pile]

# 

# === ВАЖНЫЕ ГРАБЛИ ===

# 

# \- Отступы Python сбиваются при копировании из чата -- всегда проверять

# \- view.view.gm -- двойной view это баг

# \- Pygame не поддерживает эмодзи в SysFont

# \- pygame.display.flip() -- один раз в конце GameView.draw(), НЕ в draw\_screen дочерних экранов

# \- EventView.py -- НЕ класс, только функции

# \- self.relics (не self.player\_relics!) в GameManager

# \- tick\_statuses принимает combat\_manager=None -- всегда передавать self из CombatManager

# \- spawn\_procedural\_enemy -- МЕТОД GameManager, не импортировать из core.enemies

# \- Все файлы читать из ветки DEV, не main

# \- CombatManager.\_\_init\_\_: (player, enemy, starting\_deck, game\_manager=None)

# \- RARITY\_COLORS импортировать из core.rarity

# \- on\_wet\_applied -- через Creature.add\_status, НЕ напрямую

# \- bonus\_draw -- getattr с дефолтом 0

# \- ui/chest/ -- маленькая c: from ui.chest import ...

# \- VictoryScreen.\_show\_modal -- классовая переменная, сбрасывается в \_proceed()

# \- CardRenderer.draw(player=None) -- карта всегда доступна (can\_afford=True)

# \- \_classify\_card импортирует DamageEffect, ShieldEffect, BuffEffect -- не забыть при рефакторинге

# \- random.shuffle в тултипе стопки -- НЕ вызывать каждый кадр, только при изменении состава

# 

# === ПЛАН СЛЕДУЮЩЕЙ СЕССИИ (Сессия 21) ===

# 

# Приоритет 1 -- новый контент:

# 1\. Привязка карт к классам (Воин/Разбойник/Маг) в CardLibraryView и стартовых деках

# 2\. ПроклятаяКорона: пропуск gold reward в distribute\_combat\_rewards

# 

# Приоритет 2 -- полировка:

# 3\. Хуки on\_shield\_gained, on\_kill -- подключить если нужны реликвии

# 4\. Балансировка врагов и карт по результатам тестирования

# 

# === СТАТУС ===

# 

# Сессия 20 завершена (Jun 3, 2026).

# Добавлены визуальные стопки добора/сброса с hover-превью.

# Порядок добора рандомизируется при изменении состава (кеш по id карт).

# Флаг reveal\_draw\_order готов для будущей реликвии.

# Следующая стадия: привязка карт к классам + ПроклятаяКорона gold skip.

