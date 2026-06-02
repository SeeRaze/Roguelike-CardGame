import random
from core.players.warrior import Warrior
from core.players.rogue   import Rogue
from core.players.mage    import Mage
from core.enemies.cultist import Cultist
from managers.CombatManager import CombatManager


class BotCombatManager(CombatManager):
    """CombatManager без ручного ввода."""

    def run_bot_loop(self):
        """Прогоняет бой до конца. Вызывается после __init__."""
        while self.player.hp > 0 and self.enemy.hp > 0:
            # Ход игрока: разыгрываем карты
            while True:
                hand = self.deck_manager.hand
                if not hand:
                    break
                playable = [c for c in hand if self.player.energy >= c.cost]
                if not playable:
                    break
                card = random.choice(playable)
                self.player.use_energy(card.cost)
                card.apply(self.player, self.enemy, self)
                hand.remove(card)
                self.deck_manager.discard_pile.append(card)
                if self.enemy.hp <= 0:
                    return
            # Конец хода
            self.end_turn_phase()


def run_simulation(player_class=Warrior, number_of_runs=500,
                   enemy_hp=60, enemy_dmg=8, enemy_shld=3):
    print(f"=== {player_class.__name__} × {number_of_runs} боев ===")

    wins = losses = total_turns = leftover_hp = 0

    import builtins
    _print = builtins.print
    builtins.print = lambda *a, **kw: None

    for _ in range(number_of_runs):
        player = player_class()
        deck   = player.get_starter_deck()
        enemy  = Cultist(name="Тест", hp=enemy_hp, max_hp=enemy_hp)
        enemy.base_test_damage = enemy_dmg
        enemy.base_test_shield = enemy_shld

        combat = BotCombatManager(player, enemy, deck, game_manager=None)
        combat.run_bot_loop()

        total_turns += combat.turn_count
        if player.hp > 0:
            wins        += 1
            leftover_hp += player.hp
        else:
            losses += 1

    builtins.print = _print

    win_rate  = wins / number_of_runs * 100
    avg_turns = total_turns / number_of_runs
    avg_hp    = leftover_hp / wins if wins > 0 else 0

    print(f"  Побед:     {wins} ({win_rate:.1f}%)")
    print(f"  Поражений: {losses} ({100 - win_rate:.1f}%)")
    print(f"  Ср. ходов: {avg_turns:.1f}")
    print(f"  Ср. HP:    {avg_hp:.1f} / {player_class().max_hp}")
    print("=" * 40)


if __name__ == "__main__":
    for cls in [Warrior, Rogue, Mage]:
        run_simulation(cls, number_of_runs=500)