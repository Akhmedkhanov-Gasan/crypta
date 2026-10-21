from functools import lru_cache

import pygame


POTION_PICKUP_COLORS = (
    (175, 54, 65),
    (242, 131, 133),
)


@lru_cache(maxsize=1)
def _potion_surface():
    surface = pygame.Surface((22, 28), pygame.SRCALPHA)

    pygame.draw.ellipse(
        surface,
        (5, 5, 8, 135),
        (4, 23, 15, 4),
    )

    pygame.draw.polygon(
        surface,
        (7, 8, 11),
        (
            (7, 8),
            (15, 8),
            (18, 13),
            (17, 23),
            (14, 26),
            (8, 26),
            (5, 23),
            (4, 13),
        ),
    )
    pygame.draw.polygon(
        surface,
        (92, 30, 39),
        (
            (8, 10),
            (14, 10),
            (16, 14),
            (15, 22),
            (13, 24),
            (9, 24),
            (7, 22),
            (6, 14),
        ),
    )
    pygame.draw.polygon(
        surface,
        (160, 45, 56),
        (
            (6, 17),
            (16, 17),
            (15, 22),
            (13, 24),
            (9, 24),
            (7, 22),
        ),
    )
    pygame.draw.line(
        surface,
        (232, 101, 104),
        (8, 14),
        (8, 21),
        2,
    )
    pygame.draw.line(
        surface,
        (103, 29, 38),
        (14, 13),
        (15, 21),
    )

    pygame.draw.rect(
        surface,
        (30, 31, 34),
        (7, 5, 8, 5),
        border_radius=1,
    )
    pygame.draw.rect(
        surface,
        (116, 105, 91),
        (8, 3, 6, 4),
        border_radius=1,
    )
    pygame.draw.line(
        surface,
        (196, 178, 145),
        (9, 3),
        (13, 3),
    )

    pygame.draw.polygon(
        surface,
        (227, 137, 135),
        (
            (11, 17),
            (13, 19),
            (11, 21),
            (9, 19),
        ),
    )

    return surface


def draw_potion_icon(
    screen,
    center,
    alpha=255,
    scale=1.0,
):
    surface = _potion_surface()

    if scale != 1.0:
        surface = pygame.transform.scale(
            surface,
            (
                max(
                    1,
                    round(
                        surface.get_width() * scale
                    ),
                ),
                max(
                    1,
                    round(
                        surface.get_height() * scale
                    ),
                ),
            ),
        )

    if alpha < 255:
        surface = surface.copy()
        surface.set_alpha(
            max(
                0,
                min(255, alpha),
            )
        )

    screen.blit(
        surface,
        surface.get_rect(center=center),
    )
