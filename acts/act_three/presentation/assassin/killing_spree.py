import math

import pygame

from acts.act_three.presentation.player_motion import (
    assassin_shadow_step_direction,
)
from acts.act_three.presentation.view import (
    _view_position,
)
from acts.act_three.settings import (
    ASSASSIN_ULTIMATE_CAMERA_TRAVEL_RATIO,
    ASSASSIN_ULTIMATE_FINAL_IMPACT_MS,
    ASSASSIN_ULTIMATE_OUTRO_MS,
    ASSASSIN_ULTIMATE_PRELUDE_MS,
    ASSASSIN_ULTIMATE_STEP_MS,
)
from acts.act_three.presentation.status_effects import (
    _draw_assassin_invisibility_effect,
)
from presentation.layout import ACT_THREE_TILE_SIZE


def _selected_enemies(
    floor,
    target_names,
):
    enemies_by_name = {
        enemy.name: enemy
        for enemy in floor.enemies
    }

    return [
        enemies_by_name[target_name]
        for target_name in target_names
        if target_name in enemies_by_name
    ]


def _smooth_progress(progress):
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3 - 2 * progress)


def _ultimate_elapsed(
    player,
    current_time,
):
    return max(
        0,
        current_time
        - player.ultimate_animation_started_at,
    )


def _strike_elapsed(
    player,
    current_time,
):
    return (
        _ultimate_elapsed(player, current_time)
        - ASSASSIN_ULTIMATE_PRELUDE_MS
    )


def _strike_duration(
    target_count,
):
    return target_count * ASSASSIN_ULTIMATE_STEP_MS


def _outro_started_at(
    target_count,
):
    return (
        ASSASSIN_ULTIMATE_PRELUDE_MS
        + _strike_duration(target_count)
    )


def killing_spree_camera_position(
    player,
    floor,
    current_time,
):
    if (
        not player.ultimate_animation_active
        or player.ultimate_origin is None
    ):
        return None

    targets = _selected_enemies(
        floor,
        player.ultimate_targets,
    )
    if not targets:
        return None

    elapsed = _ultimate_elapsed(
        player,
        current_time,
    )
    origin_column, origin_row = player.ultimate_origin

    if elapsed < ASSASSIN_ULTIMATE_PRELUDE_MS:
        focus_column = origin_column
        focus_row = origin_row
    elif elapsed < _outro_started_at(len(targets)):
        strikes_elapsed = (
            elapsed - ASSASSIN_ULTIMATE_PRELUDE_MS
        )
        target_index = min(
            len(targets) - 1,
            strikes_elapsed
            // ASSASSIN_ULTIMATE_STEP_MS,
        )
        step_elapsed = (
            strikes_elapsed
            % ASSASSIN_ULTIMATE_STEP_MS
        )
        destination = targets[target_index]

        if target_index == 0:
            start_column = origin_column
            start_row = origin_row
        else:
            previous_target = targets[target_index - 1]
            start_column = previous_target.column
            start_row = previous_target.row

        travel_duration = (
            ASSASSIN_ULTIMATE_STEP_MS
            * ASSASSIN_ULTIMATE_CAMERA_TRAVEL_RATIO
        )
        travel_progress = _smooth_progress(
            step_elapsed / travel_duration
        )
        focus_column = (
            start_column
            + (
                destination.column
                - start_column
            )
            * travel_progress
        )
        focus_row = (
            start_row
            + (
                destination.row
                - start_row
            )
            * travel_progress
        )
    else:
        last_target = targets[-1]
        outro_elapsed = (
            elapsed - _outro_started_at(len(targets))
        )
        return_progress = _smooth_progress(
            outro_elapsed
            / (ASSASSIN_ULTIMATE_OUTRO_MS * 0.72)
        )
        focus_column = (
            last_target.column
            + (
                origin_column
                - last_target.column
            )
            * return_progress
        )
        focus_row = (
            last_target.row
            + (
                origin_row
                - last_target.row
            )
            * return_progress
        )

    return (
        round(focus_column * ACT_THREE_TILE_SIZE),
        round(focus_row * ACT_THREE_TILE_SIZE),
    )


