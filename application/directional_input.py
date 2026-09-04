import pygame


DIRECTION_BY_KEY = {
    pygame.K_w: (0, -1),
    pygame.K_UP: (0, -1),
    pygame.K_s: (0, 1),
    pygame.K_DOWN: (0, 1),
    pygame.K_a: (-1, 0),
    pygame.K_LEFT: (-1, 0),
    pygame.K_d: (1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_KP7: (-1, -1),
    pygame.K_KP8: (0, -1),
    pygame.K_KP9: (1, -1),
    pygame.K_KP4: (-1, 0),
    pygame.K_KP6: (1, 0),
    pygame.K_KP1: (-1, 1),
    pygame.K_KP2: (0, 1),
    pygame.K_KP3: (1, 1),
}

CHORD_MOVEMENT_KEYS = frozenset(
    (
        pygame.K_w,
        pygame.K_a,
        pygame.K_s,
        pygame.K_d,
        pygame.K_UP,
        pygame.K_LEFT,
        pygame.K_DOWN,
        pygame.K_RIGHT,
    )
)

IMMEDIATE_MOVEMENT_KEYS = frozenset(
    (
        pygame.K_KP1,
        pygame.K_KP2,
        pygame.K_KP3,
        pygame.K_KP4,
        pygame.K_KP6,
        pygame.K_KP7,
        pygame.K_KP8,
        pygame.K_KP9,
    )
)

MOVEMENT_KEYS = frozenset(DIRECTION_BY_KEY)

WAIT_KEYS = frozenset(
    (
        pygame.K_SPACE,
        pygame.K_KP0,
        pygame.K_KP5,
    )
)


def movement_direction_for_key(key):
    return DIRECTION_BY_KEY.get(key)


def movement_direction_for_keys(keys):
    directions = [
        DIRECTION_BY_KEY[key]
        for key in keys
        if key in DIRECTION_BY_KEY
    ]

    column_change = sum(
        direction[0]
        for direction in directions
    )
    row_change = sum(
        direction[1]
        for direction in directions
    )

    return (
        max(-1, min(1, column_change)),
        max(-1, min(1, row_change)),
    )
