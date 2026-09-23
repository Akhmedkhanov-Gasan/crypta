import math

import pygame

from acts.act_three.abilities.berserker import (
    get_berserker_crushing_leap_direction,
)

CRUSHING_LEAP_FRAME_COUNT = 8


def crushing_leap_direction(origin, destination):
    return get_berserker_crushing_leap_direction(
        origin,
        destination,
    )


def crushing_leap_frame(elapsed, duration):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )

    return min(
        CRUSHING_LEAP_FRAME_COUNT - 1,
        int(progress * CRUSHING_LEAP_FRAME_COUNT),
    )


def crushing_leap_position(
    start_position,
    end_position,
    elapsed,
    duration,
    tile_size,
):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )
    anticipation_end = 0.16

    if progress < anticipation_end:
        anticipation_progress = (
            progress / anticipation_end
        )
        crouch_offset = (
            math.sin(
                anticipation_progress * math.pi
            )
            * tile_size
            * 0.055
        )

        return (
            start_position[0],
            round(
                start_position[1]
                + crouch_offset
            ),
        )

    flight_progress = (
        progress - anticipation_end
    ) / (1 - anticipation_end)
    eased_progress = (
        flight_progress
        * flight_progress
        * (3 - 2 * flight_progress)
    )
    jump_height = (
        math.sin(math.pi * flight_progress)
        * tile_size
        * 0.62
    )

    ground_position = (
        round(
            start_position[0]
            + (
                end_position[0]
                - start_position[0]
            )
            * eased_progress
        ),
        round(
            start_position[1]
            + (
                end_position[1]
                - start_position[1]
            )
            * eased_progress
        ),
    )

    return (
        ground_position[0],
        round(
            ground_position[1]
            - jump_height
        ),
    )


def crushing_leap_camera_offset(
    elapsed,
    travel_duration,
    impact_duration,
):
    impact_elapsed = elapsed - travel_duration
    shake_duration = min(260, impact_duration)

    if not 0 <= impact_elapsed < shake_duration:
        return (0, 0)

    progress = impact_elapsed / shake_duration
    strength = 7 * (1 - progress) ** 2

    return (
        round(math.sin(impact_elapsed * 0.21) * strength),
        round(math.cos(impact_elapsed * 0.29) * strength * 0.65),
    )


