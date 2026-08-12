import math

import pygame

from acts.act_two.presentation.enemy_effects import (
    ACT_TWO_CLASS_EFFECT_COLORS,
)
from presentation.layout import (
    MAP_HEIGHT,
    MAP_OFFSET_X,
    MAP_OFFSET_Y,
    MAP_WIDTH,
)
from settings import TILE_SIZE


def draw_player_attack_effect(
    screen,
    column,
    row,
    target,
    player_class,
    current_time,
    attack_started_at,
    critical=False,
):
    duration = 390 if critical else 310
    elapsed = current_time - attack_started_at
    if (
        target is None
        or player_class not in ACT_TWO_CLASS_EFFECT_COLORS
        or attack_started_at <= 0
        or not 0 <= elapsed < duration
    ):
        return

    progress = elapsed / duration
    visibility = max(0, 1 - progress)
    impact = math.sin(math.pi * min(1, progress * 1.45))
    direction_x = target[0] - column
    direction_y = target[1] - row
    length = max(1, math.hypot(direction_x, direction_y))
    direction_x /= length
    direction_y /= length
    perpendicular_x = -direction_y
    perpendicular_y = direction_x
    origin = (
        MAP_OFFSET_X + column * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2,
    )
    destination = (
        MAP_OFFSET_X + target[0] * TILE_SIZE + TILE_SIZE // 2,
        MAP_OFFSET_Y + target[1] * TILE_SIZE + TILE_SIZE // 2,
    )
    color = ACT_TWO_CLASS_EFFECT_COLORS[player_class]
    effect = pygame.Surface((MAP_WIDTH, MAP_HEIGHT), pygame.SRCALPHA)
    local_origin = (
        origin[0] - MAP_OFFSET_X,
        origin[1] - MAP_OFFSET_Y,
    )
    local_destination = (
        destination[0] - MAP_OFFSET_X,
        destination[1] - MAP_OFFSET_Y,
    )

    if player_class == "warrior":
        strike_delay = 60
        if elapsed < strike_delay:
            return
        strike_progress = min(
            1.0,
            (elapsed - strike_delay) / (duration - strike_delay),
        )
        visibility = max(0.0, 1 - strike_progress)
        impact = math.sin(
            math.pi * min(1.0, strike_progress * 1.55)
        )
        if abs(direction_y) > 0.5 and abs(direction_x) < 0.5:
            flash_start = (
                round(local_origin[0] + direction_x * 12),
                round(local_origin[1] + direction_y * 12),
            )
            flash_tip = (
                round(
                    local_destination[0]
                    + direction_x * (5 + impact * 5)
                ),
                round(
                    local_destination[1]
                    + direction_y * (5 + impact * 5)
                ),
            )
            flash_width = 4 + round(impact * 4)
            flash_base_left = (
                round(flash_start[0] - perpendicular_x * 2),
                round(flash_start[1] - perpendicular_y * 2),
            )
            flash_base_right = (
                round(flash_start[0] + perpendicular_x * 2),
                round(flash_start[1] + perpendicular_y * 2),
            )
            flash_tip_left = (
                round(
                    flash_tip[0]
                    - direction_x * 7
                    - perpendicular_x * flash_width
                ),
                round(
                    flash_tip[1]
                    - direction_y * 7
                    - perpendicular_y * flash_width
                ),
            )
            flash_tip_right = (
                round(
                    flash_tip[0]
                    - direction_x * 7
                    + perpendicular_x * flash_width
                ),
                round(
                    flash_tip[1]
                    - direction_y * 7
                    + perpendicular_y * flash_width
                ),
            )
            pygame.draw.polygon(
                effect,
                (205, 37, 48, round(210 * visibility)),
                (
                    flash_base_left,
                    flash_tip_left,
                    flash_tip,
                    flash_tip_right,
                    flash_base_right,
                ),
            )
            pygame.draw.line(
                effect,
                (255, 111, 88, round(250 * visibility)),
                flash_start,
                flash_tip,
                2,
            )
        else:
            sweep_center = (
                local_destination[0] - round(direction_x * 5),
                local_destination[1] - round(direction_y * 5),
            )
            sweep_length = 15 + round(impact * 5)
            arc_points = []
            for point_index in range(9):
                arc_position = -1.0 + point_index / 4
                across = arc_position * sweep_length
                forward_curve = (
                    (1 - arc_position * arc_position)
                    * (7 + round(impact * 5))
                    - 3
                )
                arc_points.append(
                    (
                        round(
                            sweep_center[0]
                            + perpendicular_x * across
                            + direction_x * forward_curve
                        ),
                        round(
                            sweep_center[1]
                            + perpendicular_y * across
                            + direction_y * forward_curve
                        ),
                    )
                )
            pygame.draw.lines(
                effect,
                (205, 37, 48, round(225 * visibility)),
                False,
                arc_points,
                7 if critical else 5,
            )
            pygame.draw.lines(
                effect,
                (255, 111, 88, round(250 * visibility)),
                False,
                arc_points,
                2,
            )
        for spark_index in range(6 if critical else 4):
            angle = spark_index * math.tau / (6 if critical else 4)
            distance = 6 + strike_progress * 16
            spark_end = (
                round(local_destination[0] + math.cos(angle) * distance),
                round(local_destination[1] + math.sin(angle) * distance),
            )
            pygame.draw.line(
                effect,
                (242, 72, 58, round(205 * visibility)),
                local_destination,
                spark_end,
                2,
            )
    elif player_class == "rogue":
        strike_delay = 35
        if elapsed < strike_delay:
            return
        strike_progress = min(
            1.0,
            (elapsed - strike_delay) / (duration - strike_delay),
        )
        visibility = max(0.0, 1 - strike_progress)
        downward_stab = direction_y > 0.5 and abs(direction_x) < 0.5
        upward_stab = direction_y < -0.5 and abs(direction_x) < 0.5
        travel = min(1, strike_progress * 2.2)
        trail_reach = min(travel, 0.75)
        trail_end = (
            round(
                local_origin[0]
                + (local_destination[0] - local_origin[0]) * trail_reach
            ),
            round(
                local_origin[1]
                + (local_destination[1] - local_origin[1]) * trail_reach
            ),
        )
        if travel > 0.4 and not downward_stab and not upward_stab:
            pygame.draw.line(
                effect,
                (*color, round(105 * visibility)),
                (
                    round(local_origin[0] + direction_x * 13),
                    round(local_origin[1] + direction_y * 13),
                ),
                trail_end,
                2,
            )
        slash_center = (
            local_destination[0] - direction_x * 5,
            local_destination[1] - direction_y * 5,
        )
        slash_span = 4 if downward_stab else 9
        slash_depth = 1 if downward_stab else 3
        if upward_stab:
            slash_start = (
                round(
                    local_origin[0]
                    + direction_x * 12
                    + perpendicular_x * 7
                ),
                round(
                    local_origin[1]
                    + direction_y * 12
                    + perpendicular_y * 7
                ),
            )
            full_slash_end = (
                round(
                    local_destination[0]
                    - direction_x * 6
                    + perpendicular_x * 4
                ),
                round(
                    local_destination[1]
                    - direction_y * 6
                    + perpendicular_y * 4
                ),
            )
            thrust_growth = min(1.0, strike_progress * 2.7)
            slash_end = (
                round(
                    slash_start[0]
                    + (full_slash_end[0] - slash_start[0])
                    * thrust_growth
                ),
                round(
                    slash_start[1]
                    + (full_slash_end[1] - slash_start[1])
                    * thrust_growth
                ),
            )
        else:
            slash_start = (
                round(
                    slash_center[0]
                    - perpendicular_x * slash_span
                    - direction_x * slash_depth
                ),
                round(
                    slash_center[1]
                    - perpendicular_y * slash_span
                    - direction_y * slash_depth
                ),
            )
            slash_end = (
                round(
                    slash_center[0]
                    + perpendicular_x * slash_span
                    + direction_x * slash_depth
                ),
                round(
                    slash_center[1]
                    + perpendicular_y * slash_span
                    + direction_y * slash_depth
                ),
            )
        pygame.draw.line(
            effect,
            (
                113,
                42,
                149,
                round((80 if downward_stab else 165) * visibility),
            ),
            slash_start,
            slash_end,
            (
                2
                if downward_stab
                else (3 if upward_stab else (5 if critical else 4))
            ),
        )
        pygame.draw.line(
            effect,
            (
                222,
                143,
                246,
                round((150 if downward_stab else 225) * visibility),
            ),
            slash_start,
            slash_end,
            1 if downward_stab or upward_stab else 2,
        )
        if upward_stab:
            pygame.draw.circle(
                effect,
                (235, 187, 255, round(190 * visibility)),
                slash_end,
                2 if critical else 1,
            )
    else:
        release_progress = max(0.0, (progress - 0.16) / 0.58)
        travel = min(1.0, release_progress)
        staff_origin = (
            local_origin[0] + direction_x * 10,
            local_origin[1]
            + direction_y * 10
            - (10 if abs(direction_x) > 0.5 else 0),
        )
        orb_center = (
            round(
                staff_origin[0]
                + (
                    local_destination[0]
                    - staff_origin[0]
                )
                * travel
            ),
            round(
                staff_origin[1]
                + (
                    local_destination[1]
                    - staff_origin[1]
                )
                * travel
            ),
        )
        if release_progress > 0:
            trail_start = (
                round(orb_center[0] - direction_x * (8 + travel * 8)),
                round(orb_center[1] - direction_y * (8 + travel * 8)),
            )
            pygame.draw.line(
                effect,
                (*color, round(135 * visibility)),
                trail_start,
                orb_center,
                5,
            )
            pygame.draw.circle(
                effect,
                (52, 118, 255, round(105 * visibility)),
                orb_center,
                9 if critical else 7,
            )
            pygame.draw.circle(
                effect,
                (76, 169, 255, round(235 * visibility)),
                orb_center,
                6 if critical else 5,
            )
            pygame.draw.circle(
                effect,
                (193, 238, 255, round(255 * visibility)),
                (
                    round(orb_center[0] - direction_x * 1 - perpendicular_x * 1),
                    round(orb_center[1] - direction_y * 1 - perpendicular_y * 1),
                ),
                2,
            )
        if travel >= 0.92:
            rune_radius = round(7 + progress * (12 if critical else 8))
            pygame.draw.circle(
                effect,
                (*color, round(190 * visibility)),
                local_destination,
                rune_radius,
                width=2,
            )
            pygame.draw.polygon(
                effect,
                (174, 226, 255, round(210 * visibility)),
                (
                    (local_destination[0], local_destination[1] - rune_radius),
                    (local_destination[0] + rune_radius, local_destination[1]),
                    (local_destination[0], local_destination[1] + rune_radius),
                    (local_destination[0] - rune_radius, local_destination[1]),
                ),
                width=1,
            )

    if critical:
        pygame.draw.circle(
            effect,
            (255, 221, 132, round(175 * visibility)),
            local_destination,
            round(8 + progress * 18),
            width=2,
        )
    screen.blit(effect, (MAP_OFFSET_X, MAP_OFFSET_Y))
