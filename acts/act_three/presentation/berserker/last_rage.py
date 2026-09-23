import math

import pygame


LAST_RAGE_FRAME_COUNT = 8


def last_rage_frame(elapsed, duration):
    progress = max(
        0.0,
        min(1.0, elapsed / duration),
    )

    return min(
        LAST_RAGE_FRAME_COUNT - 1,
        int(progress * LAST_RAGE_FRAME_COUNT),
    )


def last_rage_camera_offset(elapsed, duration):
    shake_duration = min(560, duration)

    if not 0 <= elapsed < shake_duration:
        return (0, 0)

    progress = elapsed / shake_duration
    rise = min(1.0, progress / 0.18)
    fall = (1.0 - progress) ** 2
    strength = 2.6 * rise * fall

    return (
        round(math.sin(elapsed * 0.075) * strength),
        round(math.cos(elapsed * 0.095) * strength * 0.55),
    )


def draw_last_rage_activation_effect(
    surface,
    position,
    elapsed,
    duration,
    tile_size,
):
    if not 0 <= elapsed < duration:
        return

    progress = elapsed / duration
    reveal_progress = min(1.0, progress / 0.32)
    reveal = reveal_progress * reveal_progress * (
        3.0 - 2.0 * reveal_progress
    )
    fade_progress = max(
        0.0,
        (progress - 0.68) / 0.32,
    )
    fade = 1.0 - fade_progress * fade_progress
    visibility = reveal * fade

    margin = tile_size
    effect_size = tile_size + margin * 2
    effect_surface = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    center_x = effect_size // 2
    center_y = margin + tile_size // 2

    shadow_rect = pygame.Rect(
        center_x - round(tile_size * 0.48),
        center_y + round(tile_size * 0.2),
        round(tile_size * 0.96),
        round(tile_size * 0.34),
    )
    pygame.draw.ellipse(
        effect_surface,
        (
            36,
            0,
            3,
            round(90 * visibility),
        ),
        shadow_rect,
    )

    for smoke_index in range(10):
        smoke_phase = (
            progress * 0.8
            + smoke_index / 10
        ) % 1.0
        smoke_visibility = (
            math.sin(math.pi * smoke_phase)
            * visibility
        )
        smoke_drift = math.sin(
            smoke_index * 1.83
            + progress * math.pi * 2
        )
        smoke_x = round(
            center_x
            + math.sin(smoke_index * 2.17)
            * tile_size * 0.34
            + smoke_drift * 5
        )
        smoke_y = round(
            center_y
            + tile_size * 0.35
            - smoke_phase * tile_size * 1.05
        )
        smoke_radius = max(
            4,
            round(9 - smoke_phase * 4),
        )

        pygame.draw.circle(
            effect_surface,
            (
                54,
                0,
                5,
                round(45 * smoke_visibility),
            ),
            (smoke_x, smoke_y),
            smoke_radius + 3,
        )
        pygame.draw.circle(
            effect_surface,
            (
                138,
                8,
                11,
                round(54 * smoke_visibility),
            ),
            (smoke_x, smoke_y),
            smoke_radius,
        )

    pulse = (
        math.sin(progress * math.pi * 2.2)
        + 1.0
    ) / 2.0
    aura_rect = pygame.Rect(
        center_x - round(tile_size * 0.42),
        center_y - round(tile_size * 0.48),
        round(tile_size * 0.84),
        round(tile_size * 0.92),
    )

    pygame.draw.ellipse(
        effect_surface,
        (
            72,
            3,
            8,
            round((38 + pulse * 18) * visibility),
        ),
        aura_rect,
        width=4,
    )

    rotation = progress * 0.7

    for arc_index in range(3):
        radius = round(
            tile_size
            * (
                0.42
                + arc_index * 0.12
                + reveal * 0.08
            )
        )
        arc_rect = pygame.Rect(
            center_x - radius,
            center_y - round(radius * 0.62),
            radius * 2,
            round(radius * 1.24),
        )
        start_angle = (
            rotation
            + arc_index * 1.9
        )
        end_angle = start_angle + 1.15

        pygame.draw.arc(
            effect_surface,
            (
                118 + arc_index * 18,
                7,
                11,
                round(
                    (105 - arc_index * 22)
                    * visibility
                ),
            ),
            arc_rect,
            start_angle,
            end_angle,
            width=2,
        )
        pygame.draw.arc(
            effect_surface,
            (
                92,
                3,
                8,
                round(
                    (75 - arc_index * 16)
                    * visibility
                ),
            ),
            arc_rect,
            start_angle + math.pi,
            end_angle + math.pi,
            width=2,
        )

    for ember_index in range(7):
        phase = (
            progress * 0.72
            + ember_index / 7
        ) % 1.0
        angle = (
            ember_index * 2.31
            + progress * 0.45
        )
        horizontal_radius = tile_size * (
            0.24 + phase * 0.3
        )
        ember_x = round(
            center_x
            + math.cos(angle)
            * horizontal_radius
        )
        ember_y = round(
            center_y
            + tile_size * 0.25
            - phase * tile_size * 0.78
            + math.sin(angle) * 5
        )
        ember_visibility = (
            math.sin(math.pi * phase)
            * visibility
        )

        pygame.draw.circle(
            effect_surface,
            (
                126,
                8,
                10,
                round(75 * ember_visibility),
            ),
            (ember_x, ember_y),
            3,
        )
        pygame.draw.circle(
            effect_surface,
            (
                194,
                24,
                19,
                round(145 * ember_visibility),
            ),
            (ember_x, ember_y),
            1,
        )

    for mark_index in range(4):
        angle = (
            math.pi * 0.25
            + mark_index * math.pi * 0.5
        )
        inner_radius = tile_size * 0.3
        outer_radius = tile_size * (
            0.39 + reveal * 0.06
        )
        start = (
            round(
                center_x
                + math.cos(angle) * inner_radius
            ),
            round(
                center_y
                + math.sin(angle)
                * inner_radius
                * 0.62
            ),
        )
        end = (
            round(
                center_x
                + math.cos(angle) * outer_radius
            ),
            round(
                center_y
                + math.sin(angle)
                * outer_radius
                * 0.62
            ),
        )

        pygame.draw.line(
            effect_surface,
            (
                154,
                12,
                15,
                round(120 * visibility),
            ),
            start,
            end,
            width=2,
        )

    surface.blit(
        effect_surface,
        (
            position[0] - margin,
            position[1] - margin,
        ),
    )