def killing_spree_player_sprite(
    player,
    floor,
    assets,
    current_time,
):
    if (
        not player.ultimate_animation_active
        or player.ultimate_origin is None
    ):
        return None

    targets = _selected_enemies(
        floor,
        player.ultimate_targets,
    )
    if not targets:
        return None

    elapsed = _ultimate_elapsed(
        player,
        current_time,
    )
    origin = player.ultimate_origin
    first_target = (
        targets[0].column,
        targets[0].row,
    )
    outro_start = _outro_started_at(
        len(targets)
    )

    if elapsed < ASSASSIN_ULTIMATE_PRELUDE_MS:
        progress = (
            elapsed
            / ASSASSIN_ULTIMATE_PRELUDE_MS
        )
        frame_index = min(
            3,
            int(progress * 4),
        )
        direction = assassin_shadow_step_direction(
            origin,
            first_target,
        )
        return assets[
            (
                "player_assassin_shadow_step_"
                f"{direction}_{frame_index}"
            )
        ]

    if elapsed >= outro_start:
        last_target = (
            targets[-1].column,
            targets[-1].row,
        )
        progress = min(
            1.0,
            (
                elapsed - outro_start
            )
            / ASSASSIN_ULTIMATE_OUTRO_MS,
        )
        frame_index = 4 + min(
            3,
            int(progress * 4),
        )
        direction = assassin_shadow_step_direction(
            last_target,
            origin,
        )
        return assets[
            (
                "player_assassin_shadow_step_"
                f"{direction}_{frame_index}"
            )
        ]

    hidden_sprite = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE,
            ACT_THREE_TILE_SIZE,
        ),
        pygame.SRCALPHA,
    )
    return hidden_sprite


def _rotate_offset(
    offset,
    angle,
):
    cosine = math.cos(angle)
    sine = math.sin(angle)

    return (
        offset[0] * cosine
        - offset[1] * sine,
        offset[0] * sine
        + offset[1] * cosine,
    )


def _curve_points(
    center,
    start,
    control,
    end,
    angle,
    progress,
):
    point_count = 28
    visible_count = max(
        2,
        min(
            point_count,
            round(point_count * progress),
        ),
    )
    points = []

    for point_index in range(visible_count):
        curve_progress = (
            point_index
            / (point_count - 1)
        )
        inverse_progress = 1 - curve_progress
        offset = (
            inverse_progress
            * inverse_progress
            * start[0]
            + 2
            * inverse_progress
            * curve_progress
            * control[0]
            + curve_progress
            * curve_progress
            * end[0],
            inverse_progress
            * inverse_progress
            * start[1]
            + 2
            * inverse_progress
            * curve_progress
            * control[1]
            + curve_progress
            * curve_progress
            * end[1],
        )
        rotated_offset = _rotate_offset(
            offset,
            angle,
        )
        points.append(
            (
                round(
                    center[0]
                    + rotated_offset[0]
                ),
                round(
                    center[1]
                    + rotated_offset[1]
                ),
            )
        )

    return points


