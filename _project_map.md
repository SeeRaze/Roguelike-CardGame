# \# \_project\_map.md — Roguelike-CardGame

# > Последнее обновление: Сессия 23, Jun 3, 2026

# 

# \## Архитектура

# \- `core/` — вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py)

# \- `ui/` — вся отрисовка (CardRenderer.py, CombatInterface.py, GameView.py, HubView.py, MainMenu.py и др.)

# \- `managers/` — CombatManager, DeckManager, GameManager, MapGenerator, network\_manager

# \- Разрешение: строго 1920x1080 Full HD

# \- \*\*Ветка разработки: dev\*\* (main — стабильная, dev — активная работа)

# 

# \## Железные ГОСТы

# \- Лимит файла: 150 строк (золотой стандарт)

# \- Модульность и логичные зависимости — главный принцип

# \- Никаких "божественных объектов"

# 

# \## Навигация

# \- Читать этот файл ПЕРВЫМ в каждой сессии

# \- Большие файлы (GameManager.py, CombatInterface.py, GameView.py) — query\_context

# \- Все файлы из ветки dev: `https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу`

# 

# \## Полный список файлов (после Сессии 23)

# main.py, server.py, \_project\_map.md

# 

# core/rarity.py, core/Creature.py, core/EffectCalculator.py, core/StatusRegistry.py

# 

# core/cards/init.py, base.py, basic.py, fire.py, poison.py, water.py, heal.py

# 

# core/cards/buff/init.py, strength.py, thorns.py, regen.py, vampirism.py

# 

# core/cards/debuff/init.py, vulnerable.py, weak.py, bleed.py

# 

# core/enemies/init.py, base.py, cultist.py, slime.py, boss.py

# 

# core/players/init.py, base.py, mage.py, rogue.py, warrior.py, druid.py, berserker.py

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

# ui/Campfire.py, CardRenderer.py, CombatInterface.py, CardLibraryView.py

# 

# ui/EventView.py, GameView.py, HubView.py, InputHandler.py, LeaderboardView.py, MainMenu.py, MapView.py, Shop.py

# 

# ui/VictoryScreen.py

# 

# 

# \## Ключевые системы

# 

# \### Creature.py

# Базовый класс. `hp`, `shield`, `self.statuses={}` через `\_\_getattr\_\_`/`\_\_setattr\_\_`.

# \- `take\_damage(amount, attacker=None, combat\_manager=None)`

# \- `heal(amount, combat\_manager=None)`

# \- `gain\_shield(amount, combat\_manager=None)` — с хуком `on\_shield\_gained`

# 

# \### StatusRegistry.py

# Единый реестр всех 10 статусов: `vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire`

# 

# \### EffectCalculator.py

# Единая точка боевой математики. `dry\_run=True` для превью. Обновляет `gm.stats\["max\_damage\_dealt"]`.

# Пассив Берсерка: `бонус = int((1 - hp/max\_hp) \* 10)`, только `is\_player\_attack` и `type(attacker).\_\_name\_\_ == "Berserker"`.

# 

# \### Хуки реликвий

# `on\_combat\_start`, `on\_turn\_start`, `on\_damage\_calculated(base\_dmg, is\_player\_attack=True)`,

# `on\_tick\_ignited`, `on\_wet\_applied`, `on\_card\_played`,

# `on\_shield\_gained(amount, creature, combat\_manager=None)`,

# `on\_kill` (заглушка — до мульти-врагов),

# `on\_combat\_end`, `on\_bleed\_tick`, `on\_heal`, `on\_chest\_opened`

# 

# `on\_turn\_start` вызывается в `CombatManager.start\_turn\_phase` ПОСЛЕ сброса щита.

# 

# \### CombatManager

# \- `\_\_init\_\_(player, enemy, starting\_deck, game\_manager=None)`

# \- `start\_turn\_phase`: сохраняет `player.\_iron\_will\_shield` ДО сброса щита, затем вызывает `on\_turn\_start`

# \- Пассив Разбойника: `temp\_cost = max(0, original - 1)` на случайную карту в руке

# 

# \### Персонажи

# Warrior (HP80, E3), Rogue (HP65, E4), Mage (HP55, E3), Druid (HP70, E3), Berserker (HP60, E3)

# 

# Пассивки реализованы только у:

# \- \*\*Берсерк\*\*: бонус урона от недостающего HP

# \- \*\*Разбойник\*\*: temp\_cost -1 на случайную карту в руке

# 

# Warrior, Mage, Druid — пассивки запланированы (Сессия 24+)

# 

# \### Враги

# Cultist, SlimeAndGoblins, BossTitan

# 

# Формулы (тестовый режим):

