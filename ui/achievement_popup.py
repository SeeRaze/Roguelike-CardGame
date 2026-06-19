# ui/achievement_popup.py
# Поп-апы «Достижение открыто!» (С70 Этап 4). Подписывается на шину
# meta_events.achievement_unlocked → накапливает очередь, отрисовывает
# баннер сверху экрана с автозатуханием. Поверх любого state'а (бой/хаб/карта).
#
# Чистый UI-слой: не лезет в мету, читает только payload события (ach_id, ach).
# Идемпотентен: register_handlers() безопасно вызывать многократно.

import time
import pygame

from core import meta_events


# Длительность показа одного баннера на экране (сек).
DISPLAY_SECONDS = 4.0
# Длительность fade-in/out (сек).
FADE_SECONDS    = 0.4


_queue: list = []          # [{'ach': AchievementDef, 'shown_at': float}]
_registered = False


def _on_unlocked(ach_id=None, ach=None, **_extra):
    if ach is None:
        return
    _queue.append({"ach": ach, "shown_at": time.monotonic()})


def register_handlers() -> None:
    global _registered
    if _registered:
        return
    meta_events.subscribe("achievement_unlocked", _on_unlocked)
    _registered = True


def _reset_for_tests() -> None:
    global _registered
    _registered = False
    _queue.clear()


def draw(screen) -> None:
    """Отрисовать активный баннер (если есть). Вызывается из GameView ПОСЛЕ
    основной отрисовки кадра — баннер ложится поверх любого state'а."""
    if not _queue:
        return
    now = time.monotonic()
    head = _queue[0]
    age  = now - head["shown_at"]
    if age >= DISPLAY_SECONDS:
        _queue.pop(0)
        return

    # Альфа: fade-in первые FADE_SECONDS, full в середине, fade-out последние.
    if age < FADE_SECONDS:
        alpha = int(255 * (age / FADE_SECONDS))
    elif age > DISPLAY_SECONDS - FADE_SECONDS:
        alpha = int(255 * ((DISPLAY_SECONDS - age) / FADE_SECONDS))
    else:
        alpha = 255
    alpha = max(0, min(255, alpha))

    ach = head["ach"]
    sw  = screen.get_width()

    banner_w, banner_h = 720, 110
    x = (sw - banner_w) // 2
    y = 30
    surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (40, 70, 30, alpha),       surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (140, 240, 140, alpha),    surf.get_rect(), 3, border_radius=10)

    f_h = pygame.font.SysFont("Arial", 22, bold=True)
    f_t = pygame.font.SysFont("Arial", 18, bold=True)
    f_d = pygame.font.SysFont("Arial", 16)

    title = f_h.render("ДОСТИЖЕНИЕ ОТКРЫТО!", True, (255, 230, 120))
    surf.blit(title, (20, 10))

    name = f_t.render(ach.title, True, (255, 255, 255))
    surf.blit(name, (20, 42))

    desc_line = f"Награда: {ach.grant_id}  ({ach.grant_kind})"
    desc = f_d.render(desc_line, True, (200, 240, 200))
    surf.blit(desc, (20, 76))

    surf.set_alpha(alpha)
    screen.blit(surf, (x, y))
