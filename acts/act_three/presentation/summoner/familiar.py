import math

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE


SUMMONER_FAMILIAR_FRAME_COUNT = 8
SUMMONER_FAMILIAR_FRAME_DURATION_MS = 120
SUMMONER_FAMILIAR_MOVE_DURATION_MS = 180

_SUMMONER_FAMILIAR_FRAME_SOURCES = {
    "left": ("fly_left", "idle_left"),
    "right": ("fly_right", "idle_down"),
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

    for direction, (
        directory_name,
        file_prefix,
    ) in _SUMMONER_FAMILIAR_FRAME_SOURCES.items():
        for frame_index in range(
            SUMMONER_FAMILIAR_FRAME_COUNT
        ):
            source_index = frame_index + 1
            assets[
                (
                    "summoner_familiar_fly_"
                    f"{direction}_{frame_index}"
                )
            ] = image_loader(
                familiar_directory
                / directory_name
                / f"{file_prefix}_{source_index:02d}.png",
                (tile_size, tile_size),
            )

    assets["summoner_familiar_attack"] = image_loader(
        familiar_directory
        / "attack"
        / "attack_00.png",
        (tile_size, tile_size),
    )


def summoner_familiar_direction(player):
    familiar_position = player.summoner_familiar_position
    familiar_origin = (
        player.summoner_familiar_movement_origin
    )

    if (
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


def summoner_familiar_sprite(
    assets,
    player,
    current_time,
    attack_duration,
    direction,
):
    attack_elapsed = (
        current_time
        - player.summoner_familiar_attack_started_at
    )

    if (
        player.summoner_true_form_active
        and 0 <= attack_elapsed < attack_duration
    ):
        return assets["summoner_true_form_attack"]

    if player.summoner_true_form_active:
        frame = (current_time // 180) % 3
        return assets[
            f"summoner_true_form_idle_{frame}"
        ]

    if 0 <= attack_elapsed < attack_duration:
        return assets["summoner_familiar_attack"]

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
