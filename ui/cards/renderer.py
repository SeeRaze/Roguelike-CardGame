# ui/cards/renderer.py
# Публичный фасад отрисовки карты: оркестрирует classifier/description/keywords.
import pygame
from core.rarity import Rarity, RARITY_COLORS
from ui.cards.classifier import classify_card
from ui.cards.data import (
    card_palette, COLOR_COST_LOW, COLOR_COST_DISC, GENERIC_BORDER,
    FORGE_TITLE_BASE, FORGE_TITLE_LINEAR, FORGE_TITLE_EARLY, GEM_R,
)
from ui.cards import description, keywords

# Цвет принадлежности карты (рамка) = цвет класса из единого CLASS_INFO.
# Импорт лениво-кэшируется, чтобы избежать цикла ui.hub ↔ ui.cards на загрузке.
_CLASS_COLORS = None


def _class_color(card_class):
    """Цвет класса карты для рамки (вариант Б). None / неизвестный → нейтраль."""
    global _CLASS_COLORS
    if _CLASS_COLORS is None:
        from ui.hub.data import CLASS_INFO
        _CLASS_COLORS = {k: v.get("color", GENERIC_BORDER) for k, v in CLASS_INFO.items()}
    if not card_class:
        return GENERIC_BORDER
    return _CLASS_COLORS.get(card_class, GENERIC_BORDER)


def _muted_bg(bg):
    """Приглушённый фон школы эффекта (вариант Б): фон несёт «что делает карта»
    оттенком, но не спорит с рамкой-классом и иконками статусов поверх."""
    return tuple(int(c * 0.72) for c in bg)


# Положение камня редкости — выбирается константой (превью двух вариантов).
#   "center" — по центру верхней зоны (как в Hearthstone, на «арте»)
#   "corner" — правый верхний угол (слева стоимость-орб)
GEM_POSITION = "corner"


