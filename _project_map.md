# \# \_project\_map.md

# \# Последнее обновление: Jun 3, 2026 — Сессия 19

# 

# \## НАВИГАЦИЯ

# Читать ПЕРВЫМ в каждой сессии.

# Все файлы — ветка \*\*dev\*\*:

# https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу

# 

# \---

# 

# \## АРХИТЕКТУРА

# core/ -- вся логика

# 

# ui/ -- вся отрисовка

# 

# managers/ -- CombatManager, DeckManager, GameManager, MapGenerator, network\_manager

# 

# 

# \*\*Разрешение:\*\* строго 1920×1080 Full HD

# \*\*Лимит файла:\*\* 150 строк (золотой стандарт)

# \*\*Принцип:\*\* модульность, никаких "божественных объектов"

# 

# \---

# 

# \## ПОЛНЫЙ СПИСОК ФАЙЛОВ

# main.py, server.py, \_project\_map.md

# 

# core/rarity.py

# 

# core/Creature.py

# 

# core/EffectCalculator.py, core/StatusRegistry.py

# 

# core/cards/init.py, base.py, basic.py, fire.py, poison.py, water.py

# 

# core/cards/heal.py

# 

# core/cards/buff/init.py, strength.py, thorns.py, regen.py, vampirism.py

# 

# core/cards/debuff/init.py, vulnerable.py, weak.py, bleed.py

# 

# core/enemies/init.py, base.py, cultist.py, slime.py, boss.py

# 

# core/players/init.py, base.py, mage.py, rogue.py, warrior.py

# 

# core/relics/init.py, base.py, starter.py, elemental.py, advanced.py

# 

# managers/BalanceSimulator.py, CombatManager.py, DeckManager.py, GameManager.py, MapGenerator.py, network\_manager.py

# 

# ui/chest/init.py, base.py, common.py, locked.py, cursed.py, data.py, shared.py

# 

# ui/combat/init.py, hud.py

# 

# ui/events/init.py, event\_data.py, event\_effects.py, positive.py, negative.py, neutral.py, special.py

# 

# ui/Campfire.py, CardRenderer.py, CombatInterface.py

# 

# ui/CardLibraryView.py

# 

# ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py

# 

# ui/VictoryScreen.py

# 

# 

# \---

# 

# \## КЛЮЧЕВЫЕ СИСТЕМЫ

# 

# \*\*Creature.py\*\* -- базовый класс. `hp, shield, self.statuses={}` через `\_\_getattr\_\_/\_\_setattr\_\_`.

# \- `take\_damage(amount, attacker=None, combat\_manager=None)`

# \- `heal(amount, combat\_manager=None)`

# 

# \*\*StatusRegistry.py\*\* -- единый реестр 10 статусов:

# `vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire`

# 

# \*\*EffectCalculator.py\*\* -- единая точка боевой математики.

# \- `dry\_run=True` для превью

# \- Обновляет `gm.stats\["max\_damage\_dealt"]`

# \- Определяет `is\_player\_attack`, передаёт в `on\_damage\_calculated`

# 

# \*\*Реликвии -- хуки:\*\*

# `on\_combat\_start, on\_turn\_start, on\_damage\_calculated(base\_dmg, is\_player\_attack=True),`

# `on\_tick\_ignited, on\_wet\_applied, on\_card\_played, on\_shield\_gained (заглушка),`

# `on\_kill (заглушка), on\_combat\_end, on\_bleed\_tick, on\_heal, on\_chest\_opened`

# 

# \*\*Персонажи:\*\* Warrior (HP80), Rogue (HP65), Mage (HP55)

# \*\*Враги:\*\* Cultist, SlimeAndGoblins, BossTitan

# 

# \*\*Формулы врагов (тестовый режим):\*\*

# \- hp = 20 + floor×3 + tier×10

# \- dmg = 3 + tier×1

# \- shld = 2

# \- Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

# 

# \*\*Лидерборд:\*\* Google Apps Script, `threading.Thread daemon=True`

# 

# \---

# 

# \## РЕАЛИЗОВАННЫЕ СИСТЕМЫ

# 

# Все 14 пунктов плана масштабируемости (A-N) ВЫПОЛНЕНЫ.

# 

# \*\*Реликвии -- 17 штук:\*\*

# \- COMMON: LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок

# \- UNCOMMON: ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник

# \- RARE: ЭнергоЯдро, СердцеТитана, ГнилойКлык

# \- LEGENDARY: ПроклятаяКорона

# 

# \---

# 

# \## СЕССИЯ 19 (Jun 3, 2026)

# 

# \*\*\[S19-01] Цветовое кодирование карт -- рефакторинг CardRenderer.get\_card\_colors:\*\*

# \- Старая система: ключевые слова в названии (хрупко)

# \- Новая система: `\_classify\_card()` анализирует `card.effects` (надёжно)

# \- Новые импорты: `DamageEffect, ShieldEffect` из `core.cards.base`; `BuffEffect` из `core.cards.buff.strength`

# \- Палитра `\_C`: 13 классов с уникальными `bg+border`

# \- Классы: `attack\_pure` (красный), `bleed` (бордовый), `poison` (тёмно-зелёный), `fire` (оранжевый), `water` (синий), `vampire` (пурпурный), `heal` (светло-зелёный), `regen` (изумрудный), `shield` (стальной синий), `buff` (янтарный), `debuff` (фиолетовый), `attack\_mixed` (тёмно-красный), `default`

