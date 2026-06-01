class EffectCalculator:
    """Глобальный калькулятор боевой математики с учетом статусов и реликвий."""
    
    @staticmethod
    def calculate_damage(attacker, target, base_damage, game_manager=None, combat_manager=None):
        # 1. ТРИГГЕР РЕЛИКВИЙ: Модифицируем базу урона (например, Точильный Камень)
        if game_manager and hasattr(game_manager, 'relics'):
            for relic in game_manager.relics:
                base_damage = relic.on_damage_calculated(base_damage)

        # 2. Считаем Слабость атакующего (урон режется на 25%)
        if attacker.weak > 0:
            base_damage = int(base_damage * 0.75)
            
        final_damage = base_damage
        
        # 3. Считаем Уязвимость цели (урон вырастает на 50%)
        if target.vulnerable > 0:
            final_damage = int(final_damage * 1.5)
            
        # 4. --- ИСПРАВЛЕННОЕ СТИХИЙНОЕ КОМБО: ПАР ---
        # Проверяем наличие ОБОИХ статусов на ЖЕРТВЕ (target)
        if target.wet > 0 and target.ignited > 0:
            final_damage = int(final_damage * 2.0)  # Поднимем комбо-множитель до х2.0 для сочности!
            
            # Взрыв испаряет по одному ходу каждой стихии
            target.wet = max(0, target.wet - 1)
            target.ignited = max(0, target.ignited - 1)
            
            # Выводим сочное сообщение прямо на экран в историю действий!
            if combat_manager:
                combat_manager.add_log_message("[!!! КОМБО: ПАР (х2.0) !!!]")
            
        return final_damage
