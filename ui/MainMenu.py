import pygame
import sys
from ui.hub import HubView


class MainMenu:
    """Главное меню -- тёмно-синяя тема, стиль EventView."""

    is_play_hovered  = False
    is_exit_hovered  = False
    is_cards_hovered = False

    _BG_COLOR        = (10,  10,  20)
    _PANEL_COLOR     = (20,  20,  40)
    _BTN_COLOR       = (40,  40,  75)
    _BTN_HOVER_COLOR = (70,  70, 120)
    _BTN_BORDER      = (160, 160, 255)
    _TITLE_COLOR     = (255, 220,  60)
    _SUBTITLE_COLOR  = (130, 130, 160)
    _EXIT_COLOR      = (180,  60,  60)
    _EXIT_HOVER      = (220,  80,  80)

    _hub: HubView = None

    @classmethod
    def get_hub(cls) -> HubView:
        if cls._hub is None:
            cls._hub = HubView()
        return cls._hub

    @classmethod
    def reset(cls):
        cls._hub = None

    @staticmethod
    def draw_menu(view):
        M         = MainMenu
        screen    = view.screen
        W, H      = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(M._BG_COLOR)

        title_font    = pygame.font.SysFont("Arial", 56, bold=True)
        subtitle_font = pygame.font.SysFont("Arial", 24)
        btn_font      = pygame.font.SysFont("Arial", 28, bold=True)

        # Центральная панель
        panel = pygame.Rect(W // 2 - 340, H // 2 - 320, 680, 640)
        pygame.draw.rect(screen, M._PANEL_COLOR, panel, border_radius=18)
        pygame.draw.rect(screen, M._BTN_BORDER,  panel, 2, border_radius=18)

        # Заголовок
        title = title_font.render("ROGUELIKE CARD GAME", True, M._TITLE_COLOR)
        screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 270))

        sub = subtitle_font.render("Pre-Alpha Edition v0.3", True, M._SUBTITLE_COLOR)
        screen.blit(sub, (W // 2 - sub.get_width() // 2, H // 2 - 200))

        # Разделитель
        pygame.draw.line(screen, M._BTN_BORDER,
                         (W // 2 - 260, H // 2 - 160),
                         (W // 2 + 260, H // 2 - 160), 1)

        # Есть ли сохранённый забег → показываем «Продолжить» первой кнопкой и сдвигаем
        # остальные вниз (иначе обычный layout трёх кнопок).
        from managers import RunSave
        has_run = RunSave.has_saved_run()
        view.btn_menu_continue = None
        y = H // 2 - 130
        if has_run:
            view.btn_menu_continue = pygame.Rect(W // 2 - 260, y, 520, 64)
            cont_hover = view.btn_menu_continue.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (40, 90, 50) if cont_hover else (28, 64, 36),
                             view.btn_menu_continue, border_radius=12)
            pygame.draw.rect(screen, (110, 220, 130), view.btn_menu_continue, 2,
                             border_radius=12)
            lbl = btn_font.render("ПРОДОЛЖИТЬ ЗАБЕГ", True, (220, 255, 220))
            screen.blit(lbl, (view.btn_menu_continue.centerx - lbl.get_width() // 2,
                               view.btn_menu_continue.centery - lbl.get_height() // 2))
            y += 84

        # Кнопка ВОЙТИ В ЛАГЕРЬ
        view.btn_menu_play = pygame.Rect(W // 2 - 260, y, 520, 64)
        MainMenu.is_play_hovered = view.btn_menu_play.collidepoint(mouse_pos)
        col = M._BTN_HOVER_COLOR if MainMenu.is_play_hovered else M._BTN_COLOR
        pygame.draw.rect(screen, col, view.btn_menu_play, border_radius=12)
        pygame.draw.rect(screen, M._BTN_BORDER, view.btn_menu_play, 2, border_radius=12)
        lbl = btn_font.render("ВОЙТИ В ЛАГЕРЬ", True, (255, 255, 255))
        screen.blit(lbl, (view.btn_menu_play.centerx - lbl.get_width() // 2,
                           view.btn_menu_play.centery - lbl.get_height() // 2))
        y += 84

        # Кнопка КАРТЫ
        view.btn_menu_cards = pygame.Rect(W // 2 - 260, y, 520, 64)
        MainMenu.is_cards_hovered = view.btn_menu_cards.collidepoint(mouse_pos)
        col = M._BTN_HOVER_COLOR if MainMenu.is_cards_hovered else M._BTN_COLOR
        pygame.draw.rect(screen, col, view.btn_menu_cards, border_radius=12)
        pygame.draw.rect(screen, M._BTN_BORDER, view.btn_menu_cards, 2, border_radius=12)
        lbl = btn_font.render("БИБЛИОТЕКА КАРТ", True, (255, 255, 255))
        screen.blit(lbl, (view.btn_menu_cards.centerx - lbl.get_width() // 2,
                           view.btn_menu_cards.centery - lbl.get_height() // 2))
        y += 84

        # Небольшая угловая кнопка БИБЛИОТЕКА АРТЕФАКТОВ (верх-право, инструмент ревизии).
        small_font = pygame.font.SysFont("Arial", 18, bold=True)
        view.btn_menu_relics = pygame.Rect(W - 236, 24, 212, 46)
        rel_hover = view.btn_menu_relics.collidepoint(mouse_pos)
        pygame.draw.rect(screen, M._BTN_HOVER_COLOR if rel_hover else M._BTN_COLOR,
                         view.btn_menu_relics, border_radius=10)
        pygame.draw.rect(screen, M._BTN_BORDER, view.btn_menu_relics, 2, border_radius=10)
        rlbl = small_font.render("АРТЕФАКТЫ", True, (235, 235, 255))
        screen.blit(rlbl, (view.btn_menu_relics.centerx - rlbl.get_width() // 2,
                           view.btn_menu_relics.centery - rlbl.get_height() // 2))

        # Кнопка ВЫХОД
        view.btn_menu_exit = pygame.Rect(W // 2 - 260, y, 520, 64)
        MainMenu.is_exit_hovered = view.btn_menu_exit.collidepoint(mouse_pos)
        col = (100, 35, 35) if MainMenu.is_exit_hovered else (60, 20, 20)
        pygame.draw.rect(screen, col, view.btn_menu_exit, border_radius=12)
        pygame.draw.rect(screen, M._EXIT_COLOR, view.btn_menu_exit, 2, border_radius=12)
        lbl = btn_font.render("ВЫХОД", True, M._EXIT_COLOR)
        screen.blit(lbl, (view.btn_menu_exit.centerx - lbl.get_width() // 2,
                           view.btn_menu_exit.centery - lbl.get_height() // 2))

    @staticmethod
    def draw_hub(view):
        MainMenu.get_hub().draw(view)

    @staticmethod
    def handle_clicks(view, mouse_pos):
        if view.gm.current_state == "MAIN_MENU":
            cont = getattr(view, 'btn_menu_continue', None)
            if cont is not None and cont.collidepoint(mouse_pos):
                from managers import RunSave
                data = RunSave.load_run()
                if data is not None and RunSave.restore_run(view.gm, data):
                    print("[МЕНЮ] Забег восстановлен → MAP")
                return
            if hasattr(view, 'btn_menu_play') and view.btn_menu_play.collidepoint(mouse_pos):
                view.gm.current_state = "HUB"
            elif hasattr(view, 'btn_menu_cards') and view.btn_menu_cards.collidepoint(mouse_pos):
                from ui.library import CardLibraryView
                CardLibraryView.reset()
                view.gm.current_state = "CARD_LIBRARY"
            elif hasattr(view, 'btn_menu_relics') and view.btn_menu_relics.collidepoint(mouse_pos):
                from ui.relic_library import RelicLibraryView
                RelicLibraryView.reset()
                view.gm.current_state = "RELIC_LIBRARY"
            elif hasattr(view, 'btn_menu_exit') and view.btn_menu_exit.collidepoint(mouse_pos):
                pygame.quit()
                sys.exit()

        elif view.gm.current_state == "HUB":
            MainMenu.get_hub().handle_click(view, mouse_pos)