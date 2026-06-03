# \# \_project\_map.md

# \# Актуально на Jun 3, 2026 -- после Сессии 21

# 

# \## АРХИТЕКТУРА

# 

# \- core/ -- вся логика (cards/, enemies/, players/, relics/, Creature.py, EffectCalculator.py, StatusRegistry.py)

# \- ui/ -- вся отрисовка (CardRenderer.py, CombatInterface.py, GameView.py, HubView.py, MainMenu.py и др.)

# \- managers/ -- CombatManager, DeckManager, GameManager, MapGenerator, network\_manager

# \- Разрешение: строго 1920x1080 Full HD

# \- \*\*Ветка разработки: dev\*\* (main -- стабильная, dev -- активная работа)

# 

# \## ЖЕЛЕЗНЫЕ ГОСТЫ

# 

# \- Лимит файла: 150 строк (золотой стандарт)

# \- Если файл разрастается -- рефакторинг и разбивка на модули

# \- Модульность и логичные зависимости -- главный принцип

# \- Никаких "божественных объектов"

# 

# \## НАВИГАЦИЯ

# 

# \- Читать этот файл ПЕРВЫМ в каждой сессии

# \- Большие файлы (GameManager.py, CombatInterface.py, GameView.py) -- использовать query\_context

# \- Все файлы читать из ветки dev: https://raw.githubusercontent.com/SeeRaze/Roguelike-CardGame/dev/путь/к/файлу

# 

# \## ПОЛНЫЙ СПИСОК ФАЙЛОВ (после Сессии 21)

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

# core/players/\_\_init\_\_.py, base.py, mage.py, rogue.py, warrior.py, druid.py, berserker.py

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

# \## КЛЮЧЕВЫЕ СИСТЕМЫ

# 

# \*\*Creature.py\*\* -- базовый класс. hp, shield, self.statuses={} через \_\_getattr\_\_/\_\_setattr\_\_.

# \- take\_damage(amount, attacker=None, combat\_manager=None)

# \- heal(amount, combat\_manager=None)

# 

# \*\*StatusRegistry.py\*\* -- единый реестр 10 статусов:

# vulnerable, weak, wet, ignited, poison, strength, thorns, regen, bleed, vampire

# 

# \*\*EffectCalculator.py\*\* -- единая точка боевой математики.

# \- dry\_run=True для превью

# \- Обновляет gm.stats\["max\_damage\_dealt"]

# \- Порядок: реликвии → ярость → пассив Берсерка → слабость → уязвимость → стихийное комбо

# \- Пассив Берсерка: бонус = int((1 - hp/max\_hp) \* 10), только is\_player\_attack + type=="Berserker"

# 

# \*\*Реликвии -- хуки:\*\*

# on\_combat\_start, on\_turn\_start, on\_damage\_calculated(base\_dmg, is\_player\_attack=True),

# on\_tick\_ignited, on\_wet\_applied, on\_card\_played, on\_shield\_gained (заглушка),

# on\_kill (заглушка), on\_combat\_end, on\_bleed\_tick, on\_heal, on\_chest\_opened

# 

# \*\*Лидерборд\*\* -- Google Apps Script, threading.Thread daemon=True

# 

# \## ПЕРСОНАЖИ (5 классов)

# 

# |

# &#x20;Класс     

# |

# &#x20;HP 

# |

# &#x20;Энергия 

# |

# &#x20;Фишка                              

# |

# |

# \-----------

# |

# \----

# |

# \---------

# |

# \------------------------------------

# |

# |

# &#x20;Warrior   

# |

# &#x20;80 

# |

# &#x20;3       

# |

# &#x20;Щиты, шипы, тяжёлый урон          

# |

# |

# &#x20;Rogue     

# |

# &#x20;65 

# |

# &#x20;4       

# |

# &#x20;Серии ударов, каждый ход -1 кост   

# |

# |

# &#x20;Mage      

# |

# &#x20;55 

# |

# &#x20;3       

# |

# &#x20;Стихийные комбо огонь+вода         

# |

# |

# &#x20;Druid     

# |

# &#x20;70 

# |

# &#x20;3       

# |

# &#x20;Реген, хил, медленный яд           

# |

# |

# &#x20;Berserker 

# |

# &#x20;60 

# |

# &#x20;3       

# |

# &#x20;Пассив: чем меньше HP -- тем больше урон 

# |

# 

# \## МЕХАНИКА РАЗБОЙНИКА (temp\_cost)

# 

# \- start\_turn\_phase: случайная карта в руке получает temp\_cost = max(0, cost-1)

# \- play\_card\_by\_index: читает getattr(card, 'temp\_cost', card.cost)

# \- После разыгрывания: del card.temp\_cost

# \- discard\_hand: удаляет temp\_cost у всех карт перед сбросом

# 

