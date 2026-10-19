import math

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.summoner.true_form import (
    summoner_true_form_sprite,
)


SUMMONER_FAMILIAR_FRAME_COUNT = 8
SUMMONER_FAMILIAR_FRAME_DURATION_MS = 120
SUMMONER_FAMILIAR_SUMMON_DURATION_MS = 760
SUMMONER_FAMILIAR_MOVE_DURATION_MS = 180
SUMMONER_FAMILIAR_ATTACK_DURATION_MS = 480
SUMMONER_FAMILIAR_HURT_DURATION_MS = 320
SUMMONER_FAMILIAR_DEATH_FRAME_DURATION_MS = 120
SUMMONER_FAMILIAR_DEATH_DURATION_MS = (
    SUMMONER_FAMILIAR_FRAME_COUNT
    * SUMMONER_FAMILIAR_DEATH_FRAME_DURATION_MS
)

_SUMMONER_FAMILIAR_ANIMATION_SOURCES = {
    ("fly", "left"): ("fly_left", "idle_left"),
    ("fly", "right"): ("fly_right", "idle_down"),
    ("attack", "left"): ("attack_left", "attack_left"),
    ("attack", "right"): ("attack_right", "attack_right"),
    ("hurt", "left"): ("hurt_left", "hurt_left"),
    ("hurt", "right"): ("hurt_right", "hurt_right"),
    ("death", "left"): ("death_left", "death_left"),
    ("death", "right"): ("death_right", "death_right"),
}


def load_summoner_familiar_assets(
    assets,
    act_directory,
    tile_size,
    image_loader,
):
    familiar_directory = (
        act_directory
        / "player"
        / "summoner"
        / "summoner_familiar"
    )

    for (
        animation,
        direction,
    ), (
        directory_name,
        file_prefix,
    ) in _SUMMONER_FAMILIAR_ANIMATION_SOURCES.items():
        animation_directory = (
            familiar_directory
            / animation
            / directory_name
        )

        for frame_index in range(
            SUMMONER_FAMILIAR_FRAME_COUNT
        ):
            source_index = frame_index + 1
            assets[
                (
                    f"summoner_familiar_{animation}_"
                    f"{direction}_{frame_index}"
                )
            ] = image_loader(
                animation_directory
                / f"{file_prefix}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

        summon_directory = (
                familiar_directory
                / "summon"
                / "summon_left"
        )
        for frame_index in range(
                SUMMONER_FAMILIAR_FRAME_COUNT
        ):
            source_index = frame_index + 1
            left_sprite = image_loader(
                summon_directory
                / f"summon_left_{source_index:02d}.png",
                (tile_size, tile_size),
            )
            assets[
                f"summoner_familiar_summon_left_{frame_index}"
            ] = left_sprite
            assets[
                f"summoner_familiar_summon_right_{frame_index}"
            ] = pygame.transform.flip(
                left_sprite,
                True,
                False,
            )


def summoner_familiar_direction(player):
    familiar_position = (
        player.summoner_familiar_position
        or player.summoner_familiar_hit_position
    )
    attack_target = player.summoner_familiar_attack_target
    familiar_origin = (
        player.summoner_familiar_movement_origin
    )

    if (
        familiar_position is not None
        and attack_target is not None
    ):
        direction_column = (
            attack_target[0] - familiar_position[0]
        )
        direction_row = (
            attack_target[1] - familiar_position[1]
        )
    elif (
        familiar_position is not None
        and familiar_origin is not None
    ):
        direction_column = (
            familiar_position[0] - familiar_origin[0]
        )
        direction_row = (
            familiar_position[1] - familiar_origin[1]
        )
    else:
        direction_column, direction_row = (
            player.facing_direction
        )

    if direction_column < 0:
        return "left"

    if direction_column > 0:
        return "right"

    if direction_row < 0:
        return "left"

    return "right"


def summoner_familiar_is_moving(
    player,
    current_time,
):
    elapsed = (
        current_time
        - player.summoner_familiar_movement_started_at
    )
    return (
            player.summoner_familiar_movement_origin is not None
            and 0 <= elapsed < SUMMONER_FAMILIAR_MOVE_DURATION_MS
    )


def _summoner_familiar_animation_frame(
        elapsed,
        duration,
):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )
    return min(
        SUMMONER_FAMILIAR_FRAME_COUNT - 1,
        int(progress * SUMMONER_FAMILIAR_FRAME_COUNT),
    )


