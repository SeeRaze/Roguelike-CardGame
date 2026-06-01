import pygame

class MapView:
    """Отрисовщик процедурной карты без эмодзи-квадратов под Full HD."""
    is_left_hovered = False
    is_right_hovered = False

    @staticmethod
    def clean_name(room_type):
        """Переводчик технических строк в понятный геймерский текст."""
        if isinstance(room_type, list):
            room_type = room_type[0]
            
        if room_type == "COMBAT": return "[МЕЧ] Битва"
        if room_type == "CAMPFIRE": return "[КОСТЕР] Привал"
        if room_type == "SHOP": return "[МОНЕТА] Торговец"
        return room_type

    @staticmethod
    def draw_map(view):
        WHITE = (255, 255, 255)
        YELLOW = (240, 240, 70)
        GRAY = (120, 120, 120)
        GREEN = (70, 240, 70)
        
        view.screen.fill((20, 20, 20))
        mouse_pos = pygame.mouse.get_pos()
        
        # Локальный шаг внутри 10-этажного яруса
        local_step = (view.gm.current_floor - 1) % 10 + 1
        
        view.draw_text("=== ПРОГРЕСС ВОСХОЖДЕНИЯ ПО БАШНЕ ===", view.main_font, WHITE, 100, 50)
        view.draw_text(f"Глобальный этаж: {view.gm.current_floor}  |  Шаг яруса: {local_step} / 10", view.ui_font, YELLOW, 100, 100)
        view.draw_text(f"Ваше золото: {view.gm.player_gold} з.", view.main_font, YELLOW, 1400, 50)
        
        # 1. ОТРИСОВКА СЕТКИ ЭТАЖЕЙ
        for idx, floor_rooms in enumerate(view.gm.procedural_map):
            row_num = idx + 1
            display_y = 170 + idx * 45
            
            if row_num < local_step: color, status_str = GRAY, "[ПРОЙДЕНО]"
            elif row_num == local_step: color, status_str = GREEN, "[ВЫ ЗДЕСЬ]"
            else: color, status_str = WHITE, "[ПРЕДСТОИТ]"
                
            if row_num == 10:
                view.draw_text(f"Этап {row_num} {status_str}:  *** [ ЛОГОВО ГЛАВНОГО БОССА ЯРУСА ] ***", view.ui_font, color, 100, display_y)
            elif row_num == 9:
                view.draw_text(f"Этап {row_num} {status_str}:  [КОСТЕР] Отдых  или  [МОНЕТА] Магазин Торговца", view.ui_font, color, 100, display_y)
            else:
                name_a = MapView.clean_name(floor_rooms[0])
                name_b = MapView.clean_name(floor_rooms[1])
                view.draw_text(f"Этап {row_num} {status_str}:  Ветвь А: {name_a}  |  Ветвь Б: {name_b}", view.ui_font, color, 100, display_y)

        view.draw_text("=" * 100, view.ui_font, WHITE, 100, 680)
        view.draw_text("ВЫБЕРИТЕ СЛЕДУЮЩИЙ ПУТЬ РАЗВИТИЯ:", view.main_font, YELLOW, 100, 720)

        # 2. КНОПКИ ВЫБОРА ВЕТКИ
        current_options = view.gm.procedural_map[local_step - 1]
        type_left = current_options[0] if isinstance(current_options, list) else current_options
        type_right = current_options[1] if isinstance(current_options, list) else current_options

        # Кнопка Ветвь А
        view.btn_branch_left = pygame.Rect(100, 800, 450, 80)
        MapView.is_left_hovered = view.btn_branch_left.collidepoint(mouse_pos)
        left_color = (90, 90, 95) if MapView.is_left_hovered else (60, 60, 60)
        pygame.draw.rect(view.screen, left_color, view.btn_branch_left)
        pygame.draw.rect(view.screen, WHITE, view.btn_branch_left, 2)
        
        btn_text_left = "*** БИТВА С БОССОМ ***" if local_step == 10 else f"Ветвь А: {MapView.clean_name(type_left)}"
        view.draw_text(btn_text_left, view.card_font, WHITE, 130, 825)

        # Кнопка Ветвь Б
        view.btn_branch_right = pygame.Rect(600, 800, 450, 80)
        MapView.is_right_hovered = view.btn_branch_right.collidepoint(mouse_pos)
        right_color = (90, 90, 95) if MapView.is_right_hovered else (60, 60, 60)
        pygame.draw.rect(view.screen, right_color, view.btn_branch_right)
        pygame.draw.rect(view.screen, WHITE, view.btn_branch_right, 2)
        
        btn_text_right = "*** БИТВА С БОССОМ ***" if local_step == 10 else f"Ветвь Б: {MapView.clean_name(type_right)}"
        view.draw_text(btn_text_right, view.card_font, WHITE, 630, 825)