# \## ВРАГИ (тестовый режим)

# 

# \- hp = 20 + floor×3 + tier×10

# \- dmg = 3 + tier×1

# \- shld = 2

# \- Босс: hp×2.2, dmg×1.3, shld×1.8, shield=shld×2

# 

# \## РЕЛИКВИИ (17 штук)

# 

# COMMON: LuckyClover, SpikedBracelet, ТочильныйКамень, СтараяПиявка, СчастливаяМонетка, ЗасохшийКлевер, Заплатка, ЗаточенныйОсколок

# UNCOMMON: ДревнееОгниво, НамокшаяРукавица, ОкровавленныйШприц, ФлаконСЖелчью, СвинцовыйНабалдашник

# RARE: ЭнергоЯдро, СердцеТитана, ГнилойКлык

# LEGENDARY: ПроклятаяКорона

# 

# \## ВАЖНЫЕ ДЕТАЛИ

# 

# \- on\_damage\_calculated(base\_dmg, is\_player\_attack=True) -- ВСЕГДА проверять флаг в реликвиях

# \- bleed: триггер в take\_damage при amount>0; сброс =0 (без ГнилогоКлыка) или //=2 (с ним)

# \- vampire: триггер в take\_damage при amount>0 и attacker.vampire>0; хил max(1, amount//2); vampire //= 2

# \- VampireDamageEffect: DEPRECATED stub в base.py, не использовать

# \- VampireBuffEffect: живёт в core/cards/buff/vampirism.py

# \- distribute\_combat\_rewards() → pending\_rewards → VICTORY

# \- ПроклятаяКорона: gold reward пропуск -- НЕ реализован (отложено)

# \- ui/chest/shared.py: draw\_card\_row возвращает (card, rect) или None -- не ломать контракт

# \- CardRenderer.draw сигнатура: (surface, card, x, y, font\_title, font\_desc, is\_hovered=False, player=None, enemy=None) -- НЕ Rect!

# \- \_EXTRA\_KEYWORDS -- в CardRenderer.py, НЕ в StatusRegistry

# \- draw\_pile\_rect и discard\_pile\_rect -- атрибуты GameView, не CombatInterface

# \- \_draw\_pile\_display кешируется в GameView по \[id(c) for c in dm.draw\_pile]

# 

# \## ВАЖНЫЕ ГРАБЛИ

# 

# \- Отступы Python сбиваются при копировании из чата -- всегда проверять

# \- view.view.gm -- двойной view это баг

# \- Pygame не поддерживает эмодзи в SysFont

# \- pygame.display.flip() -- один раз в конце GameView.draw()

# \- EventView.py -- НЕ класс, только функции

# \- self.relics (не self.player\_relics!) в GameManager

# \- tick\_statuses принимает combat\_manager=None -- всегда передавать self из CombatManager

# \- spawn\_procedural\_enemy -- МЕТОД GameManager, не импортировать из core.enemies

# \- CombatManager.\_\_init\_\_ сигнатура: (player, enemy, starting\_deck, game\_manager=None)

# \- RARITY\_COLORS импортировать из core.rarity

# \- on\_wet\_applied -- через Creature.add\_status, НЕ напрямую

# \- bonus\_draw -- getattr с дефолтом 0

# \- ui/chest/ -- маленькая c: from ui.chest import ...

# \- VictoryScreen.\_show\_modal -- классовая переменная, сбрасывается в \_proceed()

# \- play\_card\_by\_index был вложен сам в себя (дубль) -- исправлено в Сессии 21

# 

# \## ПЛАН СЕССИИ 22

# 

# \*\*Приоритет 1 -- аудит после расширения классов:\*\*

# 1\. Проверить все импорты стартовых дек (druid, berserker) в core/cards/\_\_init\_\_.py

# 2\. Проверить HubView -- 5 кнопок с gap=260, start\_x=100: 100+4×260=1140px, влезает

# 3\. CardRenderer -- отображать temp\_cost вместо cost (подсветить зелёным если дешевле)

# 

# \*\*Приоритет 2 -- новый контент:\*\*

# 4\. ПроклятаяКорона: пропуск gold reward в distribute\_combat\_rewards

# 5\. Хуки on\_shield\_gained, on\_kill -- подключить если нужны реликвии

# 6\. Балансировка врагов и карт

# 

# \## СТАТУС

# 

# Сессия 21 завершена (Jun 3, 2026).

# Расширена система классов с 3 до 5: Друид (реген/хил/яд) и Берсерк (пассив %HP→урон).

# Разбойник переработан: энергия 4 + механика temp\_cost.

# CardLibraryView: 6 вкладок. HubView обновлён.

# Исправлен дубль play\_card\_by\_index в CombatManager.

# Следующая стадия: аудит импортов + отображение temp\_cost в CardRenderer.

