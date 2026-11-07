import math

import pygame

from acts.act_three.mining.runtime import MINING_FRAME_MS
from presentation.layout import ACT_THREE_TILE_SIZE


def draw_active_mining_particles(context, player, current_time):
    mining = player.act_three.mining
    if mining is None or mining["ending_at"] is not None:
        return

    elapsed = max(0, current_time - mining["started_at"])
    frame_step = elapsed // MINING_FRAME_MS
    column, row = mining["target"]
    origin_column, origin_row = mining["origin"]
    center_x = (
        (column + 0.5) * ACT_THREE_TILE_SIZE
        - context.camera_x
        + (origin_column - column) * ACT_THREE_TILE_SIZE * 0.2
    )
    center_y = (
        (row + 0.5) * ACT_THREE_TILE_SIZE
        - context.camera_y
        + (origin_row - row) * ACT_THREE_TILE_SIZE * 0.2
    )
    particles = pygame.Surface((64, 64), pygame.SRCALPHA)

    for step in range(max(0, frame_step - 2), frame_step + 1):
        age = elapsed - step * MINING_FRAME_MS
        progress = age / (MINING_FRAME_MS * 3)
        if not 0 <= progress < 1:
            continue

        for index in range(4):
            angle = step * 1.73 + index * 2.399
            distance = 2 + progress * (9 + index * 3)
            x = 32 + math.cos(angle) * distance
            y = (
                32 + math.sin(angle) * distance * 0.45
                - math.sin(progress * math.pi) * 7
                + progress * progress * 8
            )
            point = (round(x), round(y))
            alpha = round(110 * (1 - progress))
            if index < 2:
                pygame.draw.circle(
                    particles,
                    (100, 87, 111, round(alpha * 0.3)),
                    point,
                    round(2 + progress * 4),
                )
            else:
                pygame.draw.rect(
                    particles,
                    (177, 151, 190, alpha),
                    (point[0], point[1], 2, 2),
                )

    context.view_surface.blit(
        particles,
        (round(center_x) - 32, round(center_y) - 32),
    )
