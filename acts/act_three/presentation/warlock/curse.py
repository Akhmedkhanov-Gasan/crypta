import math

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE
from acts.act_three.presentation.player_motion import (
    assassin_attack_direction,
    movement_frame_for_progress,
)


WARLOCK_CURSE_FRAME_COUNT = 8
WARLOCK_CURSE_CAST_DURATION_MS = 520


def load_warlock_curse_assets(
    assets,
    warlock_directory,
    tile_size,
    image_loader,
):
    curse_directory = warlock_directory / "curse"
    directions = (
        "down",
        "left",
        "right",
        "up",
    )

    for direction in directions:
        for frame_index in range(WARLOCK_CURSE_FRAME_COUNT):
            source_index = frame_index + 1
            assets[
                f"player_warlock_curse_{direction}_{frame_index}"
            ] = image_loader(
                curse_directory
                / f"curse_{direction}"
                / f"curse_{direction}_{source_index:02d}.png",
                (tile_size, tile_size),
            )


def warlock_curse_sprite(
    player,
    assets,
    current_time,
):
    if (
        player.subclass != "warlock"
        or player.warlock_curse_started_at <= 0
    ):
        return None

    elapsed = (
        current_time
        - player.warlock_curse_started_at
    )

    if not 0 <= elapsed < WARLOCK_CURSE_CAST_DURATION_MS:
        return None

    direction = assassin_attack_direction(
        player.facing_direction
    )
    frame = movement_frame_for_progress(
        elapsed / WARLOCK_CURSE_CAST_DURATION_MS,
        WARLOCK_CURSE_FRAME_COUNT,
    )

    return assets[
        f"player_warlock_curse_{direction}_{frame}"
    ]


def draw_warlock_curse_cast(
    surface,
    origin_position,
    target_position,
    current_time,
    started_at,
):
    elapsed = current_time - started_at

    if not 0 <= elapsed < WARLOCK_CURSE_CAST_DURATION_MS:
        return

    progress = elapsed / WARLOCK_CURSE_CAST_DURATION_MS
    reveal = min(1.0, progress * 4)
    fade = min(1.0, (1 - progress) * 4)
    visibility = reveal * fade
    overlay = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    half_tile = ACT_THREE_TILE_SIZE // 2
    origin = (
        origin_position[0] + half_tile,
        origin_position[1] + half_tile,
    )
    target = (
        target_position[0] + half_tile,
        target_position[1] + half_tile,
    )
    difference_x = target[0] - origin[0]
    difference_y = target[1] - origin[1]
    points = []

    for point_index in range(17):
        point_progress = point_index / 16
        wave = math.sin(
            point_progress * math.tau * 2
            - current_time * 0.025
        )
        points.append(
            (
                round(
                    origin[0]
                    + difference_x * point_progress
                    + wave * 4
                ),
                round(
                    origin[1]
                    + difference_y * point_progress
                    + math.cos(
                        point_progress * math.tau * 2
                        - current_time * 0.021
                    )
                    * 3
                ),
            )
        )

    pygame.draw.lines(
        overlay,
        (83, 12, 111, round(105 * visibility)),
        False,
        points,
        width=7,
    )
    pygame.draw.lines(
        overlay,
        (220, 82, 255, round(230 * visibility)),
        False,
        points,
        width=2,
    )

    radius = round(
        ACT_THREE_TILE_SIZE
        * (0.18 + progress * 0.55)
    )

    pygame.draw.circle(
        overlay,
        (123, 24, 172, round(75 * visibility)),
        target,
        radius,
    )
    pygame.draw.circle(
        overlay,
        (235, 116, 255, round(225 * visibility)),
        target,
        radius,
        width=2,
    )

    for rune_index in range(6):
        angle = (
            current_time * 0.008
            + rune_index * math.tau / 6
        )
        rune_position = (
            round(target[0] + math.cos(angle) * radius),
            round(target[1] + math.sin(angle) * radius),
        )
        pygame.draw.circle(
            overlay,
            (
                247,
                166,
                255,
                round(230 * visibility),
            ),
            rune_position,
            2,
        )

    surface.blit(overlay, (0, 0))


def draw_warlock_curse_status(
    surface,
    left,
    top,
    current_time,
    identity_seed,
    turns,
    font,
):
    effect_surface = pygame.Surface(
        (
            ACT_THREE_TILE_SIZE,
            ACT_THREE_TILE_SIZE,
        ),
        pygame.SRCALPHA,
    )
    center = (
        ACT_THREE_TILE_SIZE // 2,
        ACT_THREE_TILE_SIZE // 2,
    )
    pulse = (
        math.sin(
            current_time * 0.011
            + identity_seed % 19
        )
        + 1
    ) / 2
    rotation = (
        current_time * 0.004
        + identity_seed % 97
    )

    pygame.draw.ellipse(
        effect_surface,
        (105, 17, 148, round(42 + pulse * 30)),
        (5, 13, ACT_THREE_TILE_SIZE - 10, 39),
    )
    pygame.draw.ellipse(
        effect_surface,
        (221, 86, 255, round(155 + pulse * 70)),
        (5, 13, ACT_THREE_TILE_SIZE - 10, 39),
        width=2,
    )

    for rune_index in range(6):
        angle = rotation + rune_index * math.tau / 6
        rune_position = (
            round(center[0] + math.cos(angle) * 25),
            round(center[1] + math.sin(angle) * 20),
        )
        pygame.draw.circle(
            effect_surface,
            (238, 134, 255, round(175 + pulse * 70)),
            rune_position,
            2,
        )

    for mote_index in range(5):
        phase = (
            current_time / 900
            + mote_index / 5
            + identity_seed % 31 / 31
        ) % 1
        mote_x = round(
            center[0]
            + math.sin(
                phase * math.tau + mote_index
            )
            * 18
        )
        mote_y = round(
            ACT_THREE_TILE_SIZE
            - 8
            - phase * 48
        )
        pygame.draw.circle(
            effect_surface,
            (
                220,
                91,
                255,
                round(170 * math.sin(math.pi * phase)),
            ),
            (mote_x, mote_y),
            2,
        )

    surface.blit(effect_surface, (left, top))

    badge_center = (
        left + ACT_THREE_TILE_SIZE - 10,
        top + 11,
    )
    pygame.draw.circle(
        surface,
        (29, 6, 38),
        badge_center,
        10,
    )
    pygame.draw.circle(
        surface,
        (226, 103, 255),
        badge_center,
        10,
        width=2,
    )

    turns_surface = font.render(
        str(turns),
        True,
        (255, 230, 255),
    )
    surface.blit(
        turns_surface,
        turns_surface.get_rect(
            center=badge_center,
        ),
    )
