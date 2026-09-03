import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


def draw_act_one_crate(screen, crate):
    x = MAP_OFFSET_X + crate.column * TILE_SIZE
    y = MAP_OFFSET_Y + crate.row * TILE_SIZE

    if crate.is_broken:
        for start, end in (
            ((x + 3, y + 24), (x + 10, y + 27)),
            ((x + 22, y + 26), (x + 29, y + 22)),
            ((x + 4, y + 8), (x + 8, y + 12)),
            ((x + 24, y + 7), (x + 28, y + 11)),
        ):
            pygame.draw.line(screen, (31, 24, 22), start, end, 4)
            pygame.draw.line(screen, (109, 77, 49), start, end, 2)
        return

    pygame.draw.ellipse(
        screen,
        (13, 13, 17),
        (x + 2, y + 23, 29, 8),
    )

    pygame.draw.polygon(
        screen,
        (41, 29, 24),
        (
            (x + 3, y + 7),
            (x + 7, y + 3),
            (x + 28, y + 3),
            (x + 30, y + 7),
            (x + 30, y + 27),
            (x + 26, y + 30),
            (x + 3, y + 30),
        ),
    )

    pygame.draw.polygon(
        screen,
        (143, 104, 65),
        (
            (x + 5, y + 7),
            (x + 8, y + 4),
            (x + 27, y + 4),
            (x + 25, y + 7),
        ),
    )

    pygame.draw.polygon(
        screen,
        (67, 46, 33),
        (
            (x + 26, y + 8),
            (x + 29, y + 6),
            (x + 29, y + 26),
            (x + 26, y + 28),
        ),
    )

    front = pygame.Rect(x + 4, y + 8, 22, 21)
    pygame.draw.rect(screen, (111, 77, 48), front)

    for offset in (7, 14):
        pygame.draw.line(
            screen,
            (63, 43, 32),
            (front.left + offset, front.top + 1),
            (front.left + offset, front.bottom - 2),
        )
        pygame.draw.line(
            screen,
            (136, 94, 57),
            (front.left + offset + 1, front.top + 1),
            (front.left + offset + 1, front.bottom - 2),
        )

    pygame.draw.rect(screen, (165, 120, 73), front, width=2)

    brace_start = (front.left + 3, front.bottom - 4)
    brace_end = (front.right - 4, front.top + 3)

    pygame.draw.line(screen, (62, 42, 30), brace_start, brace_end, 5)
    pygame.draw.line(screen, (177, 129, 78), brace_start, brace_end, 3)

    for nail in (
        (front.left + 2, front.top + 2),
        (front.right - 3, front.top + 2),
        (front.left + 2, front.bottom - 3),
        (front.right - 3, front.bottom - 3),
    ):
        pygame.draw.rect(
            screen,
            (47, 43, 42),
            (nail[0], nail[1], 2, 2),
        )
