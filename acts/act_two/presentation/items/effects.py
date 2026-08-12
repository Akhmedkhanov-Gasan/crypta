import math

import pygame

from presentation.layout import MAP_OFFSET_X, MAP_OFFSET_Y
from settings import TILE_SIZE


def draw_pickup_effect(
    screen,
    sprites,
    kind,
    origin,
    current_time,
    effect_started_at,
):
    duration = 760
    elapsed = current_time - effect_started_at
    if (
        kind not in ("potion", "gold", "key")
        or origin is None
        or effect_started_at < 0
        or not 0 <= elapsed < duration
    ):
        return

    progress = elapsed / duration
    center_x = MAP_OFFSET_X + origin[0] * TILE_SIZE + TILE_SIZE // 2
    center_y = MAP_OFFSET_Y + origin[1] * TILE_SIZE + TILE_SIZE // 2
    effect_size = 80
    effect_center = effect_size // 2
    effect = pygame.Surface(
        (effect_size, effect_size),
        pygame.SRCALPHA,
    )
    colors = {
        "potion": ((183, 46, 59), (255, 126, 126)),
        "gold": ((194, 137, 31), (255, 226, 91)),
        "key": ((151, 110, 42), (240, 197, 94)),
    }
    sprite_names = {
        "potion": "potion",
        "gold": "coin",
        "key": "key",
    }
    base_color, bright_color = colors[kind]

    pull_progress = max(
        0.0,
        min(1.0, (progress - 0.12) / 0.42),
    )
    pull_progress = pull_progress * pull_progress * (
        3 - 2 * pull_progress
    )
    item_size = max(6, round(28 - pull_progress * 21))
    item_alpha = round(
        255
        * max(0.0, 1 - max(0.0, progress - 0.48) / 0.18)
    )
    item_y = effect_center - round(math.sin(progress * math.pi) * 6)
    item_sprite = pygame.transform.scale(
        sprites[sprite_names[kind]],
        (item_size, item_size),
    )
    item_sprite.set_alpha(item_alpha)

    orbit_radius = 18 * (1 - pull_progress) + 3
    orbit_alpha = round(180 * max(0.0, 1 - progress / 0.58))
    for particle_index in range(8):
        angle = particle_index * math.tau / 8 + progress * 3.2
        particle_position = (
            round(effect_center + math.cos(angle) * orbit_radius),
            round(item_y + math.sin(angle) * orbit_radius * 0.58),
        )
        pygame.draw.circle(
            effect,
            (*bright_color, orbit_alpha),
            particle_position,
            2 if particle_index % 3 == 0 else 1,
        )

    ring_progress = max(0.0, min(1.0, (progress - 0.3) / 0.42))
    if ring_progress > 0:
        ring_radius = round(4 + ring_progress * 22)
        ring_alpha = round(190 * (1 - ring_progress))
        pygame.draw.circle(
            effect,
            (*base_color, ring_alpha),
            (effect_center, effect_center),
            ring_radius,
            width=3,
        )
        pygame.draw.circle(
            effect,
            (*bright_color, round(ring_alpha * 0.75)),
            (effect_center, effect_center),
            max(2, ring_radius - 4),
            width=1,
        )
        for spark_index in range(6):
            angle = spark_index * math.tau / 6
            spark_start_distance = 5 + ring_progress * 10
            spark_end_distance = spark_start_distance + 5
            pygame.draw.line(
                effect,
                (*bright_color, ring_alpha),
                (
                    round(
                        effect_center
                        + math.cos(angle) * spark_start_distance
                    ),
                    round(
                        effect_center
                        + math.sin(angle) * spark_start_distance
                    ),
                ),
                (
                    round(
                        effect_center
                        + math.cos(angle) * spark_end_distance
                    ),
                    round(
                        effect_center
                        + math.sin(angle) * spark_end_distance
                    ),
                ),
                2,
            )

    item_position = item_sprite.get_rect(
        center=(effect_center, item_y)
    )
    effect.blit(item_sprite, item_position)
    screen.blit(
        effect,
        (center_x - effect_center, center_y - effect_center),
    )
