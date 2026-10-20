import math

import pygame

from acts.act_one.presentation.enemies.motion import (
    stepped_attack_offset,
)
from settings import TILE_SIZE


BRUTE_MOVE_DURATION_MS = 260
BRUTE_ATTACK_FRAME_START_MS = 105
BRUTE_ATTACK_FRAME_END_MS = 255
BRUTE_DEATH_DURATION_MS = 520


def _lighter(color, amount):
    return tuple(
        min(255, channel + amount)
        for channel in color
    )


def _darker(color, amount):
    return tuple(
        max(7, channel - amount)
        for channel in color
    )


def brute_attack_offset(enemy, current_time):
    return stepped_attack_offset(
        enemy,
        current_time,
        "brute",
        BRUTE_ATTACK_FRAME_START_MS,
        BRUTE_ATTACK_FRAME_END_MS,
        4,
    )


def brute_movement_offset(
    column,
    row,
    origin,
    current_time,
    movement_started_at,
):
    elapsed = current_time - movement_started_at
    if (
        origin is None
        or movement_started_at <= 0
        or not 0 <= elapsed < BRUTE_MOVE_DURATION_MS
    ):
        return 0, 0

    progress = elapsed / BRUTE_MOVE_DURATION_MS
    eased_progress = progress * progress * (3.0 - 2.0 * progress)
    remaining = 1.0 - eased_progress

    offset_x = round(
        (origin[0] - column)
        * TILE_SIZE
        * remaining
    )
    offset_y = round(
        (origin[1] - row)
        * TILE_SIZE
        * remaining
    )
    lift = round(
        math.sin(math.pi * progress) * 3
    )

    if progress > 0.7:
        landing_progress = (progress - 0.7) / 0.3
        offset_y += round(
            math.sin(math.pi * landing_progress) * 3
        )

    return offset_x, offset_y - lift


def draw_brute(
    screen,
    x,
    y,
    size,
    color,
    is_aggro,
):
    center_x = x + size // 2
    top = y + 2
    floor_y = y + size

    stone = _darker(color, 18)
    stone_dark = _darker(color, 43)
    stone_deep = _darker(color, 61)
    stone_light = _lighter(color, 16)
    crack = (
        (211, 80, 38)
        if is_aggro
        else (103, 65, 43)
    )
    crack_light = (
        (241, 125, 54)
        if is_aggro
        else (130, 82, 49)
    )

    pygame.draw.line(
        screen,
        stone_deep,
        (center_x - 5, top + 13),
        (center_x - 6, floor_y),
        5,
    )
    pygame.draw.line(
        screen,
        stone_deep,
        (center_x + 5, top + 13),
        (center_x + 6, floor_y),
        5,
    )
    pygame.draw.line(
        screen,
        (35, 29, 27),
        (center_x - 9, floor_y),
        (center_x - 3, floor_y),
        3,
    )
    pygame.draw.line(
        screen,
        (35, 29, 27),
        (center_x + 3, floor_y),
        (center_x + 9, floor_y),
        3,
    )

    pygame.draw.polygon(
        screen,
        stone_deep,
        (
            (center_x - 8, top + 6),
            (center_x - 5, top + 2),
            (center_x + 5, top + 2),
            (center_x + 8, top + 6),
            (center_x + 8, top + 14),
            (center_x + 4, top + 17),
            (center_x - 5, top + 17),
            (center_x - 8, top + 13),
        ),
    )
    pygame.draw.polygon(
        screen,
        stone,
        (
            (center_x - 6, top + 6),
            (center_x - 4, top + 3),
            (center_x + 4, top + 3),
            (center_x + 6, top + 6),
            (center_x + 6, top + 13),
            (center_x + 3, top + 15),
            (center_x - 4, top + 15),
            (center_x - 6, top + 12),
        ),
    )

    pygame.draw.polygon(
        screen,
        stone_dark,
        (
            (center_x - 8, top + 5),
            (x - 1, top + 8),
            (x + 1, top + 14),
            (center_x - 6, top + 13),
        ),
    )
    pygame.draw.polygon(
        screen,
        stone,
        (
            (center_x - 8, top + 6),
            (x, top + 9),
            (x + 2, top + 13),
            (center_x - 6, top + 12),
        ),
    )

    pygame.draw.polygon(
        screen,
        stone_dark,
        (
            (center_x + 7, top + 5),
            (x + size + 1, top + 7),
            (x + size, top + 13),
            (center_x + 6, top + 13),
        ),
    )
    pygame.draw.polygon(
        screen,
        stone,
        (
            (center_x + 7, top + 6),
            (x + size, top + 8),
            (x + size - 1, top + 12),
            (center_x + 6, top + 12),
        ),
    )

    pygame.draw.polygon(
        screen,
        stone_light,
        (
            (center_x - 4, top + 2),
            (center_x - 1, top),
            (center_x + 4, top + 1),
            (center_x + 6, top + 4),
            (center_x + 3, top + 6),
            (center_x - 4, top + 6),
            (center_x - 6, top + 4),
        ),
    )
    pygame.draw.rect(
        screen,
        (20, 17, 18),
        (
            center_x - 4,
            top + 5,
            8,
            4,
        ),
    )
    pygame.draw.rect(
        screen,
        crack_light,
        (
            center_x - 3,
            top + 6,
            2,
            1,
        ),
    )
    pygame.draw.rect(
        screen,
        crack_light,
        (
            center_x + 2,
            top + 6,
            2,
            1,
        ),
    )

    pygame.draw.line(
        screen,
        crack,
        (center_x - 2, top + 9),
        (center_x, top + 12),
        2,
    )
    pygame.draw.line(
        screen,
        crack,
        (center_x, top + 12),
        (center_x - 2, top + 15),
    )
    pygame.draw.line(
        screen,
        crack_light,
        (center_x + 3, top + 9),
        (center_x + 5, top + 12),
    )
    pygame.draw.line(
        screen,
        crack,
        (center_x - 6, top + 8),
        (center_x - 8, top + 11),
    )

    club_hand = (
        center_x + 7,
        top + 11,
    )
    club_end = (
        center_x + 11,
        top + 5,
    )

    pygame.draw.line(
        screen,
        (67, 43, 29),
        club_hand,
        club_end,
        4,
    )
    pygame.draw.line(
        screen,
        (111, 70, 39),
        club_hand,
        club_end,
        2,
    )
    pygame.draw.polygon(
        screen,
        (47, 39, 35),
        (
            (club_end[0] - 3, club_end[1] - 4),
            (club_end[0] + 2, club_end[1] - 6),
            (club_end[0] + 5, club_end[1] - 2),
            (club_end[0] + 3, club_end[1] + 3),
            (club_end[0] - 2, club_end[1] + 2),
        ),
    )
    pygame.draw.line(
        screen,
        (80, 63, 50),
        (club_end[0] - 2, club_end[1] - 3),
        (club_end[0] + 2, club_end[1] - 4),
        2,
    )