def _draw_crimson_slashes(
    surface,
    position,
    progress,
    seed,
):
    progress = max(
        0.0,
        min(1.0, progress),
    )
    slash_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    center = (
        position[0]
        + ACT_THREE_TILE_SIZE // 2,
        position[1]
        + ACT_THREE_TILE_SIZE // 2,
    )
    draw_progress = min(
        1.0,
        progress * 1.9,
    )
    visibility = (
        1.0
        if progress < 0.48
        else max(
            0.0,
            1.0
            - (
                progress - 0.48
            ) / 0.52,
        )
    )
    alpha = round(
        255 * visibility
    )
    angle = (
        -0.72
        + seed % 4 * 0.46
    )

    bloom_width = round(
        34 + progress * 28
    )
    bloom_height = round(
        19 + progress * 17
    )
    bloom = pygame.Rect(
        0,
        0,
        bloom_width,
        bloom_height,
    )
    bloom.center = center

    pygame.draw.ellipse(
        slash_surface,
        (95, 4, 16, alpha // 5),
        bloom.inflate(22, 14),
    )
    pygame.draw.ellipse(
        slash_surface,
        (188, 18, 32, alpha // 4),
        bloom,
    )

    curves = (
        (
            (-36, 17),
            (-3, -31),
            (37, -13),
            angle,
        ),
        (
            (-31, -17),
            (3, 27),
            (34, 15),
            angle + 0.18,
        ),
    )

    for (
        start,
        control,
        end,
        curve_angle,
    ) in curves:
        points = _curve_points(
            center,
            start,
            control,
            end,
            curve_angle,
            draw_progress,
        )

        pygame.draw.lines(
            slash_surface,
            (35, 0, 8, alpha // 2),
            False,
            points,
            width=9,
        )
        pygame.draw.lines(
            slash_surface,
            (126, 6, 22, alpha),
            False,
            points,
            width=5,
        )
        pygame.draw.lines(
            slash_surface,
            (247, 48, 62, alpha),
            False,
            points,
            width=2,
        )
        pygame.draw.lines(
            slash_surface,
            (255, 176, 162, alpha),
            False,
            points,
            width=1,
        )

    if progress > 0.22:
        droplet_progress = (
            progress - 0.22
        ) / 0.78

        for droplet_index in range(5):
            droplet_angle = (
                angle
                + 0.45
                + droplet_index * 0.23
            )
            droplet_distance = (
                14
                + droplet_progress
                * (
                    20
                    + droplet_index * 5
                )
            )
            droplet_position = (
                round(
                    center[0]
                    + math.cos(droplet_angle)
                    * droplet_distance
                ),
                round(
                    center[1]
                    + math.sin(droplet_angle)
                    * droplet_distance
                    * 0.65
                ),
            )
            pygame.draw.ellipse(
                slash_surface,
                (
                    205,
                    23,
                    38,
                    round(
                        alpha
                        * (
                            1
                            - droplet_progress
                            * 0.75
                        )
                    ),
                ),
                (
                    droplet_position[0] - 2,
                    droplet_position[1] - 1,
                    4,
                    2,
                ),
            )

    surface.blit(
        slash_surface,
        (0, 0),
    )


def _draw_impact_flash(
    surface,
    progress,
):
    flash_progress = min(
        1.0,
        progress * 2.4,
    )
    visibility = math.sin(
        math.pi * flash_progress
    )

    if visibility <= 0:
        return

    flash = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    flash.fill(
        (
            92,
            8,
            18,
            round(34 * visibility),
        )
    )
    surface.blit(flash, (0, 0))


def draw_killing_spree_target_marks(
    surface,
    player,
    floor,
    camera_x,
    camera_y,
):
    if not player.ultimate_aiming:
        return

    target_counts = {}

    for target_name in player.ultimate_targets:
        target_counts[target_name] = (
            target_counts.get(target_name, 0) + 1
        )

    for enemy in floor.enemies:
        mark_count = target_counts.get(
            enemy.name,
            0,
        )
        if enemy.health <= 0 or mark_count <= 0:
            continue

        enemy_position = _view_position(
            enemy.column,
            enemy.row,
            camera_x,
            camera_y,
        )
        center_x = (
            enemy_position[0]
            + ACT_THREE_TILE_SIZE // 2
        )
        mark_y = enemy_position[1] - 7

        for mark_index in range(mark_count):
            mark_x = (
                center_x
                - (mark_count - 1) * 5
                + mark_index * 10
            )
            pygame.draw.line(
                surface,
                (94, 16, 25),
                (mark_x - 3, mark_y + 5),
                (mark_x + 3, mark_y - 3),
                width=4,
            )
            pygame.draw.line(
                surface,
                (238, 58, 68),
                (mark_x - 3, mark_y + 5),
                (mark_x + 3, mark_y - 3),
                width=2,
            )


def draw_killing_spree_effects(
    surface,
    player,
    floor,
    assets,
    current_time,
    camera_x,
    camera_y,
):
    if not player.ultimate_animation_active:
        return

    targets = _selected_enemies(
        floor,
        player.ultimate_targets,
    )
    if not targets:
        return

    elapsed = _ultimate_elapsed(
        player,
        current_time,
    )
    outro_start = _outro_started_at(
        len(targets)
    )

    if elapsed < ASSASSIN_ULTIMATE_PRELUDE_MS:
        darkness_progress = (
            elapsed
            / ASSASSIN_ULTIMATE_PRELUDE_MS
        )
    elif elapsed < outro_start:
        darkness_progress = 1.0
    else:
        darkness_progress = 1.0 - min(
            1.0,
            (
                elapsed - outro_start
            )
            / ASSASSIN_ULTIMATE_OUTRO_MS,
        )

    darkness = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    darkness.fill(
        (
            4,
            2,
            7,
            round(108 * darkness_progress),
        )
    )
    surface.blit(darkness, (0, 0))

    strikes_elapsed = _strike_elapsed(
        player,
        current_time,
    )
    if strikes_elapsed < 0:
        return

    completed_steps = min(
        len(targets),
        max(
            0,
            int(
                strikes_elapsed
                // ASSASSIN_ULTIMATE_STEP_MS
            ),
        ),
    )

    for target_index in range(completed_steps):
        target = targets[target_index]
        target_position = _view_position(
            target.column,
            target.row,
            camera_x,
            camera_y,
        )
        variant = (
            player.ultimate_visual_variants[
                target_index
            ]
            if target_index
            < len(player.ultimate_visual_variants)
            else target_index % 4
        )
        afterimage = assets[
            (
                "player_assassin_killing_spree_"
                f"{variant}_1"
            )
        ].copy()
        age = (
            strikes_elapsed
            - (
                target_index + 1
            )
            * ASSASSIN_ULTIMATE_STEP_MS
        )
        afterimage_lifetime = (
            ASSASSIN_ULTIMATE_STEP_MS * 1.65
        )
        afterimage_progress = min(
            1.0,
            max(
                0.0,
                age / afterimage_lifetime,
            ),
        )
        afterimage_alpha = round(
            68
            * (
                1
                - afterimage_progress
            )
            ** 2
        )

        if afterimage_alpha > 0:
            afterimage.fill(
                (28, 0, 7, 0),
                special_flags=pygame.BLEND_RGB_ADD,
            )
            afterimage.set_alpha(
                afterimage_alpha
            )
            surface.blit(
                afterimage,
                (
                    target_position[0]
                    + (
                        -2
                        if variant % 2 == 0
                        else 2
                    ),
                    target_position[1],
                ),
            )

    if strikes_elapsed >= _strike_duration(
        len(targets)
    ):
        return

    target_index = min(
        len(targets) - 1,
        int(
            strikes_elapsed
            // ASSASSIN_ULTIMATE_STEP_MS
        ),
    )
    step_elapsed = (
        strikes_elapsed
        % ASSASSIN_ULTIMATE_STEP_MS
    )
    travel_duration = (
        ASSASSIN_ULTIMATE_STEP_MS
        * ASSASSIN_ULTIMATE_CAMERA_TRAVEL_RATIO
    )

    if step_elapsed < travel_duration:
        return

    action_duration = (
        ASSASSIN_ULTIMATE_STEP_MS
        - travel_duration
    )
    phase_duration = action_duration / 2
    action_elapsed = (
        step_elapsed - travel_duration
    )
    phase_index = (
        0
        if action_elapsed < phase_duration
        else 1
    )
    phase_progress = (
        action_elapsed / phase_duration
        if phase_index == 0
        else (
            action_elapsed - phase_duration
        ) / phase_duration
    )
    target = targets[target_index]
    target_position = _view_position(
        target.column,
        target.row,
        camera_x,
        camera_y,
    )
    variant = (
        player.ultimate_visual_variants[
            target_index
        ]
        if target_index
        < len(player.ultimate_visual_variants)
        else target_index % 4
    )

    _draw_assassin_invisibility_effect(
        surface,
        target_position[0],
        target_position[1],
        current_time,
        target_index + variant * 7,
    )

    surface.blit(
        assets[
            (
                "player_assassin_killing_spree_"
                f"{variant}_{phase_index}"
            )
        ],
        target_position,
    )

    if phase_index == 1:
        _draw_impact_flash(
            surface,
            phase_progress,
        )
        _draw_crimson_slashes(
            surface,
            target_position,
            phase_progress,
            target_index + variant,
        )


def draw_killing_spree_final_impacts(
    surface,
    player,
    current_time,
    camera_x,
    camera_y,
):
    if (
        player.ultimate_impact_started_at <= 0
        or not player.ultimate_impact_positions
    ):
        return

    elapsed = (
        current_time
        - player.ultimate_impact_started_at
    )
    if not 0 <= elapsed < (
        ASSASSIN_ULTIMATE_FINAL_IMPACT_MS
    ):
        return

    progress = (
        elapsed
        / ASSASSIN_ULTIMATE_FINAL_IMPACT_MS
    )

    for impact_index, impact_position in enumerate(
        player.ultimate_impact_positions
    ):
        view_position = _view_position(
            impact_position[0],
            impact_position[1],
            camera_x,
            camera_y,
        )
        delayed_progress = max(
            0.0,
            min(
                1.0,
                progress * 1.35
                - impact_index * 0.045,
            ),
        )

        _draw_assassin_invisibility_effect(
            surface,
            view_position[0],
            view_position[1],
            current_time,
            impact_index * 13,
        )
        _draw_crimson_slashes(
            surface,
            view_position,
            delayed_progress,
            impact_index * 3,
        )

    _draw_impact_flash(
        surface,
        progress,
    )