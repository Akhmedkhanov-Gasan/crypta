import math

import pygame


STUN_LABEL_MS = 900


def draw_act_three_enemy_stun(
    surface,
    enemy_position,
    tile_size,
    current_time,
    started_at,
    font,
):
    center_x = enemy_position[0] + tile_size // 2
    top_y = enemy_position[1] - 8
    rotation = current_time / 260

    for index in range(3):
        angle = rotation + index * math.tau / 3
        center = (
            round(center_x + math.cos(angle) * 14),
            round(top_y + 5 + math.sin(angle) * 4),
        )
        spike = [
            (center[0], center[1] - 6),
            (center[0] + 2, center[1] - 2),
            (center[0] + 6, center[1]),
            (center[0] + 2, center[1] + 2),
            (center[0], center[1] + 6),
            (center[0] - 2, center[1] + 2),
            (center[0] - 6, center[1]),
            (center[0] - 2, center[1] - 2),
        ]
        pygame.draw.polygon(
            surface,
            (16, 17, 23),
            spike,
        )
        pygame.draw.lines(
            surface,
            (118, 119, 134),
            True,
            spike,
            2,
        )
        pygame.draw.circle(
            surface,
            (204, 204, 211),
            center,
            2,
        )

    elapsed = current_time - started_at
    if not 0 <= elapsed < STUN_LABEL_MS:
        return

    alpha = min(
        255,
        round((STUN_LABEL_MS - elapsed) * 255 / 300),
    )
    label = font.render(
        "STUN",
        True,
        (184, 185, 197),
    )
    label.set_alpha(alpha)
    surface.blit(
        label,
        label.get_rect(
            center=(center_x, top_y - 12),
        ),
    )