def draw_brute_corpse(
    screen,
    center_x,
    center_y,
    color,
):
    floor_y = center_y + TILE_SIZE // 2 - 3
    stone = _darker(color, 24)
    stone_dark = _darker(color, 49)
    stone_light = _lighter(stone, 15)
    crack = (140, 57, 34)

    pygame.draw.ellipse(
        screen,
        (6, 6, 8),
        (
            center_x - 14,
            floor_y - 3,
            28,
            6,
        ),
    )
    pygame.draw.polygon(
        screen,
        stone_dark,
        (
            (center_x - 11, floor_y - 7),
            (center_x - 5, floor_y - 11),
            (center_x + 5, floor_y - 9),
            (center_x + 11, floor_y - 4),
            (center_x + 8, floor_y),
            (center_x - 9, floor_y),
        ),
    )
    pygame.draw.polygon(
        screen,
        stone,
        (
            (center_x - 9, floor_y - 7),
            (center_x - 4, floor_y - 9),
            (center_x + 4, floor_y - 8),
            (center_x + 8, floor_y - 4),
            (center_x + 6, floor_y - 1),
            (center_x - 7, floor_y - 1),
        ),
    )
    pygame.draw.line(
        screen,
        stone_light,
        (center_x - 6, floor_y - 7),
        (center_x, floor_y - 8),
        2,
    )
    pygame.draw.line(
        screen,
        crack,
        (center_x - 1, floor_y - 7),
        (center_x + 2, floor_y - 3),
        2,
    )
    pygame.draw.circle(
        screen,
        stone_dark,
        (center_x - 11, floor_y - 2),
        4,
    )
    pygame.draw.circle(
        screen,
        stone_dark,
        (center_x + 10, floor_y - 1),
        4,
    )

    pygame.draw.line(
        screen,
        (65, 42, 29),
        (center_x + 4, floor_y),
        (center_x + 12, floor_y - 4),
        4,
    )
    pygame.draw.polygon(
        screen,
        (45, 38, 35),
        (
            (center_x + 9, floor_y - 7),
            (center_x + 14, floor_y - 9),
            (center_x + 17, floor_y - 5),
            (center_x + 14, floor_y - 1),
            (center_x + 10, floor_y - 2),
        ),
    )


def draw_brute_death(
    screen,
    elapsed,
    color,
    center_x,
    center_y,
    is_aggro,
):
    if elapsed < 0:
        return

    if elapsed >= BRUTE_DEATH_DURATION_MS:
        draw_brute_corpse(
            screen,
            center_x,
            center_y,
            color,
        )
        return

    progress = elapsed / BRUTE_DEATH_DURATION_MS
    collapse = progress * progress
    body = pygame.Surface(
        (36, 34),
        pygame.SRCALPHA,
    )
    body_color = (
        (218, 207, 198)
        if elapsed < 85
        else tuple(
            max(10, round(channel * (1.0 - progress * 0.2)))
            for channel in color
        )
    )

    draw_brute(
        body,
        8,
        6,
        20,
        body_color,
        is_aggro,
    )

    collapsed_width = round(
        36 * (1.0 + collapse * 0.14)
    )
    collapsed_height = max(
        8,
        round(34 * (1.0 - collapse * 0.72)),
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
            center_y + 16 - collapsed_height,
        ),
    )


__all__ = [
    "brute_attack_offset",
    "brute_movement_offset",
    "draw_brute",
    "draw_brute_corpse",
    "draw_brute_death",
]
