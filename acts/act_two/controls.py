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

AUTO_MOVE_INTERVAL_MS = 175


def visual_direction(direction):
    column_change, row_change = direction

    if row_change:
        return 0, 1 if row_change > 0 else -1

    if column_change:
        return 1 if column_change > 0 else -1, 0

    return 0, 1