def draw_crushing_leap_targeting(
    surface,
    origin,
    target,
    impact_cells,
    camera_x,
    camera_y,
    current_time,
    tile_size,
):
    if target is None:
        return

    overlay = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    half_tile = tile_size // 2
    pulse = (
        math.sin(current_time * 0.009) + 1
    ) / 2

    origin_center = (
        origin[0] * tile_size
        - camera_x
        + half_tile,
        origin[1] * tile_size
        - camera_y
        + half_tile,
    )
    target_center = (
        target[0] * tile_size
        - camera_x
        + half_tile,
        target[1] * tile_size
        - camera_y
        + half_tile,
    )

    difference_x = (
        target_center[0] - origin_center[0]
    )
    difference_y = (
        target_center[1] - origin_center[1]
    )
    distance = max(
        1.0,
        math.hypot(
            difference_x,
            difference_y,
        ),
    )
    perpendicular_x = -difference_y / distance
    perpendicular_y = difference_x / distance
    upper_path = []
    lower_path = []

    for step in range(33):
        progress = step / 32
        taper = math.sin(math.pi * progress)
        wave = math.sin(
            progress * math.tau * 2
            - current_time * 0.009
        )
        separation = (
            3
            + taper * 5
            + wave * 1.5
        )
        center_x = (
            origin_center[0]
            + difference_x * progress
        )
        center_y = (
            origin_center[1]
            + difference_y * progress
        )

        upper_path.append(
            (
                round(
                    center_x
                    + perpendicular_x * separation
                ),
                round(
                    center_y
                    + perpendicular_y * separation
                ),
            )
        )
        lower_path.append(
            (
                round(
                    center_x
                    - perpendicular_x * separation
                ),
                round(
                    center_y
                    - perpendicular_y * separation
                ),
            )
        )

    pygame.draw.lines(
        overlay,
        (25, 1, 3, 145),
        False,
        upper_path,
        width=8,
    )
    pygame.draw.lines(
        overlay,
        (25, 1, 3, 145),
        False,
        lower_path,
        width=8,
    )
    pygame.draw.lines(
        overlay,
        (119, 10, 13, 205),
        False,
        upper_path,
        width=3,
    )
    pygame.draw.lines(
        overlay,
        (155, 16, 17, 195),
        False,
        lower_path,
        width=2,
    )

    stain_points = []
    stain_point_count = 28

    for point_index in range(stain_point_count):
        angle = (
            point_index
            * math.tau
            / stain_point_count
        )
        alternating_offset = (
            9
            if point_index % 2 == 0
            else -6
        )
        noise_offset = math.sin(
            point_index * 4.37
            + current_time * 0.003
        ) * 4
        radius = (
            tile_size * 1.18
            + alternating_offset
            + noise_offset
            + pulse * 3
        )

        stain_points.append(
            (
                round(
                    target_center[0]
                    + math.cos(angle) * radius
                ),
                round(
                    target_center[1]
                    + math.sin(angle)
                    * radius
                    * 0.72
                ),
            )
        )

    pygame.draw.polygon(
        overlay,
        (
            18,
            1,
            3,
            round(112 + pulse * 18),
        ),
        stain_points,
    )
    pygame.draw.lines(
        overlay,
        (
            91,
            7,
            10,
            round(180 + pulse * 35),
        ),
        True,
        stain_points,
        width=3,
    )

    inner_stain_points = []

    for point_index in range(20):
        angle = (
            point_index
            * math.tau
            / 20
            + 0.13
        )
        radius = (
            tile_size * 0.76
            + math.sin(
                point_index * 3.11
                - current_time * 0.004
            ) * 6
        )
        inner_stain_points.append(
            (
                round(
                    target_center[0]
                    + math.cos(angle) * radius
                ),
                round(
                    target_center[1]
                    + math.sin(angle)
                    * radius
                    * 0.68
                ),
            )
        )

    pygame.draw.polygon(
        overlay,
        (
            42,
            2,
            5,
            round(90 + pulse * 20),
        ),
        inner_stain_points,
    )

    for cell_index, (column, row) in enumerate(
        impact_cells
    ):
        cell_center = (
            column * tile_size
            - camera_x
            + half_tile,
            row * tile_size
            - camera_y
            + half_tile,
        )
        slash_angle = (
            -0.78
            + (cell_index % 3 - 1) * 0.18
        )
        slash_length = round(
            tile_size
            * (0.21 + cell_index % 2 * 0.05)
        )
        offset_x = round(
            math.cos(slash_angle)
            * slash_length
        )
        offset_y = round(
            math.sin(slash_angle)
            * slash_length
        )

        for slash_index in (-1, 1):
            perpendicular_offset = slash_index * 4
            start = (
                cell_center[0]
                - offset_x
                + perpendicular_offset,
                cell_center[1] - offset_y,
            )
            end = (
                cell_center[0]
                + offset_x
                + perpendicular_offset,
                cell_center[1] + offset_y,
            )
            pygame.draw.line(
                overlay,
                (
                    122,
                    11,
                    13,
                    round(105 + pulse * 35),
                ),
                start,
                end,
                width=2,
            )

    for crack_index in range(15):
        angle = (
            crack_index * math.tau / 15
            + math.sin(crack_index * 2.91) * 0.16
        )
        start_distance = tile_size * 0.13
        middle_distance = (
            tile_size
            * (0.39 + crack_index % 3 * 0.08)
        )
        end_distance = (
            tile_size
            * (0.72 + crack_index % 4 * 0.09)
        )
        bend = (
            0.08
            if crack_index % 2 == 0
            else -0.1
        )
        start = (
            round(
                target_center[0]
                + math.cos(angle)
                * start_distance
            ),
            round(
                target_center[1]
                + math.sin(angle)
                * start_distance
                * 0.72
            ),
        )
        middle = (
            round(
                target_center[0]
                + math.cos(angle + bend)
                * middle_distance
            ),
            round(
                target_center[1]
                + math.sin(angle + bend)
                * middle_distance
                * 0.72
            ),
        )
        end = (
            round(
                target_center[0]
                + math.cos(angle - bend)
                * end_distance
            ),
            round(
                target_center[1]
                + math.sin(angle - bend)
                * end_distance
                * 0.72
            ),
        )

        pygame.draw.lines(
            overlay,
            (
                144,
                13,
                14,
                round(125 + pulse * 45),
            ),
            False,
            (
                start,
                middle,
                end,
            ),
            width=2,
        )

    core_size = round(
        tile_size * (0.22 + pulse * 0.025)
    )
    core_points = (
        (
            target_center[0],
            target_center[1] - core_size,
        ),
        (
            target_center[0] + core_size,
            target_center[1],
        ),
        (
            target_center[0],
            target_center[1] + core_size,
        ),
        (
            target_center[0] - core_size,
            target_center[1],
        ),
    )

    pygame.draw.polygon(
        overlay,
        (10, 0, 2, 230),
        core_points,
    )
    pygame.draw.lines(
        overlay,
        (
            183,
            20,
            19,
            round(185 + pulse * 45),
        ),
        True,
        core_points,
        width=3,
    )

    claw_length = round(tile_size * 0.36)

    for claw_index in (-1, 0, 1):
        horizontal_offset = claw_index * 7
        pygame.draw.line(
            overlay,
            (
                204,
                28,
                22,
                round(155 + pulse * 55),
            ),
            (
                target_center[0]
                - claw_length // 2
                + horizontal_offset,
                target_center[1]
                - claw_length // 2,
            ),
            (
                target_center[0]
                + claw_length // 2
                + horizontal_offset,
                target_center[1]
                + claw_length // 2,
            ),
            width=2,
        )

    for mote_index in range(7):
        progress = (
            current_time / 900
            + mote_index / 7
        ) % 1
        source_path = (
            upper_path
            if mote_index % 2 == 0
            else lower_path
        )
        point_index = min(
            len(source_path) - 1,
            round(
                progress
                * (len(source_path) - 1)
            ),
        )
        mote_alpha = round(
            55
            + math.sin(math.pi * progress) * 125
        )

        pygame.draw.circle(
            overlay,
            (
                158,
                17,
                17,
                mote_alpha,
            ),
            source_path[point_index],
            2,
        )

    surface.blit(overlay, (0, 0))