# \- Фон карты тонирован в цвет класса; при ховере +20 к каждому каналу

# 

# \*\*\[S19-02] Вампиризм переработан в статус-бафф:\*\*

# \- `"vampire"` добавлен в StatusRegistry (`is\_stack=True, is\_duration=False`)

# \- `Creature.take\_damage`: триггер при `amount>0` и `attacker.vampire>0` -- хил `max(1, amount//2)`, затем `vampire //= 2`

# \- `VampireBuffEffect` в `vampirism.py`: накладывает статус на игрока

# \- Карты: `DamageEffect + VampireBuffEffect`

# &#x20; - Высасывание: урон 6(9) + вампиризм +4(6)

# &#x20; - Кровавый Пир: урон 18(24) + вампиризм +10(15), изгнание

# &#x20; - Жизнеотвод: урон 4(6) + вампиризм +6(9)

# \- `VampireDamageEffect` в `base.py` -- deprecated stub, не использовать в новых картах

# \- CardRenderer: импорт `VampireBuffEffect`, обновлены `\_get\_card\_keywords` и `\_classify\_card`

# 

# \---

# 

# \## ВАЖНЫЕ ДЕТАЛИ

# 

# \- `on\_damage\_calculated(base\_dmg, is\_player\_attack=True)` -- ВСЕГДА проверять флаг в реликвиях

# \- `Creature.take\_damage` сигнатура: `(amount, attacker=None, combat\_manager=None)`

# \- `Creature.heal` сигнатура: `(amount, combat\_manager=None)`

# \- bleed: триггер в `take\_damage` при `amount>0`; сброс `=0` (без ГнилогоКлыка) или `//=2` (с ним)

# \- vampire: триггер в `take\_damage` при `amount>0` и `attacker.vampire>0`; хил `max(1, amount//2)`; `vampire //= 2`

# \- `VampireDamageEffect` -- DEPRECATED, не использовать

# \- `VampireBuffEffect` -- живёт в `core/cards/buff/vampirism.py`

# \- `distribute\_combat\_rewards()` → `pending\_rewards` → VICTORY

# \- CardLibraryView: новые карты в `NEW\_CARDS` без привязки к классу

# \- ПроклятаяКорона: gold reward пропуск -- НЕ реализован (отложено)

# \- `ui/chest/shared.py`: `draw\_card\_row` возвращает `(card, rect)` или `None` -- не ломать контракт

# \- `CardRenderer.draw` сигнатура: `(surface, card, x, y, font\_title, font\_desc, is\_hovered=False, player=None, enemy=None)` -- НЕ Rect!

# \- `\_EXTRA\_KEYWORDS` -- модульная переменная в `CardRenderer.py`, НЕ в StatusRegistry

# 

# \---

# 

# \## ВАЖНЫЕ ГРАБЛИ

# 

# \- Отступы Python сбиваются при копировании из чата -- всегда проверять

# \- `view.view.gm` -- двойной view это баг

# \- Pygame не поддерживает эмодзи в SysFont

# \- `pygame.display.flip()` -- один раз в конце `GameView.draw()`, НЕ в `draw\_screen` дочерних экранов

# \- `EventView.py` -- НЕ класс, только функции

# \- `self.relics` (не `self.player\_relics`!) в GameManager

# \- `tick\_statuses` принимает `combat\_manager=None` -- всегда передавать `self` из CombatManager

# \- `spawn\_procedural\_enemy` -- МЕТОД GameManager, не импортировать из `core.enemies`

# \- Все файлы читать из ветки \*\*DEV\*\*, не main

# \- `CombatManager.\_\_init\_\_` сигнатура: `(player, enemy, starting\_deck, game\_manager=None)`

# \- `RARITY\_COLORS` импортировать из `core.rarity`

# \- `on\_wet\_applied` -- через `Creature.add\_status`, НЕ напрямую

# \- `bonus\_draw` -- `getattr` с дефолтом 0

# \- `ui/chest/` -- маленькая c: `from ui.chest import ...`

# \- `VictoryScreen.\_show\_modal` -- классовая переменная, сбрасывается в `\_proceed()`

# \- `CardRenderer.draw(player=None)` -- карта всегда доступна (`can\_afford=True`)

# \- `\_classify\_card` импортирует `DamageEffect, ShieldEffect, BuffEffect` -- не забыть при рефакторинге

# 

# \---

# 

# \## ПЛАН СЕССИИ 20

# 

# \*\*Приоритет 1 -- новый контент:\*\*

# 1\. Привязка карт к классам (Воин/Разбойник/Маг) в CardLibraryView и стартовых деках

# 2\. ПроклятаяКорона: пропуск gold reward в `distribute\_combat\_rewards`

# 

# \*\*Приоритет 2 -- полировка:\*\*

# 3\. Хуки `on\_shield\_gained`, `on\_kill` -- подключить если нужны реликвии

# 4\. Балансировка врагов и карт по результатам тестирования

# 

# \---

# 

# \## СТАТУС

# 

# Сессия 19 завершена (Jun 3, 2026).

# Цветовое кодирование карт по типу эффектов + вампиризм как статус-бафф.

# Следующая стадия: привязка карт к классам + ПроклятаяКорона gold skip.

