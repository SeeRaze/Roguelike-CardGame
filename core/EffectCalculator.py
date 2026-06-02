class EffectCalculator:
    """Глобальный калькулятор боевой математики с учетом статусов и реликвий."""

    @staticmethod
    def calculate_damage(attacker, target, base_damage,
                         game_manager=None, combat_manager=None,
                         dry_run: bool = False):
        # 1. ТРИГГЕР РЕЛИКВИЙ
        if game_manager and hasattr(game_manager, 'relics'):
            for relic in game_manager.relics:
                base_damage = relic.on_damage_calculated(base_damage)

        # 2. ЯРОСТЬ атакующего: +X к базовому урону
        if attacker.strength > 0:
            if not dry_run:
                print(f" [ЯРОСТЬ] {attacker.name} добавляет +{attacker.strength} к урону!")
            base_damage += attacker.strength

        # 3. Слабость атакующего: урон режется на 25%
        if attacker.weak > 0:
            base_damage = int(base_damage * 0.75)

        final_damage = base_damage

        # 4. Уязвимость цели: урон вырастает на 50%
        if target.vulnerable > 0:
            final_damage = int(final_damage * 1.5)

        # 5. СТИХИЙНОЕ КОМБО: ПАР
        if target.wet > 0 and target.ignited > 0:
            final_damage = int(final_damage * 2.0)
            if not dry_run:
                # Снимаем статусы только при реальном ударе
                target.wet = max(0, target.wet - 1)
                target.ignited = max(0, target.ignited - 1)
                if combat_manager:
                    combat_manager.add_log_message("[!!! КОМБО: ПАР (х2.0) !!!]")

        return final_damage