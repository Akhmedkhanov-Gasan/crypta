import math

import pygame


PIERCING_WINDUP_MS = 220
PIERCING_TRAVEL_MS = 380
PIERCING_RECOVERY_MS = 90
PIERCING_TOTAL_MS = (
    PIERCING_WINDUP_MS
    + PIERCING_TRAVEL_MS
    + PIERCING_RECOVERY_MS
)


def make_archer_arrow_sprite():
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)

    pygame.draw.line(
        surface,
        (16, 18, 25, 125),
        (7, 25),
        (24, 8),
        5,
    )
    pygame.draw.line(
        surface,
        (145, 135, 114),
        (7, 25),
        (24, 8),
        2,
    )
    pygame.draw.polygon(
        surface,
        (225, 218, 193),
        ((27, 5), (17, 8), (24, 15)),
    )
    pygame.draw.line(
        surface,
        (85, 76, 98),
        (10, 22),
        (5, 21),
        2,
    )
    pygame.draw.line(
        surface,
        (85, 76, 98),
        (10, 22),
        (11, 27),
        2,
    )
    return surface


def draw_piercing_projectile(
    surface,
    origin,
    destination,
    progress,
    tile_size,
):
    from acts.act_three.presentation.archer.arrows import draw_arrow_flight

    draw_arrow_flight(surface, origin, destination, progress, power=2.0)


def draw_piercing_impact(
    surface,
    center,
    tile_size,
    progress,
):
    size = round(tile_size * 1.7)
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    middle = (size // 2, size // 2)
    radius = tile_size * (0.16 + progress * 0.35)
    alpha = round(210 * (1 - progress))
    ring = pygame.Rect(
        0,
        0,
        round(radius * 2),
        round(radius * 2),
    )
    ring.center = middle

    for index in range(5):
        angle = index * math.tau / 5
        pygame.draw.arc(
            layer,
            (177, 186, 202, alpha),
            ring,
            angle + 0.12,
            angle + 0.79,
            3,
        )
        inner = (
            round(middle[0] + math.cos(angle) * radius * 0.5),
            round(middle[1] + math.sin(angle) * radius * 0.5),
        )
        outer = (
            round(middle[0] + math.cos(angle) * radius * 1.25),
            round(middle[1] + math.sin(angle) * radius * 1.25),
        )
        pygame.draw.line(
            layer,
            (90, 101, 123, alpha),
            inner,
            outer,
            2,
        )

    surface.blit(
        layer,
        (
            round(center[0] - middle[0]),
            round(center[1] - middle[1]),
        ),
    )
