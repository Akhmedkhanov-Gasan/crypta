import math

import pygame

from acts.act_three.presentation.summoner.animation import (
    SUMMONER_ATTACK_DURATION_MS,
)


_BIRD_RELEASE_MS = 100
_BIRD_TRAVEL_MS = 280
_BIRD_IMPACT_MS = (
    SUMMONER_ATTACK_DURATION_MS
    - _BIRD_RELEASE_MS
    - _BIRD_TRAVEL_MS
)


def _make_bird_sprite(current_time):
    size = 38
    surface = pygame.Surface(
        (size, size),
        pygame.SRCALPHA,
    )
    center_x = size // 2
    flap = (
        math.sin(current_time * 0.052)
        + 1
    ) / 2
    wing_tip_y = round(7 + flap * 13)

    left_wing = (
        (center_x - 2, 16),
        (3, wing_tip_y),
        (9, 23),
        (center_x - 2, 21),
    )
    right_wing = (
        (center_x + 2, 16),
        (size - 3, wing_tip_y),
        (size - 9, 23),
        (center_x + 2, 21),
    )

    pygame.draw.polygon(
        surface,
        (3, 10, 14, 245),
        left_wing,
    )
    pygame.draw.polygon(
        surface,
        (3, 10, 14, 245),
        right_wing,
    )
    pygame.draw.polygon(
        surface,
        (13, 103, 108, 225),
        (
            (center_x - 3, 17),
            (5, wing_tip_y + 1),
            (10, 20),
            (center_x - 2, 20),
        ),
    )
    pygame.draw.polygon(
        surface,
        (13, 103, 108, 225),
        (
            (center_x + 3, 17),
            (size - 5, wing_tip_y + 1),
            (size - 10, 20),
            (center_x + 2, 20),
        ),
    )
    pygame.draw.line(
        surface,
        (55, 199, 195, 220),
        (center_x - 3, 17),
        (5, wing_tip_y + 1),
        1,
    )
    pygame.draw.line(
        surface,
        (55, 199, 195, 220),
        (center_x + 3, 17),
        (size - 5, wing_tip_y + 1),
        1,
    )
    pygame.draw.polygon(
        surface,
        (2, 7, 11, 255),
        (
            (center_x - 3, 9),
            (center_x, 3),
            (center_x + 3, 9),
            (center_x + 3, 26),
            (center_x, 31),
            (center_x - 3, 26),
        ),
    )
    pygame.draw.circle(
        surface,
        (5, 14, 17, 255),
        (center_x, 26),
        4,
    )
    pygame.draw.polygon(
        surface,
        (42, 166, 164, 255),
        (
            (center_x - 2, 29),
            (center_x, 35),
            (center_x + 2, 29),
        ),
    )
    pygame.draw.circle(
        surface,
        (134, 255, 242, 255),
        (center_x - 2, 25),
        1,
    )
    pygame.draw.circle(
        surface,
        (134, 255, 242, 255),
        (center_x + 2, 25),
        1,
    )

    return surface


def draw_summoner_bird_attack(
    surface,
    origin,
    destination,
    elapsed,
    tile_size,
    current_time,
):
    if elapsed < _BIRD_RELEASE_MS:
        return

    effect_surface = pygame.Surface(
        surface.get_size(),
        pygame.SRCALPHA,
    )
    travel_elapsed = elapsed - _BIRD_RELEASE_MS

    if travel_elapsed < _BIRD_TRAVEL_MS:
        progress = max(
            0.0,
            min(1.0, travel_elapsed / _BIRD_TRAVEL_MS),
        )
        progress = progress * progress * (3 - 2 * progress)
        travel_x = destination[0] - origin[0]
        travel_y = destination[1] - origin[1]
        travel_length = max(
            1.0,
            math.hypot(travel_x, travel_y),
        )
        normal_x = -travel_y / travel_length
        normal_y = travel_x / travel_length
        bird_position = (
            round(origin[0] + travel_x * progress),
            round(origin[1] + travel_y * progress),
        )
        trail_progress = max(0.0, progress - 0.24)
        trail_position = (
            round(
                origin[0]
                + (
                    destination[0] - origin[0]
                ) * trail_progress
            ),
            round(
                origin[1]
                + (
                    destination[1] - origin[1]
                ) * trail_progress
            ),
        )

        for width, color in (
            (8, (4, 20, 24, 22)),
            (4, (8, 64, 70, 58)),
            (1, (36, 173, 178, 145)),
        ):
            pygame.draw.line(
                effect_surface,
                color,
                trail_position,
                bird_position,
                width,
            )

        for particle_index in range(6):
            particle_progress = max(
                0.0,
                progress - 0.04 - particle_index * 0.035,
            )
            wave = math.sin(
                current_time * 0.02
                + particle_index * 1.7
            ) * (3 + particle_index)
            particle_position = (
                round(
                    origin[0]
                    + travel_x * particle_progress
                    + normal_x * wave
                ),
                round(
                    origin[1]
                    + travel_y * particle_progress
                    + normal_y * wave
                ),
            )
            pygame.draw.circle(
                effect_surface,
                (
                    44,
                    184,
                    187,
                    max(35, 170 - particle_index * 22),
                ),
                particle_position,
                2 if particle_index < 2 else 1,
            )

        shadow_rectangle = pygame.Rect(0, 0, 18, 5)
        shadow_rectangle.center = (
            bird_position[0],
            bird_position[1] + 12,
        )
        pygame.draw.ellipse(
            effect_surface,
            (2, 8, 10, 90),
            shadow_rectangle,
        )

        flight_angle = math.degrees(
            math.atan2(travel_y, travel_x)
        )
        bird_sprite = pygame.transform.rotate(
            _make_bird_sprite(current_time),
            90 - flight_angle,
        )
        effect_surface.blit(
            bird_sprite,
            bird_sprite.get_rect(center=bird_position),
        )
        surface.blit(effect_surface, (0, 0))
        return

    impact_progress = min(
        1.0,
        (
            travel_elapsed - _BIRD_TRAVEL_MS
        ) / _BIRD_IMPACT_MS,
    )
    visibility = 1 - impact_progress
    radius = round(
        tile_size * (0.18 + impact_progress * 0.42)
    )

    pygame.draw.circle(
        effect_surface,
        (
            15,
            116,
            122,
            round(190 * visibility),
        ),
        destination,
        radius,
        width=3,
    )
    pygame.draw.circle(
        effect_surface,
        (
            73,
            221,
            218,
            round(130 * visibility),
        ),
        destination,
        max(3, radius // 2),
        width=2,
    )

    for feather_index in range(8):
        angle = (
            feather_index * math.tau / 8
            + impact_progress * 0.8
        )
        distance = (
            tile_size
            * (0.12 + impact_progress * 0.48)
        )
        feather_position = (
            round(
                destination[0]
                + math.cos(angle) * distance
            ),
            round(
                destination[1]
                + math.sin(angle) * distance
            ),
        )
        feather_end = (
            round(
                feather_position[0]
                + math.cos(angle + 0.5) * 6
            ),
            round(
                feather_position[1]
                + math.sin(angle + 0.5) * 6
            ),
        )
        pygame.draw.line(
            effect_surface,
            (
                31,
                169,
                173,
                round(210 * visibility),
            ),
            feather_position,
            feather_end,
            2,
        )

    surface.blit(effect_surface, (0, 0))
