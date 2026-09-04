"""Keyboard bindings and movement input rules owned by Act Two."""

import pygame


CONSUMABLE_KEY_ORDER = (
    pygame.K_1,
    pygame.K_2,
    pygame.K_3,
    pygame.K_4,
    pygame.K_5,
    pygame.K_6,
)
CONSUMABLE_KEYS = {
    key: slot_index
    for slot_index, key in enumerate(CONSUMABLE_KEY_ORDER)
}
MOVEMENT_KEYS = frozenset(
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
MOVE_REPEAT_DELAY_MS = 190
MOVE_REPEAT_INTERVAL_MS = 175


def movement_direction_for_keys(keys):
    left = bool(keys & {pygame.K_a, pygame.K_LEFT})
    right = bool(keys & {pygame.K_d, pygame.K_RIGHT})
    up = bool(keys & {pygame.K_w, pygame.K_UP})
    down = bool(keys & {pygame.K_s, pygame.K_DOWN})
    return int(right) - int(left), int(down) - int(up)


def visual_direction(direction):
    column_change, row_change = direction
    if row_change:
        return 0, 1 if row_change > 0 else -1
    if column_change:
        return 1 if column_change > 0 else -1, 0
    return 0, 1
