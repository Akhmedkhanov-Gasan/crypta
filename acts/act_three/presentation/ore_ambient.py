import math

import pygame

from presentation.layout import ACT_THREE_TILE_SIZE


def draw_ore_ambient(context, current_time):
    tile_size = ACT_THREE_TILE_SIZE
    padding = 24
    effect_size = tile_size + padding * 2

    for ore in context.floor.act_three_ores:
        if (
            ore["type"] != "black_ore"
            or ore["stage"] >= 3
            or ore["position"] not in context.floor.visible_cells
        ):
            continue

        column, row = ore["position"]
        left = round(column * tile_size - context.camera_x)
        top = round(row * tile_size - context.camera_y)
        rectangle = pygame.Rect(
            left - padding, top - padding, effect_size, effect_size,
        )
        if not rectangle.colliderect(context.view_surface.get_rect()):
            continue

        effect = pygame.Surface((effect_size, effect_size), pygame.SRCALPHA)
        seed = column * 0.731 + row * 1.173

        for index in range(7):
            duration = 5200 + index * 430
            phase = (current_time / duration + index * 0.173 + seed) % 1
            visibility = math.sin(math.pi * phase) ** 1.5
            angle = seed + index * 2.399 + current_time / 11000
            x = (
                padding
                + tile_size * 0.5
                + math.sin(angle) * tile_size * 0.29
                + math.sin(phase * math.pi) * 3
            )
            y = (
                padding
                + tile_size * 0.78
                - phase * tile_size * 0.72
                + math.cos(angle) * 3
            )
            center = (round(x), round(y))
            pygame.draw.circle(
                effect, (128, 91, 173, round(18 * visibility)), center, 5,
            )
            pygame.draw.circle(
                effect, (176, 139, 214, round(38 * visibility)), center, 2,
            )
            pygame.draw.circle(
                effect, (218, 193, 239, round(105 * visibility)), center, 1,
            )

        context.view_surface.blit(effect, rectangle.topleft)
