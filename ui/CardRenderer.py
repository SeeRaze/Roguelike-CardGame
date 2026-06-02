import pygame
import re
from core.EffectCalculator import EffectCalculator


class CardRenderer:
    COLOR_COMBO = (255, 215, 0)    # Золотой -- комбо ПАР
    COLOR_DMG   = (46, 204, 113)   # Зелёный -- улучшённые цифры
    COLOR_GRAY  = (200, 200, 200)  # Серый -- обычный текст

    @staticmethod
    def get_card_colors(card):
        name = card.name.lower()
        if "огн" in name or "поджог" in name:
            return (45, 20, 20), (231, 76, 60)
        elif "всплеск" in name or "дожд" in name or "вод" in name:
            return (20, 35, 50), (52, 152, 219)
        elif "яд" in name or "токсин" in name or "кислот" in name:
            return (20, 45, 20), (46, 204, 113)
        elif "скруч" in name or "нейтрал" in name or "устраш" in name:
            return (40, 20, 45), (155, 89, 182)
        elif card.card_type == "attack":
            return (45, 45, 45), (240, 70, 70)
        else:
            return (40, 40, 40), (70, 160, 240)

    @staticmethod
    def draw_centered_title(surface, text, font, card_rect, is_hovered):
        words = text.split(' ')
        lines = []
        current_line = ""
        max_width = card_rect.width - 20
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        line_height = font.get_linesize()
        start_y = card_rect.y + 20
        color = (241, 196, 15) if is_hovered else (255, 255, 255)
        for i, line in enumerate(lines):
            line_surf = font.render(line, True, color)
            x = card_rect.x + (card_rect.width // 2) - (line_surf.get_width() // 2)
            surface.blit(line_surf, (x, start_y + i * line_height))

    @staticmethod
    def _get_base_damage(description: str, is_upgraded: bool) -> int:
        """Извлекает базовое число урона из описания карты."""
        if is_upgraded:
            match = re.search(r'\d+\s*\((\d+)\)', description)
        else:
            match = re.search(r'(\d+)', description)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _resolve_description(description: str, is_upgraded: bool,
                             player=None, enemy=None) -> tuple[str, bool, bool]:
        """
        Возвращает (итоговый текст, is_boosted, is_combo).

        Для attack-карт с player+enemy: подставляет реальный урон из
        EffectCalculator вместо базового числа в тексте описания.
        Для остальных: просто чистит скобки.
        """
        is_boosted = False
        is_combo   = False

        # Чистим скобки апгрейда
        if is_upgraded:
            cleaned = re.sub(r'\d+\s*\((\d+)\)', r'\1', description)
        else:
            cleaned = re.sub(r'(\d+)\s*\(\d+\)', r'\1', description)

        if player is None or enemy is None:
            return cleaned, is_boosted, is_combo

        # Считаем модификаторы
        is_combo   = getattr(enemy, 'wet', 0) > 0 and getattr(enemy, 'ignited', 0) > 0
        is_boosted = (
            getattr(player, 'strength', 0) > 0
            or getattr(enemy, 'vulnerable', 0) > 0
            or is_combo
        )

        if not is_boosted:
            return cleaned, is_boosted, is_combo

        # Подставляем реальный урон вместо каждой цифры в описании
        base_dmg = CardRenderer._get_base_damage(description, is_upgraded)
        if base_dmg == 0:
            return cleaned, is_boosted, is_combo

        predicted = EffectCalculator.calculate_damage(
            attacker    = player,
            target      = enemy,
            base_damage = base_dmg,
            dry_run     = True,
        )

        # Заменяем первое число в очищенном тексте на предсказанный урон
        resolved = re.sub(r'\d+', str(predicted), cleaned, count=1)
        return resolved, is_boosted, is_combo

    @staticmethod
    def draw_smart_description(surface, description, font, card_rect,
                               is_upgraded, player=None, enemy=None):
        """Рендерит описание карты с динамическим уроном и цветовыми акцентами."""
        text, is_boosted, is_combo = CardRenderer._resolve_description(
            description, is_upgraded, player, enemy
        )

        color_digit = (
            CardRenderer.COLOR_COMBO if is_combo
            else CardRenderer.COLOR_DMG if is_upgraded
            else CardRenderer.COLOR_GRAY
        )
        font_big = pygame.font.SysFont("Arial", font.size("0")[1] + 4, bold=True)

        words = text.split(' ')
        lines = []
        current_line = []
        max_width = card_rect.width - 24

        for word in words:
            test_str = " ".join([w for w, _ in current_line] + [word])
            if font.size(test_str)[0] <= max_width:
                current_line.append((word, word.isdigit()))
            else:
                lines.append(current_line)
                current_line = [(word, word.isdigit())]
        if current_line:
            lines.append(current_line)

        y_pos = card_rect.y + 110
        line_height = font.get_linesize() + 4

        for line in lines:
            x_pos = card_rect.x + 15
            for word, is_digit in line:
                if is_digit:
                    display = f"*{word}*" if is_boosted else word
                    render_font = font_big if (is_upgraded or is_boosted) else font
                    word_surf = render_font.render(display + " ", True, color_digit)
                else:
                    word_surf = font.render(word + " ", True, CardRenderer.COLOR_GRAY)
                surface.blit(word_surf, (x_pos, y_pos))
                x_pos += word_surf.get_width()
            y_pos += line_height

    @staticmethod
    def draw(surface, card, x, y, font_title, font_desc,
             is_hovered=False, player=None, enemy=None):
        """Мастер-метод полной отрисовки карты 180×250."""
        width, height = 180, 250
        rect = pygame.Rect(x, y, width, height)
        bg_color = (55, 55, 60) if is_hovered else (35, 35, 38)
        border_thickness = 5 if is_hovered else 3
        _, border_color = CardRenderer.get_card_colors(card)

        pygame.draw.rect(surface, bg_color, rect, border_radius=10)
        pygame.draw.rect(surface, border_color, rect, border_thickness, border_radius=10)

        cost_surf = font_title.render(str(card.cost), True, border_color)
        surface.blit(cost_surf, (rect.x + 14, rect.y + 12))

        CardRenderer.draw_centered_title(surface, card.name, font_title, rect, is_hovered)

        # Для attack-карт передаём player+enemy для динамического урона
        if card.card_type == "attack" and player is not None and enemy is not None:
            CardRenderer.draw_smart_description(
                surface, card.description, font_desc, rect,
                card.upgraded, player=player, enemy=enemy
            )
        else:
            CardRenderer.draw_smart_description(
                surface, card.description, font_desc, rect,
                card.upgraded
            )