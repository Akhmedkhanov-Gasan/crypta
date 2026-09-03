from functools import lru_cache

import pygame


POTION_PICKUP_COLORS = (
    (175, 54, 65),
    (242, 131, 133),
)


@lru_cache(maxsize=1)
def _potion_surface():
    surface = pygame.Surface((28, 36), pygame.SRCALPHA)
    x, y = 14, 18

    body = pygame.Rect(x - 9, y - 8, 18, 23)

    pygame.draw.rect(
        surface,
        (7, 8, 12),
        body.inflate(4, 4),
        border_radius=5,
    )
    pygame.draw.rect(
        surface,
        (98, 30, 42),
        body,
        border_radius=4,
    )
    pygame.draw.rect(
        surface,
        (175, 54, 65),
        (x - 6, y, 12, 12),
        border_radius=2,
    )
    pygame.draw.rect(
        surface,
        (214, 190, 143),
        (x - 5, y - 16, 10, 5),
    )
    pygame.draw.rect(
        surface,
        (92, 91, 100),
        (x - 5, y - 11, 10, 5),
    )
    pygame.draw.line(
        surface,
        (236, 213, 189),
        (x - 4, y - 4),
        (x - 4, y + 6),
        2,
    )

    return surface


def draw_potion_icon(screen, center, alpha=255):
    surface = _potion_surface()

    if alpha < 255:
        surface = surface.copy()
        surface.set_alpha(max(0, min(255, alpha)))

    screen.blit(surface, surface.get_rect(center=center))