# \- `hp = 20 + floor×3 + tier×10`, `dmg = 3 + tier×1`, `shld = 2`

# \- Босс: `hp×2.2`, `dmg×1.3`, `shld×1.8`, `shield=shld×2`

# 

# \## Реликвии (19 итого)

# 

# | Редкость | Реликвии |

# |---|---|

# | COMMON | LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок |

# | UNCOMMON | ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник, \*\*ШипастаяБроня\*\* |

# | RARE | ЭнергоЯдро, СердцеТитана, ГнилойКлык, \*\*ЖелезнаяВоля\*\* |

# | LEGENDARY | ПроклятаяКорона |

# 

# \*\*ШипастаяБроня\*\* (UNCOMMON): `on\_shield\_gained` → враг получает +1 Кровотечение

# \*\*ЖелезнаяВоля\*\* (RARE, АКТИВНАЯ): `is\_active=True`, `activate()` из InputHandler при клике. Один раз за бой — щит не сбрасывается в начале следующего хода. UI: `\[A]` префикс, золотой/серый по состоянию.

# 

# \## Изменения по сессиям

# 

# \### Сессия 23

# \- `CardRenderer`: `display\_cost = getattr(card, 'temp\_cost', card.cost)`, `COLOR\_COST\_DISC = (80,220,80)`

# \- `ПроклятаяКорона`: gold skip в `distribute\_combat\_rewards`

# \- `Creature.gain\_shield`: новая сигнатура `(amount, combat\_manager=None)` + хук `on\_shield\_gained`

# \- `ShieldEffect.execute`: передаёт `combat\_manager` в `gain\_shield`

# \- `SpikedBracelet`: передаёт `combat\_manager` в `gain\_shield`

# \- `CombatManager.start\_turn\_phase`: сохраняет `\_iron\_will\_shield` + вызывает `on\_turn\_start`

# \- Добавлены реликвии: ШипастаяБроня, ЖелезнаяВоля

# \- `InputHandler.\_handle\_combat`: клик по активной реликвии → `relic.activate()`

# \- `hud.draw\_relics`: активные реликвии с `\[A]` префиксом и состоянием готовности

# 

# \### Сессия 22

# \- BUG-01: дублирование наград — guard в InputHandler + первая строка distribute\_combat\_rewards

# 

# \### Сессия 17

# \- UI: Campfire/Shop EventView-стиль, FORGE/REMOVE full-screen, MainMenu тёмно-синяя тема

# \- Тултипы карт: Shop, Campfire, сундуки

# \- Исправлен баг скролла CARD\_LIBRARY

# 

# \## Важные грабли

# \- `gain\_shield` без `combat\_manager` → `on\_shield\_gained` не сработает

# \- Pygame не поддерживает эмодзи в SysFont → текстовые маркеры (`\[A]`)

# \- `view.view.gm` — двойной view это баг

# \- `pygame.display.flip()` — один раз в конце `GameView.draw()`

# \- `EventView.py` — НЕ класс, только функции

# \- `self.relics` (не `self.player\_relics`!) в GameManager

# \- `tick\_statuses` принимает `combat\_manager=None` — всегда передавать `self` из CombatManager

# \- `spawn\_procedural\_enemy` — МЕТОД GameManager, не импортировать из `core.enemies`

# \- `CombatManager.\_\_init\_\_`: `(player, enemy, starting\_deck, game\_manager=None)`

# \- `RARITY\_COLORS` импортировать из `core.rarity`

# \- `on\_wet\_applied` — через `Creature.add\_status`, НЕ напрямую

# \- `ui/chest/` — маленькая c: `from ui.chest import ...`

# \- `VictoryScreen.\_show\_modal` — классовая переменная, сбрасывается в `\_proceed()`

# \- `CardRenderer.draw(player=None)` — карта всегда доступна (`can\_afford=True`)

# \- `\_EXTRA\_KEYWORDS` — модульная переменная в `CardRenderer.py`, НЕ в StatusRegistry

# \- `draw\_pile\_rect` и `discard\_pile\_rect` — атрибуты GameView, не CombatInterface

# \- `VampireDamageEffect` — DEPRECATED stub, не использовать

# \- `random.shuffle` в тултипе стопки — НЕ вызывать каждый кадр

# 

# \## Правила работы

# \- Никогда не просить у пользователя отдельные файлы — брать из репо напрямую

# \- В конце каждой сессии — полный готовый текст `\_project\_map.md` для ручной вставки

# 

# \## План Сессии 24

# 1\. Тестирование ЖелезнойВоли и ШипастойБрони

# 2\. Пассивные врождённые механики: Warrior, Mage, Druid

# 3\. Балансировка по результатам тестирования

