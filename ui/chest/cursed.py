import pygame
from ui.chest.shared import draw_leave_button

_HP_COLOR   = (220,  80,  80)
_TEXT_COLOR = (200, 200, 200)


def draw_cursed(view, screen, sub_font, card_font, desc_font):
    gm    = view.gm
    buffs = getattr(gm, "cursed_buffs", [])
    taken = getattr(gm, "cursed_taken", set())
    mouse = pygame.mouse.get_pos()

    hint = sub_font.render(
        "Выбери баффы. Каждый стоит HP. Можно взять несколько.",
        True, (200, 160, 255)
    )
    screen.blit(hint, (960 - hint.get_width() // 2, 115))

    hp_surf = sub_font.render(
        f"HP: {gm.player.hp} / {gm.player.max_hp}",
        True, _HP_COLOR
    )
    screen.blit(hp_surf, (960 - hp_surf.get_width() // 2, 155))

    card_w, card_h = 260, 160
    spacing        = 300
    count          = len(buffs)
    total_w        = count * spacing
    start_x        = 960 - total_w // 2 + spacing // 2 - card_w // 2

    for i, (name, desc, cost, _apply) in enumerate(buffs):
        cx   = start_x + i * spacing
        cy   = 280
        rect = pygame.Rect(cx, cy, card_w, card_h)

        is_taken   = (i in taken)
        is_hovered = rect.collidepoint(mouse) and not is_taken
        can_afford = gm.player.hp - cost >= 1

        if is_taken:
            bg_color, border_color, border_w = (25, 40, 25), (60, 120, 60), 2
        elif is_hovered and can_afford:
            bg_color, border_color, border_w = (60, 30, 80), (220, 100, 255), 3
        elif not can_afford:
            bg_color, border_color, border_w = (30, 20, 30), (80, 50, 80), 1
        else:
            bg_color, border_color, border_w = (35, 20, 50), (140, 60, 200), 2

        pygame.draw.rect(screen, bg_color,     rect, border_radius=8)
        pygame.draw.rect(screen, border_color, rect, border_w, border_radius=8)

        name_color = (180, 255, 180) if is_taken else (220, 180, 255)
        n = card_font.render(name, True, name_color)
        screen.blit(n, (rect.centerx - n.get_width() // 2, cy + 14))

        d = desc_font.render(desc, True, (170, 170, 190))
        screen.blit(d, (rect.centerx - d.get_width() // 2, cy + 56))

        if is_taken:
            s = card_font.render("ВЗЯТО", True, (100, 220, 100))
            screen.blit(s, (rect.centerx - s.get_width() // 2, cy + 100))
        else:
            cost_color = (220, 80, 80) if not can_afford else (255, 120, 120)
            cs = card_font.render(f"-{cost} HP", True, cost_color)
            screen.blit(cs, (rect.centerx - cs.get_width() // 2, cy + 100))
            if not can_afford:
                w = desc_font.render("Недостаточно HP", True, (160, 80, 80))
                screen.blit(w, (rect.centerx - w.get_width() // 2, cy + 130))

    draw_leave_button(view, screen, card_font, y=520)


def clicks_cursed(view, mouse_pos):
    gm    = view.gm
    buffs = getattr(gm, "cursed_buffs", [])
    taken = getattr(gm, "cursed_taken", set())

    card_w, card_h = 260, 160
    spacing        = 300
    count          = len(buffs)
    total_w        = count * spacing
    start_x        = 960 - total_w // 2 + spacing // 2 - card_w // 2

    for i, (name, desc, cost, apply_fn) in enumerate(buffs):
        if i in taken:
            continue
        rect = pygame.Rect(start_x + i * spacing, 280, card_w, card_h)
        if rect.collidepoint(mouse_pos):
            if gm.player.hp - cost >= 1:
                gm.player.hp -= cost
                apply_fn(gm)
                taken.add(i)
                gm.cursed_taken = taken
            return

    if pygame.Rect(760, 520, 400, 60).collidepoint(mouse_pos):
        gm.current_floor += 1
        gm.setup_next_floor()