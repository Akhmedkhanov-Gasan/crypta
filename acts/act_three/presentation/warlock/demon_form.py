import math

import pygame

from acts.act_three.presentation.player_motion import (
    assassin_walk_direction,
)
from acts.act_three.settings import (
    WARLOCK_DEMON_FORM_TRANSFORM_MS,
)
from presentation.layout import ACT_THREE_TILE_SIZE


_DEMON_FORM_FRAME_COUNT = 8
_DEMON_FORM_IDLE_FRAME_MS = 210


def load_warlock_demon_form_assets(
    assets,
    warlock_directory,
    tile_size,
    image_loader,
):
    demon_form_directory = (
        warlock_directory / "demon_form"
    )
    idle_directory = demon_form_directory / "idle"
    walk_directory = demon_form_directory / "walk"
    attack_directory = demon_form_directory / "attack"
    hurt_directory = demon_form_directory / "hurt"
    transform_directory = (
        demon_form_directory / "transform_down"
    )
    idle_sources = {
        "down": (
            "demon_idle_down",
            "idle_down",
        ),
        "left": (
            "demon_idle_left",
            "idle_left",
        ),
        "right": (
            "idle_right_01",
            "idle_right",
        ),
        "up": (
            "demon_idle_up",
            "idle_up",
        ),
    }
    walk_sources = {
        "down": (
            "demon_walk_down",
            "walk_down",
        ),
        "left": (
            "demon_walk_left",
            "walk_left",
        ),
        "right": (
            "walk_right",
            "walk_right",
        ),
        "up": (
            "demon_walk_up",
            "walk_up",
        ),
    }
    attack_sources = {
        "down": (
            "demon_attack_down",
            "attack_down",
        ),
        "left": (
            "demon_attack_left",
            "attack_left",
        ),
        "right": (
            "attack_right",
            "attack_right",
        ),
        "up": (
            "demon_attack_up",
            "attack_up",
        ),
    }
    hurt_sources = {
        "down": (
            "demon_hurt_down",
            "hurt_down",
        ),
        "left": (
            "demon_hurt_left",
            "hurt_left",
        ),
        "right": (
            "hurt_right",
            "hurt_right",
        ),
        "up": (
            "demon_hurt_up",
            "hurt_up",
        ),
    }

    for frame_index in range(_DEMON_FORM_FRAME_COUNT):
        source_index = frame_index + 1

        for direction, (
            idle_directory_name,
            idle_filename_prefix,
        ) in idle_sources.items():
            walk_directory_name, walk_filename_prefix = (
                walk_sources[direction]
            )
            attack_directory_name, attack_filename_prefix = (
                attack_sources[direction]
            )
            hurt_directory_name, hurt_filename_prefix = (
                hurt_sources[direction]
            )
            idle_sprite = image_loader(
                idle_directory
                / idle_directory_name
                / (
                    f"{idle_filename_prefix}_"
                    f"{source_index:02d}.png"
                ),
                (tile_size, tile_size),
            )
            walk_sprite = image_loader(
                walk_directory
                / walk_directory_name
                / (
                    f"{walk_filename_prefix}_"
                    f"{source_index:02d}.png"
                ),
                (tile_size, tile_size),
            )
            attack_sprite = image_loader(
                attack_directory
                / attack_directory_name
                / (
                    f"{attack_filename_prefix}_"
                    f"{source_index:02d}.png"
                ),
                (tile_size, tile_size),
            )
            hurt_sprite = image_loader(
                hurt_directory
                / hurt_directory_name
                / (
                    f"{hurt_filename_prefix}_"
                    f"{source_index:02d}.png"
                ),
                (tile_size, tile_size),
            )
            assets[
                (
                    "player_warlock_demon_idle_"
                    f"{direction}_{frame_index}"
                )
            ] = idle_sprite
            assets[
                (
                    "player_warlock_demon_walk_"
                    f"{direction}_{frame_index}"
                )
            ] = walk_sprite
            assets[
                (
                    "player_warlock_demon_attack_"
                    f"{direction}_{frame_index}"
                )
            ] = attack_sprite
            assets[
                (
                    "player_warlock_demon_hurt_"
                    f"{direction}_{frame_index}"
                )
            ] = hurt_sprite

        assets[
            f"player_warlock_demon_idle_{frame_index}"
        ] = assets[
            f"player_warlock_demon_idle_down_{frame_index}"
        ]
        assets[
            f"player_warlock_demon_walk_{frame_index}"
        ] = assets[
            f"player_warlock_demon_walk_down_{frame_index}"
        ]
        assets[
            f"player_warlock_demon_attack_{frame_index}"
        ] = assets[
            f"player_warlock_demon_attack_down_{frame_index}"
        ]
        assets[
            f"player_warlock_demon_hurt_{frame_index}"
        ] = assets[
            f"player_warlock_demon_hurt_down_{frame_index}"
        ]
        assets[
            f"player_warlock_demon_transform_{frame_index}"
        ] = image_loader(
            transform_directory
            / f"transform_down_{source_index:02d}.png",
            (tile_size, tile_size),
        )

    assets["player_warlock_demon_attack"] = assets[
        "player_warlock_demon_attack_down_0"
    ]
    assets["player_warlock_demon_hurt"] = assets[
        "player_warlock_demon_hurt_down_0"
    ]


