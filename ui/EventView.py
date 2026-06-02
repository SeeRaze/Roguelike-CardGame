import pygame
from ui.events.event_data    import get_random_event
from ui.events.event_effects import apply_option

# ─── Состояние ──────────────────────────────────────────────────────────────
_current_event = None
_option_rects  = []   # [(tag, pygame.Rect)]

# ─── Цвета ──────────────────────────────────────────────────────────────────
_BG_COLOR        = (15,  15,  25)
_PANEL_COLOR     = (25,  25,  45)
_BTN_COLOR       = (50,  50,  80)
_BTN_HOVER_COLOR = (80,  80, 130)
_BTN_BORDER      = (180, 180, 255)
_TITLE_COLOR     = (255, 220,  60)
_TEXT_COLOR      = (210, 210, 210)
_RESULT_COLOR    = (100, 220, 100)


def init_event(gm):
    global _current_event
    _current_event  = get_random_event()
    gm.event_result = None


def reset():
    global _current_event
    _current_event = None


def draw_screen(view):
    global _option_rects

    if _current_event is None:
        init_event(view.gm)

    screen = view.screen
    W, H   = screen.get_size()
    mouse  = pygame.mouse.get_pos()
    screen.fill(_BG_COLOR)

    panel = pygame.Rect(W // 2 - 480, 80, 960, 900)
    pygame.draw.rect(screen, _PANEL_COLOR, panel, border_radius=16)
    pygame.draw.rect(screen, _BTN_BORDER,  panel, 2, border_radius=16)

    title_font = pygame.font.SysFont("Arial", 42, bold=True)
    title_surf = title_font.render(_current_event["title"], True, _TITLE_COLOR)
    screen.blit(title_surf, (W // 2 - title_surf.get_width() // 2, 120))

    text_font = pygame.font.SysFont("Arial", 26)
    y = 210
    for line in _current_event["text"].split("\n"):
        surf = text_font.render(line, True, _TEXT_COLOR)
        screen.blit(surf, (W // 2 - surf.get_width() // 2, y))
        y += 38

    _option_rects.clear()
    btn_font = pygame.font.SysFont("Arial", 24, bold=True)

    if getattr(view.gm, "event_result", None):
        res_font = pygame.font.SysFont("Arial", 32, bold=True)
        res_surf = res_font.render(view.gm.event_result, True, _RESULT_COLOR)
        screen.blit(res_surf, (W // 2 - res_surf.get_width() // 2, y + 30))

        cont_rect = pygame.Rect(W // 2 - 160, y + 100, 320, 60)
        hover = cont_rect.collidepoint(mouse)
        pygame.draw.rect(screen, _BTN_HOVER_COLOR if hover else _BTN_COLOR, cont_rect, border_radius=10)
        pygame.draw.rect(screen, _BTN_BORDER, cont_rect, 2, border_radius=10)
        lbl = btn_font.render("Продолжить ->", True, (255, 255, 255))
        screen.blit(lbl, (cont_rect.centerx - lbl.get_width() // 2,
                          cont_rect.centery - lbl.get_height() // 2))
        _option_rects.append(("continue", cont_rect))
        return

    y += 60
    for i, opt in enumerate(_current_event["options"]):
        btn_rect = pygame.Rect(W // 2 - 380, y, 760, 64)
        hover = btn_rect.collidepoint(mouse)
        pygame.draw.rect(screen, _BTN_HOVER_COLOR if hover else _BTN_COLOR, btn_rect, border_radius=10)
        pygame.draw.rect(screen, _BTN_BORDER, btn_rect, 2, border_radius=10)
        lbl = btn_font.render(opt["label"], True, (255, 255, 255))
        screen.blit(lbl, (btn_rect.centerx - lbl.get_width() // 2,
                          btn_rect.centery - lbl.get_height() // 2))
        _option_rects.append((i, btn_rect))
        y += 84


def handle_clicks(view, mouse_pos):
    if _current_event is None:
        return

    for tag, rect in _option_rects:
        if rect.collidepoint(mouse_pos):
            if tag == "continue":
                reset()
                view.gm.event_result = None
                view.gm.current_floor += 1
                view.gm.setup_next_floor()
                return
            apply_option(_current_event["options"][tag], view.gm)
            return