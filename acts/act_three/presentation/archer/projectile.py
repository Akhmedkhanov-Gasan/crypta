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
        (9, 35, 21, 125),
        (7, 25),
        (24, 8),
        5,
    )
    pygame.draw.line(
        surface,
        (92, 172, 106),
        (7, 25),
        (24, 8),
        2,
    )
    pygame.draw.polygon(
        surface,
        (177, 224, 176),
        ((27, 5), (17, 8), (24, 15)),
    )
    pygame.draw.line(
        surface,
        (67, 121, 79),
        (10, 22),
        (5, 21),
        2,
    )
    pygame.draw.line(
        surface,
        (67, 121, 79),
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
    progress = max(0.0, min(1.0, progress))
    dx = destination[0] - origin[0]
    dy = destination[1] - origin[1]
    length = max(1.0, math.hypot(dx, dy))
    direction = (dx / length, dy / length)
    normal = (-direction[1], direction[0])
    head = (
        origin[0] + dx * progress,
        origin[1] + dy * progress,
    )
    pad = round(tile_size * 0.7)
    left = math.floor(min(origin[0], head[0])) - pad
    top = math.floor(min(origin[1], head[1])) - pad
    right = math.ceil(max(origin[0], head[0])) + pad
    bottom = math.ceil(max(origin[1], head[1])) + pad
    layer = pygame.Surface(
        (right - left, bottom - top),
        pygame.SRCALPHA,
    )

    def local(position):
        return (
            round(position[0] - left),
            round(position[1] - top),
        )

    def arrow_point(back, side):
        return local(
            (
                head[0] - direction[0] * back + normal[0] * side,
                head[1] - direction[1] * back + normal[1] * side,
            )
        )

    trail_progress = max(0.0, progress - 0.24)
    trail_start = (
        origin[0] + dx * trail_progress,
        origin[1] + dy * trail_progress,
    )
    for color, width in (
        ((4, 19, 12, 105), 22),
        ((15, 61, 35, 150), 13),
        ((54, 132, 73, 160), 5),
    ):
        pygame.draw.line(
            layer,
            color,
            local(trail_start),
            local(head),
            width,
        )

    silhouette = [
        arrow_point(-tile_size * 0.13, 0),
        arrow_point(tile_size * 0.19, tile_size * 0.16),
        arrow_point(tile_size * 0.28, tile_size * 0.09),
        arrow_point(tile_size * 0.57, tile_size * 0.08),
        arrow_point(tile_size * 0.57, -tile_size * 0.08),
        arrow_point(tile_size * 0.28, -tile_size * 0.09),
        arrow_point(tile_size * 0.19, -tile_size * 0.16),
    ]
    pygame.draw.polygon(
        layer,
        (5, 25, 15, 235),
        silhouette,
    )
    pygame.draw.lines(
        layer,
        (70, 169, 94, 220),
        False,
        silhouette[:4],
        2,
    )
    pygame.draw.lines(
        layer,
        (70, 169, 94, 220),
        False,
        silhouette[4:] + silhouette[:1],
        2,
    )
    pygame.draw.line(
        layer,
        (178, 222, 170, 220),
        arrow_point(tile_size * 0.36, 0),
        arrow_point(-tile_size * 0.07, 0),
        2,
    )

    for index in range(3):
        distance = tile_size * (0.25 + index * 0.11)
        side = tile_size * (0.11 + index * 0.045)
        sign = -1 if index % 2 else 1
        pygame.draw.lines(
            layer,
            (43, 116, 66, 150 - index * 30),
            False,
            (
                arrow_point(distance + tile_size * 0.13, 0),
                arrow_point(distance, side * sign),
                arrow_point(distance - tile_size * 0.08, side * sign),
            ),
            2,
        )

    if progress < 0.24:
        burst = progress / 0.24
        radius = round(tile_size * (0.16 + burst * 0.35))
        alpha = round(195 * (1 - burst))
        ring = pygame.Rect(0, 0, radius * 2, radius * 2)
        ring.center = local(origin)
        for index in range(3):
            start = index * math.tau / 3 + 0.2
            pygame.draw.arc(
                layer,
                (68, 161, 87, alpha),
                ring,
                start,
                start + 0.8,
                3,
            )

    surface.blit(layer, (left, top))


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
            (65, 153, 82, alpha),
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
            (30, 89, 49, alpha),
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