def summoner_familiar_death_active(
        player,
        current_time,
):
    elapsed = (
            current_time
            - player.summoner_familiar_hit_animation_started_at
    )
    return (
            player.summoner_familiar_health <= 0
            and player.summoner_familiar_hit_animation_started_at >= 0
            and 0 <= elapsed < SUMMONER_FAMILIAR_DEATH_DURATION_MS
    )


def summoner_familiar_summon_active(
    player,
    current_time,
):
    elapsed = (
        current_time
        - player.summoner_familiar_summoned_at
    )
    return (
        player.summoner_familiar_summoned_at >= 0
        and 0
        <= elapsed
        < SUMMONER_FAMILIAR_SUMMON_DURATION_MS
    )


def summoner_familiar_sprite(
    assets,
    player,
    current_time,
    direction,
):
    hit_elapsed = (
        current_time
        - player.summoner_familiar_hit_animation_started_at
    )

    if summoner_familiar_death_active(
        player,
        current_time,
    ):
        frame = _summoner_familiar_animation_frame(
            hit_elapsed,
            SUMMONER_FAMILIAR_DEATH_DURATION_MS,
        )
        return assets[
            f"summoner_familiar_death_{direction}_{frame}"
        ]

    if summoner_familiar_summon_active(
        player,
        current_time,
    ):
        summon_elapsed = (
            current_time
            - player.summoner_familiar_summoned_at
        )
        frame = _summoner_familiar_animation_frame(
            summon_elapsed,
            SUMMONER_FAMILIAR_SUMMON_DURATION_MS,
        )
        return assets[
            (
                "summoner_familiar_summon_"
                f"{player.summoner_familiar_summon_direction}_"
                f"{frame}"
            )
        ]

    true_form_sprite = summoner_true_form_sprite(
        assets,
        player,
        current_time,
    )
    if true_form_sprite is not None:
        return true_form_sprite

    if (
        player.summoner_familiar_hit_animation_started_at >= 0
        and 0 <= hit_elapsed < SUMMONER_FAMILIAR_HURT_DURATION_MS
    ):
        frame = _summoner_familiar_animation_frame(
            hit_elapsed,
            SUMMONER_FAMILIAR_HURT_DURATION_MS,
        )
        return assets[
            f"summoner_familiar_hurt_{direction}_{frame}"
        ]

    attack_elapsed = (
        current_time
        - player.summoner_familiar_attack_started_at
    )

    if (
        0
        <= attack_elapsed
        < SUMMONER_FAMILIAR_ATTACK_DURATION_MS
    ):
        frame = _summoner_familiar_animation_frame(
            attack_elapsed,
            SUMMONER_FAMILIAR_ATTACK_DURATION_MS,
        )
        return assets[
            f"summoner_familiar_attack_{direction}_{frame}"
        ]

    frame = (
        current_time
        // SUMMONER_FAMILIAR_FRAME_DURATION_MS
    ) % SUMMONER_FAMILIAR_FRAME_COUNT

    return assets[
        f"summoner_familiar_fly_{direction}_{frame}"
    ]


def draw_summoner_familiar_aura(
    surface,
    position,
    current_time,
    direction,
    moving,
):
    margin = 20
    effect_surface = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE + margin * 2,
            ACT_THREE_TILE_SIZE + margin * 2,
        ),
        pygame.SRCALPHA,
    )
    center = (
        margin + ACT_THREE_TILE_SIZE // 2,
        margin + ACT_THREE_TILE_SIZE // 2 + 6,
    )
    pulse = 0.5 + 0.5 * math.sin(current_time / 170)
    glow_alpha = round(28 + pulse * 24)

    pygame.draw.ellipse(
        effect_surface,
        (7, 90, 101, glow_alpha),
        (
            center[0] - 19,
            center[1] - 9,
            38,
            18,
        ),
    )
    pygame.draw.ellipse(
        effect_surface,
        (26, 185, 185, round(55 + pulse * 35)),
        (
            center[0] - 17,
            center[1] - 7,
            34,
            14,
        ),
        width=1,
    )

    ring_start = (
        current_time / 520
    ) % math.tau
    pygame.draw.arc(
        effect_surface,
        (89, 225, 218, round(80 + pulse * 45)),
        (
            center[0] - 21,
            center[1] - 12,
            42,
            24,
        ),
        ring_start,
        ring_start + 2.25,
        width=2,
    )
    pygame.draw.arc(
        effect_surface,
        (112, 78, 170, round(45 + pulse * 30)),
        (
            center[0] - 24,
            center[1] - 14,
            48,
            28,
        ),
        ring_start + math.pi,
        ring_start + math.pi + 1.85,
        width=1,
    )

    if moving:
        facing = -1 if direction == "left" else 1

        for trail_index in range(5):
            trail_distance = 10 + trail_index * 7
            trail_x = (
                center[0] - facing * trail_distance
            )
            trail_y = (
                center[1]
                + round(
                    math.sin(
                        current_time / 85 + trail_index
                    ) * 3
                )
            )
            trail_alpha = round(
                (82 - trail_index * 12)
                * (0.72 + pulse * 0.28)
            )
            trail_width = 11 + trail_index * 2
            trail_height = 5 + trail_index

            pygame.draw.ellipse(
                effect_surface,
                (
                    22 + trail_index * 5,
                    179,
                    181,
                    trail_alpha,
                ),
                (
                    trail_x - trail_width // 2,
                    trail_y - trail_height // 2,
                    trail_width,
                    trail_height,
                ),
            )
    else:
        for mote_index in range(6):
            angle = (
                current_time / 410
                + mote_index * math.tau / 6
            )
            radius_x = 17 + mote_index % 2 * 4
            radius_y = 9 + mote_index % 3
            mote_position = (
                center[0] + round(
                    math.cos(angle) * radius_x
                ),
                center[1] + round(
                    math.sin(angle) * radius_y
                ),
            )
            mote_radius = (
                2 if mote_index % 3 == 0 else 1
            )

            pygame.draw.circle(
                effect_surface,
                (
                    97 + mote_index * 9,
                    224,
                    216,
                    round(95 + pulse * 70),
                ),
                mote_position,
                mote_radius,
            )

    surface.blit(
        effect_surface,
        (
            position[0] - margin,
            position[1] - margin,
        ),
    )


