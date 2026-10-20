import pygame

from acts.act_one.presentation.enemies.motion import (
    stepped_attack_offset,
)
from settings import TILE_SIZE


GOBLIN_ATTACK_DURATION_MS = 260
GOBLIN_ATTACK_FRAME_START_MS = 80
GOBLIN_ATTACK_FRAME_END_MS = 190
GOBLIN_DEATH_DURATION_MS = 360


def _lighter(color, amount):
    return tuple(
        min(255, channel + amount)
        for channel in color
    )


def _darker(color, amount):
    return tuple(
        max(8, channel - amount)
        for channel in color
    )


def goblin_attack_offset(enemy, current_time):
    return stepped_attack_offset(
        enemy,
        current_time,
        "goblin",
        GOBLIN_ATTACK_FRAME_START_MS,
        GOBLIN_ATTACK_FRAME_END_MS,
        5,
    )


def draw_goblin(
    screen,
    x,
    y,
    size,
    color,
    is_aggro,
):
    center_x = x + size // 2
    top = y + 3
    floor_y = y + size - 1

    skin = color
    skin_light = _lighter(color, 17)
    skin_shadow = _darker(color, 29)
    skin_deep_shadow = _darker(color, 47)
    cloth = (27, 21, 24)
    cloth_light = (43, 28, 31)
    leather = (76, 47, 32)
    eye = (
        (207, 101, 68)
        if is_aggro
        else (101, 67, 58)
    )

    pygame.draw.line(
        screen,
        (21, 19, 21),
        (center_x - 3, top + 11),
        (center_x - 4, floor_y),
        3,
    )
    pygame.draw.line(
        screen,
        (18, 17, 19),
        (center_x + 2, top + 11),
        (center_x + 4, floor_y),
        3,
    )
    pygame.draw.line(
        screen,
        (47, 37, 33),
        (center_x - 6, floor_y),
        (center_x - 2, floor_y),
        2,
    )
    pygame.draw.line(
        screen,
        (47, 37, 33),
        (center_x + 2, floor_y),
        (center_x + 6, floor_y),
        2,
    )

    pygame.draw.polygon(
        screen,
        cloth,
        (
            (center_x - 4, top + 8),
            (center_x + 4, top + 8),
            (center_x + 5, top + 13),
            (center_x + 2, top + 15),
            (center_x, top + 14),
            (center_x - 3, top + 15),
            (center_x - 5, top + 12),
        ),
    )
    pygame.draw.polygon(
        screen,
        cloth_light,
        (
            (center_x - 3, top + 9),
            (center_x + 2, top + 9),
            (center_x + 2, top + 12),
            (center_x, top + 13),
            (center_x - 3, top + 12),
        ),
    )
    pygame.draw.line(
        screen,
        leather,
        (center_x - 4, top + 12),
        (center_x + 4, top + 12),
        2,
    )

    pygame.draw.polygon(
        screen,
        skin_deep_shadow,
        (
            (center_x - 5, top + 3),
            (x + 1, top + 1),
            (center_x - 4, top + 6),
            (center_x - 5, top + 8),
        ),
    )
    pygame.draw.polygon(
        screen,
        skin_deep_shadow,
        (
            (center_x + 5, top + 3),
            (x + size - 1, top + 1),
            (center_x + 4, top + 6),
            (center_x + 5, top + 8),
        ),
    )
    pygame.draw.polygon(
        screen,
        skin,
        (
            (center_x - 5, top + 2),
            (center_x - 3, top),
            (center_x + 3, top),
            (center_x + 5, top + 2),
            (center_x + 5, top + 7),
            (center_x + 2, top + 10),
            (center_x - 3, top + 9),
            (center_x - 5, top + 6),
        ),
    )
    pygame.draw.polygon(
        screen,
        skin_light,
        (
            (center_x - 3, top + 1),
            (center_x + 2, top + 1),
            (center_x + 4, top + 3),
            (center_x + 2, top + 4),
            (center_x - 3, top + 4),
            (center_x - 4, top + 3),
        ),
    )
    pygame.draw.polygon(
        screen,
        skin_shadow,
        (
            (center_x - 4, top + 5),
            (center_x + 4, top + 5),
            (center_x + 3, top + 8),
            (center_x, top + 9),
            (center_x - 3, top + 8),
        ),
    )
    pygame.draw.rect(
        screen,
        (25, 18, 20),
        (center_x - 3, top + 5, 6, 2),
    )
    pygame.draw.rect(
        screen,
        eye,
        (center_x - 2, top + 5, 1, 1),
    )
    pygame.draw.rect(
        screen,
        eye,
        (center_x + 1, top + 5, 1, 1),
    )
    pygame.draw.rect(
        screen,
        (91, 72, 65),
        (center_x - 1, top + 8, 2, 1),
    )

    weapon_hand = (
        center_x + 4,
        top + 11,
    )
    handle_end = (
        center_x + 7,
        top + 9,
    )
    blade_tip = (
        center_x + 11,
        top + 5,
    )

    pygame.draw.line(
        screen,
        skin_shadow,
        (center_x + 3, top + 9),
        weapon_hand,
        3,
    )
    pygame.draw.line(
        screen,
        leather,
        weapon_hand,
        handle_end,
        3,
    )
    pygame.draw.line(
        screen,
        (126, 76, 44),
        weapon_hand,
        handle_end,
    )
    pygame.draw.line(
        screen,
        (61, 64, 67),
        handle_end,
        blade_tip,
        3,
    )
    pygame.draw.line(
        screen,
        (121, 119, 113),
        handle_end,
        blade_tip,
    )


