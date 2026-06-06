"""Базовый класс реликвий + КОНТРАКТ РЕДКОСТИ (рамка калибровки артефактов).

Контракт редкости — единый ориентир при создании/балансе артефактов. Чтобы
понять, какую редкость дать новому артефакту, сверяйся с этой шкалой (сила
растёт сверху вниз; цены завязаны на редкость в ui/shop/data.py: 70/100/140/200/280):

  COMMON     — простой плоский стат или маленький разовый эффект; без условий
               синергии (напр. +10 щита в начале боя, +2 урона всем атакам).
  UNCOMMON   — условные/синергийные эффекты средней силы (привязка к стихии/
               статусу/событию: +урон за тик Горения, щит при наложении Мокрого).
  RARE       — сильные движки и билд-дефайнеры (генерация энергии, сустейн,
               внутрибоевой компаунд: +1 макс. энергия, хил % недостающего HP).
  EPIC       — масштабирование ПО ЗАБЕГУ (компаунд между боями; см.
               core/relics/advanced/persistent.py и [[balance-curve-framework]]).
  LEGENDARY  — меняет правила игры, обычно с трейдоффом (×2 урон ценой золота/удаления).
"""
from core.rarity import Rarity


class Relic:
    """
    Базовый класс для всех пассивных артефактов.

    Хуки вызываются из соответствующих систем:
      on_combat_start      <- CombatManager.__init__
      on_turn_start        <- CombatManager.start_turn_phase
      on_damage_calculated <- EffectCalculator.calculate_damage
      on_tick_ignited      <- Creature.tick_statuses
      on_wet_applied       <- Creature.add_status (key="wet")
      on_card_played       <- CombatManager.play_card_by_index
      on_shield_gained     <- Creature.gain_shield
      on_kill              <- CombatManager.end_turn_phase (заглушка)
      on_combat_end        <- GameManager.distribute_combat_rewards
      on_boss_defeated     <- GameManager.distribute_combat_rewards (только босс-этаж)
                              + managers/balance/runner.py (сим, босс-этаж)
      on_bleed_tick        <- Creature.take_damage (при bleed > 0)
      on_heal              <- Creature.heal (после фактического хила)
      on_chest_opened      <- ui/chest/common.py (при открытии сундука)
      activate             <- InputHandler (только для is_active=True реликвий)
    """

    def __init__(self, name: str, description: str,
                 rarity: Rarity = Rarity.COMMON):
        self.name        = name
        self.description = description
        self.rarity      = rarity
        self.is_active   = False

    # --- Пассивные хуки ---
    def on_combat_start(self, combat_manager):          pass
    def on_turn_start(self, combat_manager):            pass
    def on_damage_calculated(self, base_dmg, is_player_attack=True, dry_run=False):
        return base_dmg
    def on_tick_ignited(self, creature):                return 0
    def on_wet_applied(self, combat_manager):           pass
    def on_card_played(self, card, combat_manager):     pass
    def on_shield_gained(self, amount, creature, combat_manager=None): pass
    def on_kill(self, enemy, combat_manager):           pass
    def on_combat_end(self, player, combat_manager=None): pass
    def on_boss_defeated(self, player, combat_manager=None): pass
    def on_bleed_tick(self, bleed_dmg, creature,
                      combat_manager):                  return bleed_dmg
    def on_heal(self, healed_amount, creature):         pass
    def on_chest_opened(self, chest_type: str,
                        game_manager):                  pass

    # --- Активный хук (только для is_active=True) ---
    def activate(self, combat_manager) -> bool:
        """Вызывается из InputHandler при клике на активную реликвию.
        Возвращает True если активация прошла успешно, False иначе."""
        return False