def _warlock_demon_transition_state(
    player,
    current_time,
):
    target_active = (
        player.warlock_demon_form_target_active
    )
    started_at = player.warlock_demon_form_started_at
    if target_active is None or started_at < 0:
        return None

    elapsed = current_time - started_at
    if (
        elapsed < 0
        or elapsed >= WARLOCK_DEMON_FORM_TRANSFORM_MS
    ):
        return None

    return (
        elapsed / WARLOCK_DEMON_FORM_TRANSFORM_MS,
        target_active,
    )


def warlock_demon_transition_sprite(
    player,
    assets,
    current_time,
):
    transition = _warlock_demon_transition_state(
        player,
        current_time,
    )
    if transition is None:
        return None

    progress, target_active = transition
    frame = min(
        _DEMON_FORM_FRAME_COUNT - 1,
        int(progress * _DEMON_FORM_FRAME_COUNT),
    )
    if not target_active:
        frame = _DEMON_FORM_FRAME_COUNT - 1 - frame

    return assets[
        f"player_warlock_demon_transform_{frame}"
    ]


def warlock_demon_idle_sprite(
    player,
    assets,
    current_time,
):
    idle_started_at = (
        player.warlock_demon_form_started_at
        + WARLOCK_DEMON_FORM_TRANSFORM_MS
    )
    elapsed = max(
        0,
        current_time - idle_started_at,
    )
    frame = (
        elapsed // _DEMON_FORM_IDLE_FRAME_MS
    ) % _DEMON_FORM_FRAME_COUNT
    direction = assassin_walk_direction(
        player.facing_direction
    )
    return assets[
        (
            "player_warlock_demon_idle_"
            f"{direction}_{frame}"
        )
    ]


