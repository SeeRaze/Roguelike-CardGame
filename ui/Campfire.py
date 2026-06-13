import pygame

from core import forge as forge_mod


class Campfire:
    """Экран Лестничной клетки -- передышка между этажами, стиль EventView.
    Опции: Перекур (30% недостающего HP) / Доработка (улучшение карт за CR) /
    Тюнинг (компаунд-урон за CR) / Выпиливание (удалить карту ценой HP)."""
    sub_state          = "MAIN"
    is_rest_hovered    = False
    is_forge_hovered   = False
    is_sharpen_hovered = False
    is_ritual_hovered  = False

    # Состояние драфта майлстоуна (B3): индекс кующейся карты + 3 тега-кандидата +
    # тир (генерятся ОДИН раз при входе, чтобы не перетасовывать каждый кадр).
    _draft_card_index = None
    _draft_choices    = []
    _draft_tier       = None

    # Цвет тира тега в драфте (юзер: тир выделяем цветом текста).
    _TIER_COLORS = {"early": (140, 200, 255), "legendary": (255, 200, 80)}

    # Цена «Выпиливания»: HP сквозь щит за удаление одной карты из колоды.
    _BLOOD_RITUAL_COST = 10

    _BG_COLOR        = (15,  10,  10)
    _PANEL_COLOR     = (35,  20,  15)
    _BTN_COLOR       = (70,  40,  20)
    _BTN_HOVER_COLOR = (120, 70,  30)
    _BTN_DISABLED    = (45,  35,  30)
    _BTN_BORDER      = (220, 140, 60)
    _TITLE_COLOR     = (255, 180, 60)
    _TEXT_COLOR      = (210, 200, 185)
    _HP_COLOR        = (100, 220, 100)
    _BLOOD_COLOR     = (220, 80,  70)

    @staticmethod
    def reset():
        Campfire.sub_state          = "MAIN"
        Campfire.is_rest_hovered    = False
        Campfire.is_forge_hovered   = False
        Campfire.is_sharpen_hovered = False
        Campfire.is_ritual_hovered  = False
        Campfire._clear_draft()

    @staticmethod
    def _clear_draft():
        Campfire._draft_card_index = None
        Campfire._draft_choices    = []
        Campfire._draft_tier       = None

    @staticmethod
    def _ritual_available(view) -> bool:
        """Выпиливание доступно, только если HP хватает пережить цену и в колоде
        есть что приносить в жертву (защита от суицида / пустой колоды)."""
        return (view.gm.player.hp > Campfire._BLOOD_RITUAL_COST
                and len(view.gm.current_deck) > 1)

    @staticmethod
    def draw_screen(view):
        C         = Campfire
        screen    = view.screen
        screen.fill(C._BG_COLOR)

        title_font = pygame.font.SysFont("Arial", 42, bold=True)
        text_font  = pygame.font.SysFont("Arial", 28)
        btn_font   = pygame.font.SysFont("Arial", 26, bold=True)
        small_font = pygame.font.SysFont("Arial", 18, bold=True)

        if Campfire.sub_state == "MAIN":
            Campfire._draw_main(view, screen, title_font, text_font, btn_font)
        elif Campfire.sub_state == "FORGE":
            Campfire._draw_card_grid(
                view, screen, title_font, text_font, small_font,
                title="ДОРАБОТКА: УЛУЧШЕНИЕ КАРТ",
                hint="Клик по карте: +1 уровень за CR  |  Колесо мыши -- прокрутка",
                mark_upgraded=False, forge_view=True,
            )
        elif Campfire.sub_state == "SACRIFICE":
            Campfire._draw_card_grid(
                view, screen, title_font, text_font, small_font,
                title="ВЫПИЛИВАНИЕ: ВЫБЕРИТЕ КАРТУ",
                hint=f"Удалить карту из колоды ценой -{Campfire._BLOOD_RITUAL_COST} HP"
                     "  |  Колесо мыши -- прокрутка",
                mark_upgraded=False,
            )
        elif Campfire.sub_state == "DRAFT":
            Campfire._draw_draft(view, screen, title_font, text_font, btn_font)

    # ------------------------------------------------------------------
    # MAIN: три кнопки-опции
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_main(view, screen, title_font, text_font, btn_font):
        C         = Campfire
        W, _      = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()

        panel = pygame.Rect(W // 2 - 480, 90, 960, 600)
        pygame.draw.rect(screen, C._PANEL_COLOR, panel, border_radius=16)
        pygame.draw.rect(screen, C._BTN_BORDER,  panel, 2, border_radius=16)

        title = title_font.render(
            f"ЭТАЖ {view.gm.current_floor}: ЛЕСТНИЧНАЯ КЛЕТКА", True, C._TITLE_COLOR)
        screen.blit(title, (W // 2 - title.get_width() // 2, 130))

        hp_surf = text_font.render(
            f"Здоровье: {view.gm.player.hp} / {view.gm.player.max_hp}",
            True, C._HP_COLOR)
        screen.blit(hp_surf, (W // 2 - hp_surf.get_width() // 2, 195))

        heal_preview = view.gm.player.rest_heal_amount(
            view.gm.player.hp, view.gm.player.max_hp)

        player = view.gm.player
        fp     = player.forge_points

        # 4 опции: Перекур / Доработка / Тюнинг / Выпиливание. Лестничная клетка =
        # чистый CR-узел (С57: Закалка переехала на ось ЗОЛОТА → в магазин, economy-axis-trinity).
        # Стоки CR (Доработка/Тюнинг) не продвигают этаж — продвижение за Перекуром/Выпиливанием.
        x = W // 2 - 300
        view.btn_rest_rect    = pygame.Rect(x, 250, 600, 64)
        view.btn_forge_rect   = pygame.Rect(x, 346, 600, 64)
        view.btn_sharpen_rect = pygame.Rect(x, 442, 600, 64)
        view.btn_ritual_rect  = pygame.Rect(x, 538, 600, 64)
        ritual_ok    = Campfire._ritual_available(view)
        sharpen_cost = forge_mod.SHARPEN_FP_COST
        sharpen_ok   = fp >= sharpen_cost

        Campfire.is_rest_hovered    = view.btn_rest_rect.collidepoint(mouse_pos)
        Campfire.is_forge_hovered   = view.btn_forge_rect.collidepoint(mouse_pos)
        Campfire.is_sharpen_hovered = (sharpen_ok
                                       and view.btn_sharpen_rect.collidepoint(mouse_pos))
        Campfire.is_ritual_hovered  = (ritual_ok
                                       and view.btn_ritual_rect.collidepoint(mouse_pos))

        Campfire._draw_button(screen, btn_font, view.btn_rest_rect,
                              f"ПЕРЕКУР  (+{heal_preview} HP, 30% недостающего)",
                              Campfire.is_rest_hovered, True)
        Campfire._draw_button(screen, btn_font, view.btn_forge_rect,
                              f"ДОРАБОТКА  (Улучшение за CR: {fp})",
                              Campfire.is_forge_hovered, True)
        sharpen_pct = int(forge_mod.SHARPEN_ATK_PCT * 100)
        Campfire._draw_button(screen, btn_font, view.btn_sharpen_rect,
                              f"ТЮНИНГ  (+{sharpen_pct}% урон ×{player.atk_mult:.2f}, {sharpen_cost} CR)",
                              Campfire.is_sharpen_hovered, sharpen_ok)
        ritual_lbl = (f"ВЫПИЛИВАНИЕ  (Удалить карту, -{Campfire._BLOOD_RITUAL_COST} HP)"
                      if ritual_ok else "ВЫПИЛИВАНИЕ  (недоступно)")
        Campfire._draw_button(screen, btn_font, view.btn_ritual_rect,
                              ritual_lbl, Campfire.is_ritual_hovered, ritual_ok,
                              border=Campfire._BLOOD_COLOR)

    @staticmethod
    def _draw_button(screen, font, rect, label, hovered, enabled, border=None):
        C = Campfire
        if not enabled:
            col = C._BTN_DISABLED
        elif hovered:
            col = C._BTN_HOVER_COLOR
        else:
            col = C._BTN_COLOR
        pygame.draw.rect(screen, col, rect, border_radius=12)
        pygame.draw.rect(screen, border or C._BTN_BORDER, rect, 2, border_radius=12)
        txt_col = (255, 255, 255) if enabled else (140, 130, 125)
        lbl = font.render(label, True, txt_col)
        screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                          rect.centery - lbl.get_height() // 2))

    # ------------------------------------------------------------------
    # FORGE / SACRIFICE: общая прокручиваемая сетка карт колоды
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_card_grid(view, screen, title_font, text_font, small_font,
                        *, title, hint, mark_upgraded, forge_view=False):
        C         = Campfire
        W, H      = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()
        player    = view.gm.player

        panel = pygame.Rect(40, 20, W - 80, H - 40)
        pygame.draw.rect(screen, C._PANEL_COLOR, panel, border_radius=16)
        pygame.draw.rect(screen, C._BTN_BORDER,  panel, 2, border_radius=16)

        t = title_font.render(title, True, C._TITLE_COLOR)
        screen.blit(t, (W // 2 - t.get_width() // 2, 45))
        h = text_font.render(hint, True, C._TEXT_COLOR)
        screen.blit(h, (W // 2 - h.get_width() // 2, 110))

        # Режим ковки: шапка с балансом FP/капом + кнопка «Завершить» (вне клипа).
        if forge_view:
            info = text_font.render(
                f"CR: {player.forge_points}    Кап уровня: {player.forge_level_cap}",
                True, C._TITLE_COLOR)
            screen.blit(info, (W // 2 - info.get_width() // 2, 138))
            view.btn_forge_done_rect = pygame.Rect(W - 40 - 226, 42, 210, 56)
            done_hov = view.btn_forge_done_rect.collidepoint(mouse_pos)
            Campfire._draw_button(screen, small_font, view.btn_forge_done_rect,
                                  "← ГОТОВО", done_hov, True)
            view.btn_campfire_back_rect = None
        else:
            view.btn_forge_done_rect = None
            # Выпиливание — кнопка «Назад»: выйти без удаления (игрок мог зайти
            # просто посмотреть колоду; не наказываем за любопытство).
            # Справа — симметрично «← ГОТОВО» Доработки, чтобы не налезать на HUD ресурсов.
            view.btn_campfire_back_rect = pygame.Rect(W - 40 - 226, 42, 210, 56)
            back_hov = view.btn_campfire_back_rect.collidepoint(mouse_pos)
            Campfire._draw_button(screen, small_font, view.btn_campfire_back_rect,
                                  "← НАЗАД", back_hov, True)

        cards_per_row = 7
        card_w, card_h = view.card_width, view.card_height
        spacing_x = card_w + 24
        spacing_y = card_h + 36
        total_w   = cards_per_row * spacing_x - 24
        start_x   = W // 2 - total_w // 2
        start_y   = 175 if forge_view else 165

        clip_rect = pygame.Rect(60, start_y, W - 120, H - start_y - 30)
        screen.set_clip(clip_rect)

        hovered_card_data    = None
        view.campfire_card_rects = []

        for index, card in enumerate(view.gm.current_deck):
            row    = index // cards_per_row
            col    = index % cards_per_row
            card_x = start_x + col * spacing_x
            card_y = start_y + 10 + row * spacing_y - view.scroll_y
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
            view.campfire_card_rects.append((card_rect, index))

            is_hov = card_rect.collidepoint(mouse_pos)
            if is_hov:
                hovered_card_data = (card, card_rect)
            draw_y = card_y - 10 if is_hov else card_y
            view.draw_card_by_data(card, card_x, draw_y)

            if forge_view:
                Campfire._draw_forge_overlay(screen, small_font, player, card,
                                             card_x, draw_y, card_w, card_h)
            elif mark_upgraded and card.upgraded:
                lbl = small_font.render("[МАКС]", True, C._HP_COLOR)
                screen.blit(lbl, (card_x + 8, draw_y + card_h - 26))

        screen.set_clip(None)

        if hovered_card_data:
            card, rect = hovered_card_data
            from ui.cards import CardRenderer
            CardRenderer.draw_card_keyword_tooltip(
                screen, view.card_font, view.card_desc_font, card, rect
            )

    @staticmethod
    def _draw_forge_overlay(screen, font, player, card, card_x, draw_y,
                            card_w, card_h):
        """Поверх карты в Доработке: бейдж уровня (сверху) + цена/статус следующей
        ковки (снизу). Зелёный — по карману, красный — не хватает FP, золотой —
        упёрлись в кап. Звезда — следующий уровень открывает теговый слот."""
        C     = Campfire
        level = forge_mod.forge_level(player, card)
        cap   = player.forge_level_cap

        badge = font.render(f"Ур.{level}", True,
                            C._HP_COLOR if level > 0 else C._TEXT_COLOR)
        bg = pygame.Rect(card_x + 6, draw_y + 6, badge.get_width() + 10,
                         badge.get_height() + 6)
        pygame.draw.rect(screen, (0, 0, 0), bg, border_radius=6)
        screen.blit(badge, (bg.x + 5, bg.y + 3))

        if level >= cap:
            txt, col = f"кап {cap}", C._BTN_BORDER
        else:
            cost = forge_mod.level_cost(level)
            affordable = player.forge_points >= cost
            star = " *" if forge_mod.milestone_tier(level + 1) else ""
            txt  = f"+ур: {cost} CR{star}"
            col  = C._HP_COLOR if affordable else C._BLOOD_COLOR
        line = font.render(txt, True, col)
        lbg = pygame.Rect(card_x + 4, draw_y + card_h - 26,
                          line.get_width() + 8, line.get_height() + 4)
        pygame.draw.rect(screen, (0, 0, 0), lbg, border_radius=6)
        screen.blit(line, (lbg.x + 4, lbg.y + 2))

    # ------------------------------------------------------------------
    # Обработка кликов
    # ------------------------------------------------------------------
    @staticmethod
    def handle_clicks(view, mouse_pos):
        if Campfire.sub_state == "MAIN":
            Campfire._handle_main(view, mouse_pos)
        elif Campfire.sub_state == "FORGE":
            Campfire._handle_forge(view, mouse_pos)
        elif Campfire.sub_state == "SACRIFICE":
            Campfire._handle_sacrifice(view, mouse_pos)
        elif Campfire.sub_state == "DRAFT":
            Campfire._handle_draft(view, mouse_pos)

    @staticmethod
    def _handle_main(view, mouse_pos):
        if hasattr(view, 'btn_rest_rect') and view.btn_rest_rect.collidepoint(mouse_pos):
            player = view.gm.player
            amount = player.rest_heal_amount(player.hp, player.max_hp)
            player.heal(amount)
            Campfire._advance(view)

        elif hasattr(view, 'btn_forge_rect') and view.btn_forge_rect.collidepoint(mouse_pos):
            view.scroll_y = 0
            Campfire.sub_state = "FORGE"

        # Заточка (FP) — мгновенный сток, НЕ продвигает этаж. Закалка (С57) ушла
        # в магазин на ось ЗОЛОТА (economy-axis-trinity) — лестн. клетка = чистый CR-узел.
        elif hasattr(view, 'btn_sharpen_rect') and view.btn_sharpen_rect.collidepoint(mouse_pos):
            forge_mod.sharpen(view.gm.player)

        elif hasattr(view, 'btn_ritual_rect') \
                and view.btn_ritual_rect.collidepoint(mouse_pos) \
                and Campfire._ritual_available(view):
            view.scroll_y = 0
            Campfire.sub_state = "SACRIFICE"

    @staticmethod
    def _handle_forge(view, mouse_pos):
        # «Готово» — вернуться к выбору в лестничной клетке (продвижение по этажу — за
        # Перекуром/Выпиливанием на главном экране; доработка CR параллельна, как в симе).
        done = getattr(view, 'btn_forge_done_rect', None)
        if done is not None and done.collidepoint(mouse_pos):
            view.scroll_y = 0
            Campfire.sub_state = "MAIN"
            return
        # Клик по карте — поднять её на +1 уровень за FP (остаёмся на экране,
        # можно ковать дальше, пока хватает FP / не упёрлись в кап). Если следующий
        # уровень — майлстоун (открывает тег), уходим в драфт 1-из-3 (B3).
        player     = view.gm.player
        class_name = type(player).__name__
        for card_rect, index in getattr(view, 'campfire_card_rects', []):
            if card_rect.collidepoint(mouse_pos):
                card = view.gm.current_deck[index]
                if not forge_mod.can_forge(player, card):
                    break
                tier = forge_mod.next_forge_milestone_tier(player, card)
                if tier is not None:
                    Campfire._open_draft(player, card, index, tier)
                else:
                    forge_mod.forge_card_one_level(player, card, class_name)
                break

    @staticmethod
    def _open_draft(player, card, index, tier):
        """Войти в драфт майлстоуна: сгенерить 3 тега-кандидата ОДИН раз (B3) и
        переключить под-экран. Канал — по природе карты."""
        from core.ForgeRegistry import draft_tag_choices
        channel = forge_mod.card_forge_channel(card)
        class_name = type(player).__name__
        Campfire._draft_card_index = index
        Campfire._draft_tier       = tier
        Campfire._draft_choices    = draft_tag_choices(class_name, tier, channel)
        # Краевой случай (бедный канал даёт 0 кандидатов) — не блокируем ковку,
        # падаем на авто-тег (pick_tag), как раньше.
        if not Campfire._draft_choices:
            forge_mod.forge_card_one_level(player, card, class_name)
            Campfire._clear_draft()
            return
        Campfire.sub_state = "DRAFT"

    @staticmethod
    def _draw_draft(view, screen, title_font, text_font, btn_font):
        """Под-экран драфта майлстоуна (B3): карта + 3 тега-кандидата на выбор.
        Тир тега выделен цветом текста. Клик по тегу вешает его на карту."""
        from core.ForgeRegistry import TAGS
        C    = Campfire
        W, H = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(C._BG_COLOR)

        panel = pygame.Rect(W // 2 - 420, 80, 840, H - 160)
        pygame.draw.rect(screen, C._PANEL_COLOR, panel, border_radius=16)
        pygame.draw.rect(screen, C._BTN_BORDER,  panel, 2, border_radius=16)

        card = view.gm.current_deck[C._draft_card_index]
        tier_name = "ЛЕГЕНДАРНЫЙ" if C._draft_tier == "legendary" else "РАННИЙ"
        tier_col  = C._TIER_COLORS.get(C._draft_tier, C._TEXT_COLOR)

        t = title_font.render("ВЫБОР УЛУЧШЕНИЯ", True, C._TITLE_COLOR)
        screen.blit(t, (W // 2 - t.get_width() // 2, panel.y + 24))
        sub = text_font.render(f"Карта «{card.name}»  •  {tier_name} тег", True, tier_col)
        screen.blit(sub, (W // 2 - sub.get_width() // 2, panel.y + 78))
        hint = view.card_desc_font.render(
            "Выбери один из трёх. Рандом кусается — иногда чужой тег, иногда джекпот.",
            True, C._TEXT_COLOR)
        screen.blit(hint, (W // 2 - hint.get_width() // 2, panel.y + 116))

        # Три кнопки-кандидата (вертикально). Заголовок — название тега в цвете
        # тира, под ним — короткое описание эффекта.
        view.draft_choice_rects = []
        btn_w, btn_h = 720, 96
        x  = W // 2 - btn_w // 2
        y0 = panel.y + 160
        for i, tag_id in enumerate(C._draft_choices):
            spec = TAGS.get(tag_id, {})
            rect = pygame.Rect(x, y0 + i * (btn_h + 18), btn_w, btn_h)
            hov  = rect.collidepoint(mouse_pos)
            col  = C._BTN_HOVER_COLOR if hov else C._BTN_COLOR
            pygame.draw.rect(screen, col, rect, border_radius=12)
            pygame.draw.rect(screen, tier_col, rect, 2, border_radius=12)
            name = btn_font.render(spec.get("label", tag_id), True, tier_col)
            screen.blit(name, (rect.x + 24, rect.y + 22))
            kind = "усиление ×" if spec.get("kind") == "mult" else "добавка +"
            desc = view.card_desc_font.render(
                f"{kind}  •  канал: {spec.get('channel', 'damage')}",
                True, C._TEXT_COLOR)
            screen.blit(desc, (rect.x + 24, rect.y + 58))
            view.draft_choice_rects.append((rect, tag_id))

    @staticmethod
    def _handle_draft(view, mouse_pos):
        """Клик по тегу-кандидату → ковка с выбранным тегом, возврат в Доработку."""
        player = view.gm.player
        for rect, tag_id in getattr(view, 'draft_choice_rects', []):
            if rect.collidepoint(mouse_pos):
                card = view.gm.current_deck[Campfire._draft_card_index]
                forge_mod.forge_card_one_level(
                    player, card, type(player).__name__, forced_tag=tag_id)
                Campfire._clear_draft()
                Campfire.sub_state = "FORGE"
                break

    @staticmethod
    def _handle_sacrifice(view, mouse_pos):
        # «Назад» — вернуться на главный экран лестничной клетки без удаления (HP цел).
        back = getattr(view, 'btn_campfire_back_rect', None)
        if back is not None and back.collidepoint(mouse_pos):
            view.scroll_y = 0
            Campfire.sub_state = "MAIN"
            return
        for card_rect, index in getattr(view, 'campfire_card_rects', []):
            if card_rect.collidepoint(mouse_pos):
                removed = view.gm.current_deck.pop(index)
                view.gm.player.lose_hp(Campfire._BLOOD_RITUAL_COST)
                print(f"[ВЫПИЛИВАНИЕ] Карта '{removed.name}' выпилена из колоды.")
                Campfire._advance(view)
                break

    @staticmethod
    def _advance(view):
        """Лестничная клетка -- одно действие за визит: применили и идём на след. этаж."""
        Campfire.sub_state = "MAIN"
        view.gm.current_floor += 1
        view.gm.setup_next_floor()
