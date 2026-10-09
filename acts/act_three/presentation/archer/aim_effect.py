import math

import pygame

from acts.act_three.combat.archer_aim import (
    archer_aim_targets,
)
from acts.act_three.presentation.view import _view_position
from acts.act_three.presentation.archer.projectile import (
    PIERCING_WINDUP_MS,
)


def _polar(center, angle, distance):
    return (
        round(center[0] + math.cos(angle) * distance),
        round(center[1] + math.sin(angle) * distance),
    )


def _draw_target_reticle(surface, center, tile_size, current_time):
    size = round(tile_size * 1.5)
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    middle = (size // 2, size // 2)
    pulse = math.sin(current_time * 0.009) * 1.2
    radius = tile_size * 0.34 + pulse
    ring = pygame.Rect(0, 0, round(radius * 2), round(radius * 2))
    ring.center = middle

    for index in range(4):
        angle = index * math.pi / 2
        start = angle + 0.23
        end = angle + 1.12
        pygame.draw.arc(
            layer,
            (5, 20, 13, 220),
            ring,
            start,
            end,
            5,
        )
        pygame.draw.arc(
            layer,
            (49, 142, 78, 230),
            ring,
            start,
            end,
            2,
        )

        claw = [
            _polar(middle, angle - 0.18, radius + 4),
            _polar(middle, angle - 0.11, radius - 2),
            _polar(middle, angle, radius - 10),
            _polar(middle, angle + 0.11, radius - 2),
            _polar(middle, angle + 0.18, radius + 4),
        ]
        pygame.draw.polygon(layer, (5, 18, 12, 240), claw)
        pygame.draw.lines(
            layer,
            (83, 190, 105, 245),
            False,
            claw[1:4],
            2,
        )

    pygame.draw.circle(layer, (7, 24, 15, 220), middle, 4)
    pygame.draw.circle(layer, (110, 211, 125, 230), middle, 2)

    surface.blit(
        layer,
        (
            round(center[0] - middle[0]),
            round(center[1] - middle[1]),
        ),
    )


def _draw_aim_entry(surface, center, tile_size, elapsed):
    if not 0 <= elapsed < 220:
        return

    size = round(tile_size * 1.5)
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    middle = (size // 2, size // 2)
    progress = elapsed / 220
    radius = round(tile_size * (0.27 + progress * 0.22))
    alpha = round(160 * (1 - progress))
    ring = pygame.Rect(0, 0, radius * 2, radius * 2)
    ring.center = middle

    for index in range(3):
        start = index * math.tau / 3 + 0.15
        pygame.draw.arc(
            layer,
            (49, 150, 83, alpha),
            ring,
            start,
            start + 0.85,
            2,
        )

    surface.blit(
        layer,
        (
            round(center[0] - middle[0]),
            round(center[1] - middle[1]),
        ),
    )


def draw_piercing_charge(
    surface,
    feet,
    tile_size,
    current_time,
    compression=0.0,
):
    size = round(tile_size * 1.9)
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    middle = (size // 2, size // 2)
    pulse = math.sin(current_time * 0.014) * 1.2
    radius = tile_size * (
        0.47 - 0.22 * compression
    ) + pulse

    for index in range(7):
        angle = index * math.tau / 7
        bend = math.sin(index * 3.8) * 3
        points = []

        for fraction, offset in (
            (1.15, 0.0),
            (0.84, 0.09),
            (0.61, -0.07),
            (0.30, 0.03),
        ):
            distance = radius * fraction
            direction = angle + offset
            points.append(
                (
                    round(
                        middle[0]
                        + math.cos(direction) * distance
                    ),
                    round(
                        middle[1]
                        + math.sin(direction)
                        * distance * 0.48
                        + bend * fraction
                    ),
                )
            )

        pygame.draw.lines(
            layer,
            (5, 23, 13, 220),
            False,
            points,
            6,
        )
        pygame.draw.lines(
            layer,
            (45, 128, 67, 205),
            False,
            points,
            2,
        )

    for index in range(4):
        angle = index * math.pi / 2
        ring = pygame.Rect(
            0,
            0,
            round(radius * 1.4),
            round(radius * 0.67),
        )
        ring.center = middle
        pygame.draw.arc(
            layer,
            (74, 174, 91, 170),
            ring,
            angle + 0.19,
            angle + 0.96,
            2,
        )

    pygame.draw.ellipse(
        layer,
        (6, 27, 15, 155),
        pygame.Rect(
            middle[0] - round(radius * 0.28),
            middle[1] - round(radius * 0.10),
            round(radius * 0.56),
            round(radius * 0.20),
        ),
    )
    surface.blit(
        layer,
        (
            round(feet[0] - middle[0]),
            round(feet[1] - middle[1]),
        ),
    )


def draw_archer_aim_effect(
    surface,
    game_state,
    camera_x,
    camera_y,
    current_time,
    tile_size,
):
    player = game_state.player
    piercing_elapsed = (
        current_time
        - player.archer_piercing_effect_started_at
    )
    piercing_windup = (
        player.archer_piercing_effect_target is not None
        and 0 <= piercing_elapsed < PIERCING_WINDUP_MS
    )
    if not (
        player.archer_basic_aiming
        or player.archer_piercing_aiming
        or piercing_windup
    ):
        return

    floor = game_state.floor
    player_position = _view_position(
        floor.player_column,
        floor.player_row,
        camera_x,
        camera_y,
    )
    player_center = (
        player_position[0] + tile_size // 2,
        player_position[1] + tile_size // 2,
    )
    feet = (
        player_position[0] + tile_size // 2,
        player_position[1] + round(tile_size * 0.79),
    )

    if player.archer_piercing_aiming or piercing_windup:
        draw_piercing_charge(
            surface,
            feet,
            tile_size,
            current_time,
            compression=(
                piercing_elapsed / PIERCING_WINDUP_MS
                if piercing_windup
                else 0.0
            ),
        )

    if piercing_windup:
        return

    if player.archer_basic_aiming:
        _draw_aim_entry(
            surface,
            player_center,
            tile_size,
            current_time - player.archer_basic_aim_started_at,
        )


    target = player.archer_basic_aim_target
    if target not in archer_aim_targets(game_state):
        return

    target_position = _view_position(
        target[0],
        target[1],
        camera_x,
        camera_y,
    )
    target_center = (
        target_position[0] + tile_size // 2,
        target_position[1] + tile_size // 2,
    )
    _draw_target_reticle(
        surface,
        target_center,
        tile_size,
        current_time,
    )
