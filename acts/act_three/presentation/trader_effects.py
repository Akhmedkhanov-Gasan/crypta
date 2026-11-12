import math
from functools import lru_cache

import pygame

from presentation.movement import smoothstep


PRESS_MS = 170
PURCHASE_MS = 460
_BRONZE = (166, 115, 69)
_HOVER_BRONZE = (184, 132, 81)
_EMBER = (180, 102, 62)
_OXBLOOD = (92, 39, 39)


def trader_press_offset(elapsed, purchased):
    if elapsed is None or elapsed >= PRESS_MS:
        return 0, 0
    if elapsed < 38:
        depth = smoothstep(elapsed / 38)
    else:
        depth = 1 - smoothstep((elapsed - 38) / (PRESS_MS - 38))
    if purchased:
        rebound = math.sin(math.pi * smoothstep((elapsed - 69) / 101))
        return round(depth * 3 - rebound * 2), round(depth * 3 - rebound)
    return 0, round(depth * 2)


@lru_cache(maxsize=16)
def _edge_glow(size, color):
    glow = pygame.Surface(size, pygame.SRCALPHA)
    rect = glow.get_rect().inflate(-4, -4)
    for width in range(10, 0, -1):
        pygame.draw.rect(glow, (*color, 12 + (10 - width) * 7), rect, width, border_radius=9)
    return glow


def draw_trader_slot_effect(screen, rect, hovered, elapsed, purchased, current_time):
    if hovered:
        glow = _edge_glow(rect.size, _HOVER_BRONZE).copy()
        glow.set_alpha(round(176 + 16 * math.sin(current_time / 310)))
        screen.blit(glow, rect)

    if elapsed is None or elapsed >= PURCHASE_MS:
        return
    if not purchased:
        strength = 1 - smoothstep(elapsed / PRESS_MS)
        if strength > 0:
            glow = _edge_glow(rect.size, _OXBLOOD).copy()
            glow.set_alpha(round(170 * strength))
            screen.blit(glow, rect)
        return

    progress = elapsed / PURCHASE_MS
    glow = _edge_glow(rect.size, _EMBER).copy()
    glow.set_alpha(round(225 * (1 - progress) ** 2))
    screen.blit(glow, rect)

    embers = pygame.Surface(rect.size, pygame.SRCALPHA)
    for index in range(7):
        age = elapsed - index * 18
        if not 0 <= age < 320:
            continue
        drift = age / 320
        x = rect.width - 32 - index * 11 - (20 + index * 4) * drift
        y = rect.height - 17 - (24 + index % 3 * 9) * drift
        alpha = round(168 * (1 - drift) ** 1.7)
        pygame.draw.line(
            embers, (*_BRONZE, alpha // 2),
            (round(x + 3), round(y + 3)), (round(x), round(y)),
        )
        pygame.draw.circle(embers, (*_EMBER, alpha), (round(x), round(y)), 1 + (index % 3 == 0))
    screen.blit(embers, rect)