def draw_warlock_demon_smoke(
    surface,
    position,
    current_time,
):
    horizontal_margin = 30
    top_margin = 8
    width = (
        ACT_THREE_TILE_SIZE
        + horizontal_margin * 2
    )
    height = ACT_THREE_TILE_SIZE + 20
    smoke_surface = pygame.Surface(
        (width, height),
        pygame.SRCALPHA,
    )
    center_x = horizontal_margin + ACT_THREE_TILE_SIZE // 2
    ground_y = top_margin + ACT_THREE_TILE_SIZE - 5
    pulse = 0.5 + 0.5 * math.sin(current_time / 410)

    pygame.draw.ellipse(
        smoke_surface,
        (
            19,
            4,
            31,
            round(58 + pulse * 24),
        ),
        (
            center_x - 37,
            ground_y - 6,
            74,
            17,
        ),
    )
    pygame.draw.ellipse(
        smoke_surface,
        (
            73,
            19,
            103,
            round(30 + pulse * 18),
        ),
        (
            center_x - 30,
            ground_y - 4,
            60,
            11,
        ),
    )

    anchors = (
        -27,
        -21,
        -15,
        -9,
        -3,
        4,
        10,
        16,
        22,
        28,
    )
    smoke_count = len(anchors)

    for smoke_index, anchor in enumerate(anchors):
        phase = (
            current_time / 1750
            + smoke_index / smoke_count
        ) % 1
        visibility = math.sin(math.pi * phase)
        side = -1 if anchor < 0 else 1
        outward = round(
            side * phase * (5 + smoke_index % 3)
        )
        drift = round(
            math.sin(
                current_time / 330
                + smoke_index * 1.8
            )
            * 4
        )
        rise = round(
            phase * (11 + smoke_index % 4 * 4)
        )
        smoke_x = (
            center_x
            + anchor
            + outward
            + drift
        )
        smoke_y = (
            ground_y
            - rise
            + round(
                math.sin(
                    current_time / 270
                    + smoke_index
                )
                * 2
            )
        )
        radius_x = round(
            5
            + visibility * (4 + smoke_index % 3)
        )
        radius_y = round(
            3
            + visibility * (3 + smoke_index % 2)
        )
        alpha = round(105 * visibility)

        pygame.draw.ellipse(
            smoke_surface,
            (
                24,
                5,
                38,
                alpha,
            ),
            (
                smoke_x - radius_x,
                smoke_y - radius_y,
                radius_x * 2,
                radius_y * 2,
            ),
        )
        pygame.draw.ellipse(
            smoke_surface,
            (
                76,
                20,
                112,
                alpha // 2,
            ),
            (
                smoke_x - radius_x + 2,
                smoke_y - radius_y,
                max(2, radius_x * 2 - 4),
                max(2, radius_y * 2 - 2),
            ),
        )
        pygame.draw.circle(
            smoke_surface,
            (
                137,
                48,
                181,
                alpha // 3,
            ),
            (
                smoke_x,
                smoke_y - radius_y + 1,
            ),
            max(1, radius_y // 2),
        )

    for wisp_index in range(4):
        phase = (
            current_time / 2100
            + wisp_index * 0.23
        ) % 1
        visibility = math.sin(math.pi * phase)
        base_x = (
            center_x
            + (-18 + wisp_index * 12)
        )
        sway = round(
            math.sin(
                current_time / 290
                + wisp_index * 2.1
            )
            * 5
        )
        height_offset = round(
            phase * (17 + wisp_index % 2 * 7)
        )
        alpha = round(72 * visibility)
        points = (
            (
                base_x,
                ground_y + 1,
            ),
            (
                base_x + sway // 2,
                ground_y - height_offset // 2,
            ),
            (
                base_x + sway,
                ground_y - height_offset,
            ),
        )
        pygame.draw.lines(
            smoke_surface,
            (
                48,
                9,
                69,
                alpha,
            ),
            False,
            points,
            width=5,
        )
        pygame.draw.lines(
            smoke_surface,
            (
                119,
                34,
                157,
                alpha // 2,
            ),
            False,
            points,
            width=2,
        )

    surface.blit(
        smoke_surface,
        (
            position[0] - horizontal_margin,
            position[1] - top_margin,
        ),
    )


def draw_warlock_demon_transformation(
    surface,
    player,
    position,
    current_time,
):
    transition = _warlock_demon_transition_state(
        player,
        current_time,
    )
    if transition is None:
        return

    progress, target_active = transition
    intensity = math.sin(math.pi * progress)
    margin = 28
    size = ACT_THREE_TILE_SIZE + margin * 2
    center = (
        margin + ACT_THREE_TILE_SIZE // 2,
        margin + ACT_THREE_TILE_SIZE // 2,
    )
    effect_surface = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )

    primary_color = (
        (205, 69, 255)
        if target_active
        else (111, 69, 163)
    )
    ring_radius = round(9 + progress * 45)
    ring_alpha = round(220 * intensity)

    pygame.draw.circle(
        effect_surface,
        (*primary_color, ring_alpha // 4),
        center,
        ring_radius + 7,
        width=5,
    )
    pygame.draw.circle(
        effect_surface,
        (*primary_color, ring_alpha),
        center,
        ring_radius,
        width=2,
    )

    for particle_index in range(12):
        angle = (
            particle_index * math.tau / 12
            + current_time / 360
        )
        travel = (
            34 * (1 - progress)
            if target_active
            else 34 * progress
        )
        particle_position = (
            center[0] + round(math.cos(angle) * travel),
            center[1] + round(math.sin(angle) * travel),
        )
        particle_radius = 1 + particle_index % 2
        pygame.draw.circle(
            effect_surface,
            (
                primary_color[0],
                primary_color[1],
                primary_color[2],
                round(235 * intensity),
            ),
            particle_position,
            particle_radius,
        )

    core_radius = round(7 + intensity * 14)
    pygame.draw.circle(
        effect_surface,
        (223, 104, 255, round(55 * intensity)),
        center,
        core_radius,
    )
    pygame.draw.circle(
        effect_surface,
        (255, 213, 255, round(190 * intensity)),
        center,
        max(2, core_radius // 3),
        width=2,
    )

    surface.blit(
        effect_surface,
        (
            position[0] - margin,
            position[1] - margin,
        ),
    )

    flash_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    flash_surface.fill(
        (48, 5, 72, round(34 * intensity))
    )
    surface.blit(flash_surface, (0, 0))
