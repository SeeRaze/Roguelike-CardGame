class EffectCalculator:

    # Бонус урона за один заряд Шока, расходуемый при ударе (см. шаг 6).
    SHOCK_DAMAGE_PER_STACK = 3

    # Множитель урона по цели с Расколом, ПОКА у неё есть щит (см. шаг 4b).
    SHATTER_MULT = 3.0

    @staticmethod
    def calculate_damage(attacker, target, base_damage,
                         game_manager=None, combat_manager=None,
                         dry_run: bool = False):
        # Определяем: игрок атакует или враг
        player = None
        if combat_manager:
            player = getattr(combat_manager, 'player', None)
        is_player_attack = (player is not None and attacker is player)

        # 1. ТРИГГЕР РЕЛИКВИЙ -- только для атак игрока
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

        # 2c. МАСТЕРСТВО СТИХИЙ (Маг): +N к урону за каждое комбо в этом бою
        if is_player_attack:
            mastery = getattr(attacker, 'mastery', 0)
            if mastery > 0:
                base_damage += mastery
                if not dry_run:
                    print(f" [МАСТЕРСТВО] +{mastery} к урону (стихийный резонанс).")

        # 2b. ПАССИВ БЕРСЕРКА: бонус урона от недостатка HP
        if is_player_attack and type(attacker).__name__ == "Berserker":
            if attacker.max_hp > 0:
                missing = 1.0 - attacker.hp / attacker.max_hp
                rage_bonus = int(missing * 10)
                if rage_bonus > 0:
                    base_damage += rage_bonus
                    if not dry_run:
                        print(f" [БЕРСЕРК] Ярость крови: +{rage_bonus} к урону "
                              f"({attacker.hp}/{attacker.max_hp} HP)")

        # 3. Слабость атакующего
        if attacker.weak > 0:
            base_damage = int(base_damage * 0.75)

        final_damage = base_damage

        # 4. Уязвимость цели
        if target.vulnerable > 0:
            final_damage = int(final_damage * 1.5)

        # 4b. РАСКОЛ цели — контра броне: пока у цели есть щит, урон ×SHATTER_MULT.
        # Множитель-ЧТЕНИЕ (заряды не тратятся, статус тикает по ходам). Условие
        # на щит проверяется в момент удара: при мульти-хите как только щит сбит,
        # последующие удары идут без бонуса.
        if target.shatter > 0 and target.shield > 0:
            final_damage = int(final_damage * EffectCalculator.SHATTER_MULT)
            if not dry_run and combat_manager:
                combat_manager.add_log_message(
                    f"[РАСКОЛ] Броня крошится: урон ×{EffectCalculator.SHATTER_MULT}!"
                )

        # 5. СТИХИЙНЫЕ КОМБО — data-driven реестр (core/ComboRegistry.py)
        # Множительные комбо: все requires-статусы >0 → ×multiplier, снять consume.
        from core.ComboRegistry import all_combos
        for combo_key, combo in all_combos().items():
            if all(getattr(target, req, 0) > 0
                   for req in combo["requires"]):
                final_damage = int(final_damage * combo["multiplier"])
                if not dry_run:
                    for req in combo["requires"]:
                        current = getattr(target, req, 0)
                        setattr(target, req, max(0, current - combo["consume"]))
                    if combat_manager:
                        combat_manager.add_log_message(combo["log"])
                        combat_manager._combo_triggered = True

        # 6. ШОК цели — флатовый разряд: +SHOCK_DAMAGE_PER_STACK за удар, −1 заряд.
        # Добавляется ПОСЛЕ множителей (уязвимость/комбо), чтобы оставаться плоским
        # и предсказуемым. Каждый отдельный удар (каждый DamageEffect карты) дренит
        # один заряд — отсюда синергия с мульти-хит/микро-атаками.
        if target.shock > 0:
            final_damage += EffectCalculator.SHOCK_DAMAGE_PER_STACK
            if not dry_run:
                target.shock = max(0, target.shock - 1)
                if combat_manager:
                    combat_manager.add_log_message(
                        f"[ШОК] Разряд: +{EffectCalculator.SHOCK_DAMAGE_PER_STACK} "
                        f"урона (зарядов осталось: {target.shock})."
                    )

        if not dry_run and game_manager and hasattr(game_manager, 'stats'):
            if final_damage > game_manager.stats.get("max_damage_dealt", 0):
                game_manager.stats["max_damage_dealt"] = final_damage

        return final_damage