import pygame

from presentation.layout import (
    ACT_TWO_VIEW_HEIGHT,
    ACT_TWO_VIEW_WIDTH,
    ACT_TWO_VIEW_X,
    ACT_TWO_VIEW_Y,
)


def draw_frame(screen):
    outer_rectangle = pygame.Rect(
        ACT_TWO_VIEW_X - 4,
        ACT_TWO_VIEW_Y - 4,
        ACT_TWO_VIEW_WIDTH + 8,
        ACT_TWO_VIEW_HEIGHT + 8,
    )
    pygame.draw.rect(
        screen,
        (8, 10, 14),
        outer_rectangle.inflate(6, 6),
        width=5,
    )
    pygame.draw.rect(screen, (58, 76, 79), outer_rectangle, width=3)
    pygame.draw.rect(
        screen,
        (30, 27, 34),
        outer_rectangle.inflate(-6, -6),
        width=1,
    )
    pygame.draw.line(
        screen,
        (99, 112, 108),
        outer_rectangle.topleft,
        outer_rectangle.topright,
    )
    for corner in (
        outer_rectangle.topleft,
        outer_rectangle.topright,
        outer_rectangle.bottomleft,
        outer_rectangle.bottomright,
    ):
        pygame.draw.circle(screen, (13, 17, 21), corner, 5)
        pygame.draw.circle(screen, (75, 92, 92), corner, 2)
