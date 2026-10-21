import pygame

from acts.act_one.presentation.enemies.motion import (
    attack_direction,
)
from settings import TILE_SIZE


ARCHER_ATTACK_DURATION_MS = 300
ARCHER_DEATH_DURATION_MS = 400


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


def archer_attack_pose(enemy, current_time):
    direction_x, _ = attack_direction(enemy)
    facing = -1 if direction_x < 0 else 1

    started_at = enemy.get(
        "attack_animation_started_at",
        0,
    )
    if started_at <= 0:
        return facing, 0.0, False

    elapsed = current_time - started_at
    if not 0 <= elapsed < ARCHER_ATTACK_DURATION_MS:
        return facing, 0.0, False

    if elapsed < 90:
        draw_strength = elapsed / 90
    elif elapsed < 145:
        draw_strength = 1.0
    else:
        release_progress = min(
            1.0,
            (elapsed - 145) / 45,
        )
        draw_strength = 1.0 - release_progress

    arrow_visible = elapsed < 155

    return facing, draw_strength, arrow_visible


def draw_archer(
    screen,
    x,
    y,
    size,
    color,
    is_aggro,
    facing=1,
    draw_strength=0.0,
    arrow_visible=False,
    opacity=255,
):
    actor = pygame.Surface(
        (30, 26),
        pygame.SRCALPHA,
    )

    skin = color
    skin_light = _lighter(color, 19)
    skin_shadow = _darker(color, 31)
    skin_deep = _darker(color, 53)
    cloth = (29, 31, 24)
    cloth_light = (48, 50, 34)
    leather = (77, 48, 29)
    leather_light = (119, 76, 39)
    bow_dark = (62, 38, 25)
    bow_light = (130, 79, 39)
    eye = (
        (238, 205, 53)
        if is_aggro
        else (139, 124, 51)
    )

    pygame.draw.line(
        actor,
        skin_deep,
        (11, 18),
        (10, 23),
        3,
    )
    pygame.draw.line(
        actor,
        skin_deep,
        (17, 18),
        (18, 23),
        3,
    )
    pygame.draw.line(
        actor,
        (34, 31, 25),
        (8, 24),
        (12, 24),
        2,
    )
    pygame.draw.line(
        actor,
        (34, 31, 25),
        (17, 24),
        (21, 24),
        2,
    )

    pygame.draw.line(
        actor,
        leather,
        (8, 9),
        (6, 20),
        3,
    )
    pygame.draw.line(
        actor,
        leather_light,
        (7, 8),
        (5, 14),
    )
    pygame.draw.line(
        actor,
        (127, 120, 90),
        (6, 8),
        (5, 3),
    )
    pygame.draw.line(
        actor,
        (127, 120, 90),
        (8, 8),
        (8, 3),
    )

    pygame.draw.polygon(
        actor,
        (17, 19, 16),
        (
            (9, 8),
            (16, 7),
            (20, 11),
            (20, 18),
            (17, 21),
            (9, 20),
            (6, 16),
            (6, 11),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth,
        (
            (10, 8),
            (16, 8),
            (19, 11),
            (18, 19),
            (14, 20),
            (9, 18),
            (7, 15),
            (8, 11),
        ),
    )
    pygame.draw.polygon(
        actor,
        cloth_light,
        (
            (10, 9),
            (14, 9),
            (16, 12),
            (15, 18),
            (10, 17),
            (8, 14),
        ),
    )
    pygame.draw.line(
        actor,
        leather,
        (8, 16),
        (18, 16),
        2,
    )

    pygame.draw.polygon(
        actor,
        skin_deep,
        (
            (8, 4),
            (10, 1),
            (17, 1),
            (21, 4),
            (22, 8),
            (19, 12),
            (11, 12),
            (7, 9),
        ),
    )
    pygame.draw.polygon(
        actor,
        skin,
        (
            (9, 4),
            (11, 2),
            (17, 2),
            (20, 4),
            (20, 7),
            (23, 8),
            (20, 11),
            (12, 11),
            (8, 8),
        ),
    )
    pygame.draw.polygon(
        actor,
        skin_shadow,
        (
            (8, 5),
            (4, 4),
            (6, 8),
            (9, 9),
        ),
    )
    pygame.draw.polygon(
        actor,
        skin_light,
        (
            (11, 3),
            (17, 3),
            (19, 5),
            (17, 6),
            (11, 6),
            (9, 5),
        ),
    )
    pygame.draw.rect(
        actor,
        (23, 27, 18),
        (10, 6, 10, 3),
    )
    pygame.draw.rect(
        actor,
        eye,
        (12, 6, 2, 2),
    )
    pygame.draw.rect(
        actor,
        eye,
        (17, 6, 2, 2),
    )
    pygame.draw.rect(
        actor,
        skin_shadow,
        (20, 8, 3, 2),
    )
    pygame.draw.rect(
        actor,
        (178, 160, 112),
        (20, 10, 1, 2),
    )

    hand_x = round(
        21 - draw_strength
    )
    hand_y = 14

    pygame.draw.line(
        actor,
        skin_shadow,
        (17, 11),
        (hand_x, hand_y),
        3,
    )
    pygame.draw.circle(
        actor,
        skin,
        (hand_x, hand_y),
        2,
    )

    bow_points = (
        (22, 3),
        (26, 6),
        (28, 12),
        (27, 18),
        (23, 23),
    )
    pygame.draw.lines(
        actor,
        bow_dark,
        False,
        bow_points,
        4,
    )
    pygame.draw.lines(
        actor,
        bow_light,
        False,
        bow_points,
        2,
    )

    string_point = (
        round(22 - draw_strength * 2),
        13,
    )
    pygame.draw.line(
        actor,
        (117, 104, 78),
        bow_points[0],
        string_point,
    )
    pygame.draw.line(
        actor,
        (117, 104, 78),
        string_point,
        bow_points[-1],
    )

    if arrow_visible:
        pygame.draw.line(
            actor,
            (153, 139, 101),
            string_point,
            (29, 13),
            2,
        )
        pygame.draw.polygon(
            actor,
            (113, 116, 105),
            (
                (29, 13),
                (26, 11),
                (26, 15),
            ),
        )

    if facing < 0:
        actor = pygame.transform.flip(
            actor,
            True,
            False,
        )

    actor.set_alpha(
        max(
            0,
            min(255, opacity),
        )
    )

    center_x = x + size // 2
    floor_y = y + size

    screen.blit(
        actor,
        (
            center_x - actor.get_width() // 2,
            floor_y - 25,
        ),
    )


def draw_archer_corpse(
    screen,
    center_x,
    center_y,
    color,
):
    floor_y = center_y + TILE_SIZE // 2 - 3
    skin = _darker(color, 18)
    skin_shadow = _darker(color, 43)

    pygame.draw.ellipse(
        screen,
        (6, 7, 7),
        (
            center_x - 14,
            floor_y - 3,
            28,
            6,
        ),
    )
    pygame.draw.polygon(
        screen,
        (27, 29, 23),
        (
            (center_x - 8, floor_y - 7),
            (center_x + 4, floor_y - 8),
            (center_x + 9, floor_y - 4),
            (center_x + 6, floor_y),
            (center_x - 9, floor_y),
        ),
    )
    pygame.draw.polygon(
        screen,
        skin,
        (
            (center_x - 11, floor_y - 8),
            (center_x - 7, floor_y - 11),
            (center_x - 2, floor_y - 9),
            (center_x, floor_y - 5),
            (center_x - 5, floor_y - 3),
            (center_x - 11, floor_y - 5),
        ),
    )
    pygame.draw.line(
        screen,
        skin_shadow,
        (center_x - 9, floor_y - 5),
        (center_x - 4, floor_y - 4),
        2,
    )
    pygame.draw.line(
        screen,
        (67, 40, 25),
        (center_x + 3, floor_y),
        (center_x + 12, floor_y - 8),
        3,
    )
    pygame.draw.lines(
        screen,
        (116, 69, 35),
        False,
        (
            (center_x + 7, floor_y - 10),
            (center_x + 13, floor_y - 6),
            (center_x + 14, floor_y),
        ),
        2,
    )
    pygame.draw.line(
        screen,
        (105, 93, 69),
        (center_x + 7, floor_y - 10),
        (center_x + 14, floor_y),
    )


def draw_archer_death(
    screen,
    elapsed,
    color,
    center_x,
    center_y,
    is_aggro,
):
    if elapsed < 0:
        return

    if elapsed >= ARCHER_DEATH_DURATION_MS:
        draw_archer_corpse(
            screen,
            center_x,
            center_y,
            color,
        )
        return

    progress = elapsed / ARCHER_DEATH_DURATION_MS
    collapse = progress * progress

    body = pygame.Surface(
        (36, 30),
        pygame.SRCALPHA,
    )
    body_color = (
        (218, 211, 192)
        if elapsed < 70
        else tuple(
            max(
                10,
                round(
                    channel
                    * (1.0 - progress * 0.24)
                ),
            )
            for channel in color
        )
    )

    draw_archer(
        body,
        8,
        5,
        20,
        body_color,
        is_aggro,
    )

    collapsed_width = round(
        36 * (1.0 + collapse * 0.08)
    )
    collapsed_height = max(
        6,
        round(
            30 * (1.0 - collapse * 0.76)
        ),
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
            center_y + 15 - collapsed_height,
        ),
    )


__all__ = [
    "archer_attack_pose",
    "draw_archer",
    "draw_archer_corpse",
    "draw_archer_death",
]