def draw_summoner_familiar_attack_effect(
    surface,
    origin_position,
    target_position,
    current_time,
    started_at,
):
    elapsed = current_time - started_at
    if not (
        0
        <= elapsed
        < SUMMONER_FAMILIAR_ATTACK_DURATION_MS
    ):
        return

    progress = (
        elapsed / SUMMONER_FAMILIAR_ATTACK_DURATION_MS
    )
    margin = 14
    left = min(origin_position[0], target_position[0]) - margin
    top = min(origin_position[1], target_position[1]) - margin
    right = (
        max(origin_position[0], target_position[0])
        + ACT_THREE_TILE_SIZE
        + margin
    )
    bottom = (
        max(origin_position[1], target_position[1])
        + ACT_THREE_TILE_SIZE
        + margin
    )
    effect_surface = pygame.Surface(
        (right - left, bottom - top),
        pygame.SRCALPHA,
    )
    origin_center = (
        origin_position[0]
        + ACT_THREE_TILE_SIZE // 2
        - left,
        origin_position[1]
        + ACT_THREE_TILE_SIZE // 2
        - top,
    )
    target_center = (
        target_position[0]
        + ACT_THREE_TILE_SIZE // 2
        - left,
        target_position[1]
        + ACT_THREE_TILE_SIZE // 2
        - top,
    )
    travel_progress = min(
        1.0,
        progress / 0.45,
    )

    for mote_index in range(4):
        mote_progress = max(
            0.0,
            min(
                1.0,
                travel_progress - mote_index * 0.08,
            ),
        )
        mote_position = (
            round(
                origin_center[0]
                + (
                    target_center[0] - origin_center[0]
                )
                * mote_progress
            ),
            round(
                origin_center[1]
                + (
                    target_center[1] - origin_center[1]
                )
                * mote_progress
                + math.sin(
                    progress * math.tau * 2 + mote_index
                )
                * 3
            ),
        )
        pygame.draw.circle(
            effect_surface,
            (
                71 + mote_index * 15,
                229,
                220,
                170 - mote_index * 28,
            ),
            mote_position,
            3 if mote_index == 0 else 2,
        )

    impact_progress = max(
        0.0,
        min(1.0, (progress - 0.24) / 0.76),
    )
    if impact_progress > 0:
        visibility = math.sin(
            math.pi * impact_progress
        )
        radius = round(6 + impact_progress * 15)
        alpha = round(190 * visibility)

        pygame.draw.circle(
            effect_surface,
            (42, 205, 196, alpha),
            target_center,
            radius,
            width=2,
        )
        pygame.draw.arc(
            effect_surface,
            (170, 97, 218, alpha),
            (
                target_center[0] - radius - 4,
                target_center[1] - radius - 4,
                radius * 2 + 8,
                radius * 2 + 8,
            ),
            progress * math.tau,
            progress * math.tau + 2.4,
            width=2,
        )

    surface.blit(
        effect_surface,
        (left, top),
    )