def draw_crushing_leap_travel_effect(
    surface,
    sprite,
    start_position,
    end_position,
    elapsed,
    duration,
    tile_size,
):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )
    eased_progress = (
        progress
        * progress
        * (3 - 2 * progress)
    )
    ground_position = (
        round(
            start_position[0]
            + (
                end_position[0]
                - start_position[0]
            )
            * eased_progress
        ),
        round(
            start_position[1]
            + (
                end_position[1]
                - start_position[1]
            )
            * eased_progress
        ),
    )
    height_ratio = math.sin(math.pi * progress)
    shadow_width = round(
        tile_size * (0.48 - height_ratio * 0.16)
    )
    shadow_height = max(5, round(shadow_width * 0.28))
    shadow_surface = pygame.Surface(
        (tile_size, tile_size),
        pygame.SRCALPHA,
    )
    pygame.draw.ellipse(
        shadow_surface,
        (
            25,
            8,
            5,
            round(145 - height_ratio * 70),
        ),
        (
            tile_size // 2 - shadow_width // 2,
            tile_size - shadow_height - 5,
            shadow_width,
            shadow_height,
        ),
    )
    surface.blit(shadow_surface, ground_position)

    for echo_index in range(2, 0, -1):
        echo_elapsed = max(
            0,
            elapsed - echo_index * 48,
        )
        echo_position = crushing_leap_position(
            start_position,
            end_position,
            echo_elapsed,
            duration,
            tile_size,
        )
        echo = sprite.copy()
        echo.fill(
            (80, 24, 8, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        echo.set_alpha(14 + echo_index * 12)
        surface.blit(echo, echo_position)


def draw_crushing_leap_impact_effect(
    surface,
    target,
    camera_x,
    camera_y,
    impact_elapsed,
    impact_duration,
    tile_size,
):
    if not 0 <= impact_elapsed < impact_duration:
        return

    progress = impact_elapsed / impact_duration
    visibility = (1 - progress) ** 2
    effect_size = tile_size * 3
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    center = (effect_size // 2, effect_size // 2)
    target_position = (
        target[0] * tile_size - camera_x,
        target[1] * tile_size - camera_y,
    )

    outer_radius = round(
        tile_size * (0.25 + progress * 1.15)
    )
    inner_radius = round(
        tile_size * (0.12 + progress * 0.72)
    )

    pygame.draw.circle(
        effect_surface,
        (
            255,
            91,
            31,
            round(210 * visibility),
        ),
        center,
        outer_radius,
        width=max(1, round(4 * visibility)),
    )
    pygame.draw.circle(
        effect_surface,
        (
            255,
            185,
            78,
            round(175 * visibility),
        ),
        center,
        inner_radius,
        width=2,
    )

    for crack_index in range(12):
        angle = (
            crack_index * math.tau / 12
            + math.sin(crack_index * 3.17) * 0.18
        )
        start_distance = tile_size * 0.16
        end_distance = (
            tile_size
            * (0.38 + (crack_index % 4) * 0.09)
            * min(1, progress * 4)
        )
        start = (
            round(
                center[0]
                + math.cos(angle) * start_distance
            ),
            round(
                center[1]
                + math.sin(angle) * start_distance
            ),
        )
        end = (
            round(
                center[0]
                + math.cos(angle) * end_distance
            ),
            round(
                center[1]
                + math.sin(angle) * end_distance
            ),
        )
        pygame.draw.line(
            effect_surface,
            (
                112,
                35,
                19,
                round(220 * visibility),
            ),
            start,
            end,
            width=2,
        )

    for dust_index in range(18):
        phase = (
            progress + dust_index * 0.071
        ) % 1
        angle = dust_index * 2.399
        distance = (
            tile_size
            * (0.18 + phase * 0.88)
        )
        dust_position = (
            round(
                center[0]
                + math.cos(angle) * distance
            ),
            round(
                center[1]
                + math.sin(angle) * distance * 0.48
                - math.sin(math.pi * phase) * 15
            ),
        )
        dust_visibility = (
            math.sin(math.pi * phase)
            * visibility
        )
        pygame.draw.circle(
            effect_surface,
            (
                191,
                91,
                43,
                round(190 * dust_visibility),
            ),
            dust_position,
            2 if dust_index % 4 == 0 else 1,
        )

    surface.blit(
        effect_surface,
        (
            target_position[0] - tile_size,
            target_position[1] - tile_size,
        ),
    )
