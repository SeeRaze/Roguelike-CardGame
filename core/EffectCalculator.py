class EffectCalculator:

    @staticmethod
    def calculate_damage(attacker, target, base_damage,
                         game_manager=None, combat_manager=None,
                         dry_run: bool = False):
        # Определяем: игрок атакует или враг
        player = None
        if combat_manager:
            player = getattr(combat_manager, 'player', None)
        is_player_attack = (player is not None and attacker is player)

        # 1. ТРИГГЕР РЕЛИКВИЙ — только для атак игрока
        if game_manager and hasattr(game_manager, 'relics'):
            for relic in game_manager.relics:
                base_damage = relic.on_damage_calculated(
                    base_damage, is_player_attack
                )

        # 2. ЯРОСТЬ атакующего
        if attacker.strength > 0:
            if not dry_run:
                print(f" [ЯРОСТЬ] {attacker.name} добавляет "
                      f"+{attacker.strength} к урону!")
            base_damage += attacker.strength

        # 3. Слабость атакующего
        if attacker.weak > 0:
            base_damage = int(base_damage * 0.75)

        final_damage = base_damage

        # 4. Уязвимость цели
        if target.vulnerable > 0:
            final_damage = int(final_damage * 1.5)

        # 5. СТИХИЙНОЕ КОМБО: ПАР
        if target.wet > 0 and target.ignited > 0:
            final_damage = int(final_damage * 2.0)
            if not dry_run:
                target.wet     = max(0, target.wet - 1)
                target.ignited = max(0, target.ignited - 1)
                if combat_manager:
                    combat_manager.add_log_message("[!!! КОМБО: ПАР (х2.0) !!!]")

        if not dry_run and game_manager and hasattr(game_manager, 'stats'):
            if final_damage > game_manager.stats.get("max_damage_dealt", 0):
                game_manager.stats["max_damage_dealt"] = final_damage

        return final_damage