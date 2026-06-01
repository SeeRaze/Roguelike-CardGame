import pygame

class CombatInterface:
    """Отрисовщик боевого экрана под разрешение 1920x1080 с выводом Реликвий."""
    
    @staticmethod
    def draw_hp_bar(screen, x, y, width, height, current_hp, max_hp, shield):
        pygame.draw.rect(screen, (40, 40, 40), (x, y, width, height))
        hp_percent = max(0, min(current_hp / max_hp, 1))
        fill_width = int(width * hp_percent)
        if fill_width > 0:
            pygame.draw.rect(screen, (70, 200, 70), (x, y, fill_width, height))
        if shield > 0:
            shield_percent = min(shield / max_hp, 1)
            shield_width = int(width * shield_percent)
            pygame.draw.rect(screen, (70, 160, 240), (x, y, shield_width, 8))
        pygame.draw.rect(screen, (200, 200, 200), (x, y, width, height), 1)

    @staticmethod
    def draw_combat_screen(view):
        view.screen.fill((30, 30, 30))
        WHITE, RED, GREEN, BLUE, YELLOW, GRAY = (255,255,255), (240,70,70), (70,240,70), (70,160,240), (240,240,70), (150,150,150)
        
        combat = view.gm.active_combat
        enemy = combat.enemy
        player = combat.player
        dm = combat.deck_manager
        
        # --- НОВОЕ: ВЫВОД СУМКИ РЕЛИКВИЙ (В САМЫЙ ВЕРХ СЛЕВА) ---
        view.draw_text("АРТЕФАКТЫ:", view.card_font, YELLOW, 100, 20)
        if hasattr(view.gm, 'relics'):
            for r_idx, relic in enumerate(view.gm.relics):
                # Выводим их списком в строчку через запятую или лесенкой
                view.draw_text(f"[{relic.name}]", view.card_desc_font, WHITE, 250 + r_idx * 180, 23)

        # 1. ИНТЕРФЕЙС ВРАГА ( Full HD сдвиг)
        view.draw_text(f"ВРАГ: {enemy.name}", view.main_font, WHITE, 100, 70)
        if enemy.hp > 0:
            CombatInterface.draw_hp_bar(view.screen, 100, 120, 500, 25, enemy.hp, enemy.max_hp, enemy.shield)
            shield_str = f" (+{enemy.shield} Щит)" if enemy.shield > 0 else ""
            view.draw_text(f"HP: {enemy.hp}/{enemy.max_hp}{shield_str}", view.card_font, RED, 100, 155)
            if enemy.intent_type:
                view.draw_text(f"НАМЕРЕНИЕ: {enemy.intent_type.upper()} на {enemy.intent_value}", view.main_font, YELLOW, 100, 195)
            view.draw_text(f"Статусы: Уязв:{enemy.vulnerable} Слаб:{enemy.weak} Мокр:{enemy.wet} Гор:{enemy.ignited}", view.ui_font, GRAY, 100, 245)
        else:
            view.draw_text(" [!!!] ВРАГ ПОВЕРЖЕН! КЛИКНИТЕ ДЛЯ СЛЕДУЮЩЕГО ЭТАЖА [!!!]", view.main_font, GREEN, 100, 120)
        
        view.draw_text("-" * 120, view.ui_font, GRAY, 100, 290)
        
        # 2. ИНТЕРФЕЙС ИГРОКА ( Full HD сдвиг)
        view.draw_text("ИГРОК: Вы", view.main_font, WHITE, 100, 330)
        CombatInterface.draw_hp_bar(view.screen, 100, 380, 500, 25, player.hp, player.max_hp, player.shield)
        player_shield_str = f" (+{player.shield} Щит)" if player.shield > 0 else ""
        view.draw_text(f"HP: {player.hp}/{player.max_hp}{player_shield_str}", view.card_font, GREEN, 100, 415)
        
        # Энергия (Красивые синие Full HD сферы)
        view.draw_text("Энергия: ", view.main_font, BLUE, 100, 460)
        for i in range(player.max_energy):
            sphere_x = 270 + i * 45  # Было 240 + i * 40
            sphere_y = 480
            if i < player.energy: 
                pygame.draw.circle(view.screen, BLUE, (sphere_x, sphere_y), 15)
            else: 
                pygame.draw.circle(view.screen, (50, 50, 60), (sphere_x, sphere_y), 15, 2)
                
        view.draw_text(f"Золото: {view.gm.player_gold} монет", view.main_font, YELLOW, 450, 460)
        view.draw_text(f"Статусы:  Уязв:{player.vulnerable} Слаб:{player.weak}", view.ui_font, GRAY, 100, 510)
        
        view.draw_text("=" * 100, view.ui_font, WHITE, 100, 570)
        
        # 3. ДИНАМИЧЕСКИЙ ВЕЕР КАРТ (ИСПРАВЛЕНО!)
        hand_size = len(dm.hand)
        view.draw_text(f"Колода: {len(dm.draw_pile)} шт.", view.main_font, YELLOW, 100, 600)
        view.draw_text(f"Сброс: {len(dm.discard_pile)} шт.", view.main_font, GRAY, 1600, 600)
        
        for index, card in enumerate(dm.hand):
            # Вызываем метод центрирования из GameView!
            card_x = view.calculate_card_x(index, hand_size)
            card_y = view.base_y
            if index == view.hovered_card_index: card_y = view.base_y - 40 # Вылетает выше под крупный размер
            view.draw_card_by_data(card, card_x, card_y)
            
        # 4. КНОПКА КОНЦА ХОДА
        btn_color = (90, 90, 95) if view.is_end_turn_hovered else (60, 60, 60)
        pygame.draw.rect(view.screen, btn_color, view.end_turn_rect)
        pygame.draw.rect(view.screen, WHITE, view.end_turn_rect, 2)
        view.draw_text("КОНЕЦ ХОДА", view.card_font, WHITE, view.end_turn_rect.x + 45, view.end_turn_rect.y + 18)
        
        # 5. БОЕВОЙ ЛОГ (Сдвинут в правый верхний угол Full HD экрана)
        log_x, log_y = 1400, 70
        log_rect = pygame.Rect(log_x - 15, log_y - 15, 420, 220)
        pygame.draw.rect(view.screen, (20, 20, 20), log_rect)
        pygame.draw.rect(view.screen, GRAY, log_rect, 1)
        view.draw_text("ИСТОРИЯ ДЕЙСТВИЙ:", view.card_font, YELLOW, log_x, log_y)
        for log_index, message in enumerate(combat.combat_log):
            view.draw_text(message, view.card_desc_font, WHITE, log_x, log_y + 35 + log_index * 26)