def draw_goblin_corpse(
    screen,
    center_x,
    center_y,
    color,
):
    floor_y = center_y + TILE_SIZE // 2 - 4
    skin = _darker(color, 15)
    skin_light = _lighter(skin, 12)
    skin_shadow = _darker(color, 40)

    pygame.draw.ellipse(
        screen,
        (6, 6, 8),
        (
            center_x - 11,
            floor_y - 2,
            22,
            5,
        ),
    )

    pygame.draw.line(
        screen,
        (21, 18, 20),
        (center_x - 1, floor_y - 4),
        (center_x + 8, floor_y),
        5,
    )
    pygame.draw.polygon(
        screen,
        (34, 23, 26),
        (
            (center_x - 4, floor_y - 7),
            (center_x + 5, floor_y - 6),
            (center_x + 8, floor_y - 2),
            (center_x + 3, floor_y),
            (center_x - 5, floor_y - 2),
        ),
    )
    pygame.draw.line(
        screen,
        (49, 34, 31),
        (center_x + 5, floor_y - 2),
        (center_x + 10, floor_y),
        3,
    )

    pygame.draw.polygon(
        screen,
        skin_shadow,
        (
            (center_x - 10, floor_y - 7),
            (center_x - 7, floor_y - 9),
            (center_x - 2, floor_y - 7),
            (center_x - 1, floor_y - 3),
            (center_x - 6, floor_y - 2),
            (center_x - 10, floor_y - 4),
        ),
    )
    pygame.draw.polygon(
        screen,
        skin,
        (
            (center_x - 9, floor_y - 7),
            (center_x - 6, floor_y - 8),
            (center_x - 2, floor_y - 6),
            (center_x - 2, floor_y - 4),
            (center_x - 6, floor_y - 3),
            (center_x - 9, floor_y - 4),
        ),
    )
    pygame.draw.line(
        screen,
        skin_light,
        (center_x - 8, floor_y - 7),
        (center_x - 5, floor_y - 6),
    )
    pygame.draw.line(
        screen,
        (27, 18, 20),
        (center_x - 7, floor_y - 4),
        (center_x - 4, floor_y - 4),
    )

    pygame.draw.line(
        screen,
        (73, 44, 30),
        (center_x + 2, floor_y),
        (center_x + 8, floor_y - 3),
        2,
    )
    pygame.draw.line(
        screen,
        (66, 69, 71),
        (center_x + 8, floor_y - 3),
        (center_x + 13, floor_y - 6),
        3,
    )
    pygame.draw.line(
        screen,
        (126, 123, 116),
        (center_x + 8, floor_y - 3),
        (center_x + 13, floor_y - 6),
    )


def draw_goblin_death(
    screen,
    elapsed,
    color,
    center_x,
    center_y,
    is_aggro,
):
    if elapsed < 0:
        return

    if elapsed >= GOBLIN_DEATH_DURATION_MS:
        draw_goblin_corpse(
            screen,
            center_x,
            center_y,
            color,
        )
        return

    progress = elapsed / GOBLIN_DEATH_DURATION_MS
    collapse = progress * progress
    body = pygame.Surface(
        (28, 28),
        pygame.SRCALPHA,
    )
    body_color = (
        (220, 208, 201)
        if elapsed < 70
        else tuple(
            max(12, round(channel * (1.0 - progress * 0.24)))
            for channel in color
        )
    )

    draw_goblin(
        body,
        4,
        4,
        20,
        body_color,
        is_aggro,
    )

    collapsed_width = round(
        28 * (1.0 + collapse * 0.08)
    )
    collapsed_height = max(
        6,
        round(28 * (1.0 - collapse * 0.78)),
    )
    body = pygame.transform.scale(
        body,
        (
            collapsed_width,
            collapsed_height,
        ),
    )

    screen.blit(
        body,
        (
            center_x - collapsed_width // 2,
            center_y + 14 - collapsed_height,
        ),
    )


__all__ = [
    "draw_goblin",
    "draw_goblin_corpse",
    "draw_goblin_death",
    "goblin_attack_offset",
]