class CardRenderer:
    @staticmethod
    def get_card_colors(card):
        """(bg, border) карты. Вариант Б: фон = приглушённая школа эффекта,
        рамка = цвет класса (generic → нейтраль)."""
        school_bg, _ = card_palette(classify_card(card))
        border = _class_color(getattr(card, "card_class", None))
        return _muted_bg(school_bg), border

    @staticmethod
    def _forge_level_and_tier(card, player):
        """(level, has_legendary) карты по паспорту ковки. (0, False) если не кована
        / нет игрока. has_legendary — есть ли легендарный слот (15+ майлстоун)."""
        if player is None:
            return 0, False
        from core.ForgeRegistry import resolve_forge_record, TAGS
        rec = resolve_forge_record(card, player)
        if not rec:
            return 0, False
        level = rec.get("level", 0)
        has_leg = any(
            TAGS.get(s.get("tag_id"), {}).get("tier") == "legendary"
            for s in (rec.get("slots") or [])
        )
        return level, has_leg

    @staticmethod
    def _forge_slots(card, player):
        """Список слотов-тегов ковки карты (для расчёта высоты строки меток).
        Пусто, если карта не кована / нет игрока."""
        if player is None:
            return []
        from core.ForgeRegistry import resolve_forge_record
        rec = resolve_forge_record(card, player)
        if not rec:
            return []
        return rec.get("slots") or []

    @staticmethod
    def _title_style(level, has_legendary):
        """(color, rainbow) названия по уровню ковки. 0=серый,1-4=зелёный,
        5-14=жёлтый, 15+/легендарный=радуга."""
        if has_legendary or level >= 15:
            return None, True
        if level >= 5:
            return FORGE_TITLE_EARLY, False
        if level >= 1:
            return FORGE_TITLE_LINEAR, False
        return FORGE_TITLE_BASE, False

    @staticmethod
    def draw(surface, card, x, y, font_title, font_desc,
             is_hovered=False, player=None, enemy=None, combat_manager=None):
        """Мастер-метод полной отрисовки карты 180×250."""
        width, height = 180, 250
        rect = pygame.Rect(x, y, width, height)

        # temp_cost: механика Потока (-1 к стоимости случайной карты)
        display_cost = getattr(card, 'temp_cost', card.cost)
        is_discounted = display_cost < card.cost

        can_afford = (
            player is None
            or not hasattr(player, 'energy')
            or display_cost <= player.energy
        )

        bg_color, border_color = CardRenderer.get_card_colors(card)

        if is_hovered:
            bg_color = tuple(min(255, c + 20) for c in bg_color)

        border_thickness = 5 if is_hovered else 3

        pygame.draw.rect(surface, bg_color, rect, border_radius=10)
        pygame.draw.rect(surface, border_color, rect, border_thickness, border_radius=10)

        # ── Название: цвет/радуга по уровню ковки ──────────────────────────
        level, has_leg = CardRenderer._forge_level_and_tier(card, player)
        title_color, rainbow = CardRenderer._title_style(level, has_leg)
        if is_hovered and not rainbow and level == 0:
            title_color = (241, 196, 15)   # ховер подсвечивает только некованые
        phase = (pygame.time.get_ticks() / 1400.0) if rainbow else 0.0
        title_bottom = description.draw_centered_title(
            surface, card.name, font_title, rect, is_hovered,
            color=title_color, rainbow=rainbow, phase=phase)

        # ── Стоимость-орб (энергия) слева-сверху ───────────────────────────
        if is_discounted:
            cost_color = COLOR_COST_DISC
        elif not can_afford:
            cost_color = COLOR_COST_LOW
        else:
            cost_color = border_color
        CardRenderer._draw_cost_orb(surface, rect, display_cost, cost_color, font_title)

        # ── Камень редкости ────────────────────────────────────────────────
        CardRenderer._draw_rarity_gem(surface, rect, getattr(card, "rarity", None))

        # Нижняя граница описания: над строкой меток ковки/чипов. Чем больше тегов,
        # тем выше граница → динамический шрифт описания ужмётся, не налезая.
        n_dots = len(CardRenderer._forge_slots(card, player))
        has_chips = False  # вычислим после preview ниже

        # ── Строка иконок эффектов (под названием) ─────────────────────────
        # Заменяет текстовые названия эффектов в описании. Полный разбор — в тултипе.
        eff_bottom = CardRenderer._draw_effect_icons(surface, card, rect, title_bottom)
        desc_top = eff_bottom + 4

        preview = None
        if card.card_type == "attack" and player is not None and enemy is not None:
            # База урона для превью — из ЭФФЕКТА (учитывает уровень ковки +δ + текущий
            # ресурс для scaling-карт), а не из строки описания (ковкой не обновляется).
            base = CardRenderer._card_base_damage(card, player)
            predicted = None
            if base and combat_manager is not None:
                # Единый расчёт: КОНЕЧНОЕ число (со ВСЕМИ реакциями — комбо ×N,
                # ковка, шок) в строке урона; чипы реакций остаются как ОБЪЯСНЕНИЕ,
                # откуда такая цифра. Игрок не перемножает сам. Превью == удар.
                # Нет реакций → full == guaranteed (несинергийные карты не меняются).
                from core.EffectCalculator import EffectCalculator
                preview = EffectCalculator.preview(
                    player, enemy, base, combat_manager=combat_manager,
                    game_manager=getattr(combat_manager, "gm", None), card=card)
                predicted = preview["full"]
                has_chips = bool(preview.get("reactions")) or \
                    (preview.get("forge_mult", 1.0) not in (None, 1.0))

        # Зарезервировать низ под строку меток (Ур.N + точки-теги) и/или чипы.
        marks_h = 22 if (level > 0 or n_dots) else 0
        chips_h = 22 if has_chips else 0
        desc_bottom = rect.bottom - 10 - max(marks_h, 0) - chips_h

        # Описание с актуальными числами эффектов (ковка +δ не трогает строку):
        # пары N(M) пересчитываются из эффектов везде — и в бою, и в костре/магазине.
        display_desc = description.project_forge_values(card)

        if preview is not None:
            description.draw_smart_description(
                surface, display_desc, font_desc, rect,
                card.upgraded, player=player, enemy=enemy,
                base_override=base, predicted=predicted,
                top_y=desc_top, bottom_y=desc_bottom,
            )
        else:
            description.draw_smart_description(
                surface, display_desc, font_desc, rect,
                card.upgraded, top_y=desc_top, bottom_y=desc_bottom,
            )

        CardRenderer._draw_forge_marks(surface, card, player, rect, font_desc)
        if preview is not None:
            CardRenderer._draw_reaction_chips(surface, rect, preview, font_desc)

        if not can_afford:
            CardRenderer._draw_unaffordable_overlay(surface, rect)

        return rect

    # ── Стоимость-орб ───────────────────────────────────────────────────────
    @staticmethod
    def _draw_cost_orb(surface, rect, cost, color, font):
        """Аккуратный энерго-орб со стоимостью слева-сверху: круг с заливкой,
        светлой каймой и числом по центру."""
        cx, cy, r = rect.x + 22, rect.y + 22, 18
        dark = tuple(int(c * 0.35) for c in color)
        pygame.draw.circle(surface, dark, (cx, cy), r)
        pygame.draw.circle(surface, color, (cx, cy), r, 3)
        # лёгкий блик сверху
        pygame.draw.arc(surface, (255, 255, 255),
                        (cx - r + 3, cy - r + 3, (r - 3) * 2, (r - 3) * 2),
                        0.7, 2.2, 2)
        ts = font.render(str(cost), True, (255, 255, 255))
        surface.blit(ts, ts.get_rect(center=(cx, cy)))

    # ── Камень редкости ─────────────────────────────────────────────────────
    @staticmethod
    def _draw_rarity_gem(surface, rect, rarity):
        """Минималистичный самоцвет редкости (стиль Hearthstone): огранённый ромб
        цвета редкости с тёмной оправой и бликом. Позиция — GEM_POSITION."""
        if rarity is None:
            rarity = Rarity.COMMON
        color = RARITY_COLORS.get(rarity, (150, 150, 150))

        if GEM_POSITION == "center":
            cx, cy = rect.centerx, rect.y + 78
        else:  # corner
            cx, cy = rect.right - 24, rect.y + 22

        r = GEM_R
        # Оправа (тёмный ободок-ромб).
        outer = [(cx, cy - r - 3), (cx + r + 3, cy), (cx, cy + r + 3), (cx - r - 3, cy)]
        pygame.draw.polygon(surface, (18, 18, 26), outer)
        pygame.draw.polygon(surface, (235, 235, 245), outer, 1)
        # Самоцвет (ромб цвета редкости).
        gem = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(surface, color, gem)
        # Грань-блик (верхняя левая половина светлее).
        hi = tuple(min(255, c + 70) for c in color)
        pygame.draw.polygon(surface, hi, [(cx, cy - r), (cx - r, cy), (cx, cy)])

    # ── Строка иконок эффектов ───────────────────────────────────────────────
    _EFF_ICON_R = 9          # радиус иконки эффекта
    _EFF_ICON_GAP = 8        # шаг между иконками

    @staticmethod
    def _draw_effect_icons(surface, card, rect, title_bottom):
        """Ряд иконок эффектов карты под названием (key+значение). Иконки заменяют
        текстовые названия эффектов; полный разбор — в ховер-тултипе. Возвращает Y
        нижней границы ряда (title_bottom, если эффектов нет — ряд не рисуется)."""
        from ui.cards.keywords import get_card_keywords
        from ui.status_icons import draw_status_icon
        from ui.cards.data import effect_icon_color

        kws = get_card_keywords(card)
        if not kws:
            return title_bottom

        r = CardRenderer._EFF_ICON_R
        gap = CardRenderer._EFF_ICON_GAP
        font = pygame.font.SysFont("Arial", 13, bold=True)

        # Ширина одной ячейки: иконка (+ число, если val>0).
        cells = []
        for key, val in kws:
            num = font.render(str(val), True, (235, 235, 240)) if val else None
            w = r * 2 + (num.get_width() + 3 if num else 0)
            cells.append((key, num, w))

        total = sum(w for _, _, w in cells) + gap * (len(cells) - 1)
        x = rect.centerx - total // 2
        cy = title_bottom + 4 + r

        for key, num, w in cells:
            color = effect_icon_color(key)
            draw_status_icon(surface, key, x + r, cy, r, color)
            if num:
                surface.blit(num, (x + r * 2 + 3, cy - num.get_height() // 2))
            x += w + gap

        return cy + r

    @staticmethod
    def _card_base_damage(card, player=None):
        """Текущее значение урона карты из ЭФФЕКТА (а не из строки описания):
        upgrade_val если карта улучшена/прокачана, иначе base_val. Учитывает
        линейный слой ковки (+δ бампит base_val/upgrade_val). None, если карта без
        урона. Используется для корректного превью числа на карте (39.5 хотфикс).

        Урон-эффекты с плоской базой: DamageEffect и EchoPayoffEffect («Каскад» —
        ×2 при Эхо остаётся условным, показывается отдельно). ShieldDamageEffect
        («Регрессионка») НЕ считается: его урон = живой щит, плоского числа нет.

        Классовые scaling-эффекты (Дисциплина/Мастерство/HP-долг) сами знают свою
        проекцию через projected_damage(player) — урон с учётом ТЕКУЩЕГО ресурса
        игрока, чтобы превью == фактический удар."""
        from core.cards.base import DamageEffect
        from core.cards.echo import EchoPayoffEffect
        for e in card.effects:
            if hasattr(e, "projected_damage"):
                return e.projected_damage(player, card.upgraded)
            if isinstance(e, (DamageEffect, EchoPayoffEffect)):
                return e.upgrade_val if card.upgraded else e.base_val
        return None

    # Цвета чипов реакций (минимал-стиль, решение юзера: смысл из цвета + ховера).
    _CHIP_COMBO = (70, 130, 180)    # стихийное комбо (ПАР и т.п.) — стально-синий
    _CHIP_FORGE = (200, 120, 40)    # forge-теги — оранжевый

    @staticmethod
    def _draw_reaction_chips(surface, rect, preview, font):
        """Схематичные чипы условных реакций, что СРАБОТАЮТ против текущей цели:
        только цвет + ×множитель (синий=комбо, оранж=ковка). Полные названия и
        разбор — в ховер-тултипе. Низ карты, выровнены вправо (растут влево),
        чтобы не пересекаться с точками-тегами (низ-слева)."""
        chips = []
        for r in preview.get("reactions", []):
            chips.append((f"×{r['mult']:g}", CardRenderer._CHIP_COMBO))
        fm = preview.get("forge_mult", 1.0)
        if fm and fm != 1.0:
            chips.append((f"×{fm:g}", CardRenderer._CHIP_FORGE))
        if not chips:
            return

        x = rect.right - 8
        for text, color in reversed(chips):
            ts = font.render(text, True, (255, 255, 255))
            w, h = ts.get_width() + 12, ts.get_height() + 4
            chip = pygame.Rect(x - w, rect.bottom - h - 6, w, h)
            pygame.draw.rect(surface, color, chip, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255), chip, 1, border_radius=6)
            surface.blit(ts, (chip.x + 6, chip.y + 2))
            x -= w + 4

    @staticmethod
    def _draw_forge_marks(surface, card, player, rect, font):
        """Метки прокачки карты (39.5): уровень и точки-теги — компактной строкой
        снизу-слева. Уровень ТАКЖЕ кодируется цветом названия (см. _title_style),
        здесь — точное число «Ур.N». Золотая точка-тег = легендарный ×mult,
        серебряная = ранний +mult; число рядом = grade Гипер-заряда."""
        if player is None:
            return
        from core.ForgeRegistry import resolve_forge_record, TAGS
        rec = resolve_forge_record(card, player)
        if not rec:
            return

        level = rec.get("level", 0)
        dot_x = rect.x + 12
        dot_y = rect.bottom - 20

        # «Ур.N» — слева в нижней строке (бейдж сверху-справа убран: там камень редкости).
        if level > 0:
            lvl = font.render(f"Ур.{level}", True, (210, 210, 220))
            surface.blit(lvl, (dot_x, dot_y - 1))
            dot_x += lvl.get_width() + 8

        for slot in rec.get("slots") or []:
            spec = TAGS.get(slot.get("tag_id"), {})
            col = (235, 200, 80) if spec.get("kind") == "mult" else (200, 200, 210)
            pygame.draw.circle(surface, col, (dot_x + 5, dot_y + 5), 6)
            pygame.draw.circle(surface, (0, 0, 0), (dot_x + 5, dot_y + 5), 6, 1)
            grade = slot.get("grade", 0)
            if grade:
                g = font.render(str(grade), True, (255, 240, 180))
                surface.blit(g, (dot_x + 12, dot_y - 2))
                dot_x += g.get_width() + 4
            dot_x += 18

    @staticmethod
    def draw_card_keyword_tooltip(screen, font_title, font_desc, card, card_rect,
                                  damage_steps=None, player=None):
        keywords.draw_card_keyword_tooltip(
            screen, font_title, font_desc, card, card_rect, damage_steps, player)

    @staticmethod
    def _draw_unaffordable_overlay(surface, rect: pygame.Rect):
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (rect.x, rect.y))
